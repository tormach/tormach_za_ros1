import time
from typing import Tuple, Generator

import serial
import logging

from .exceptions import CommunicationError, ResponseError
from .feetech_device import FeetechDevice  # noqa: F401

logger = logging.getLogger(__name__)


class FeetechServo:
    """
    Feetech SMB/SMS servo control.
    """

    BAUDRATE_VALUES = [
        1000000,
        500000,
        250000,
        128000,
        115200,
        76800,
        57600,
        38400,
    ]

    _FIRMWARE_MAIN_VERSION_ADDR = 0x00
    _FIRMWARE_SECONDARY_VERSION_ADDR = 0x01
    _SERVO_MAIN_VERSION_ADDR = 0x03
    _SERVO_SECONDARY_VERSION_ADDR = 0x04
    _ID_ADDR = 0x05
    _BAUDRATE_ADDR = 0x06
    _RETURN_DELAY_TIME_ADDR = 0x07
    _STATUS_RETURN_LEVEL_ADDR = 0x08
    _MIN_POSITION_LIMIT_ADDR = 0x09
    _MAX_POSITION_LIMIT_ADDR = 0x0B
    _MAX_TEMPERATURE_LIMIT_ADDR = 0x0D
    _MAX_INPUT_VOLTAGE_ADDR = 0x0E
    _MIN_INPUT_VOLTAGE_ADDR = 0x0F
    _MAX_TORQUE_LIMIT_ADDR = 0x10
    _SETTING_BYTE_ADDR = 0x12
    _PROTECTION_SWITCH_ADDR = 0x13
    _LED_ALARM_CONDITION_ADDR = 0x14
    _POSITION_P_GAIN_ADDR = 0x15
    _POSITION_D_GAIN_ADDR = 0x16
    _POSITION_I_GAIN_ADDR = 0x17
    _MINIMUM_STARTUP_FORCE_ADDR = 0x18
    _CW_DEAD_BAND_ADDR = 0x1A
    _CCW_DEAD_BAND_ADDR = 0x1B
    _OVERLOAD_CURRENT_ADDR = 0x1C
    _ANGULAR_RESOLUTION_ADDR = 0x1E
    _POSITION_OFFSET_ADDR = 0x1F
    _WORK_MODE_ADDR = 0x21
    _PROTECTION_TORQUE_ADDR = 0x22
    _OVERLOAD_PROTECTION_TIME_ADDR = 0x23
    _OVERLOAD_TORQUE_ADDR = 0x24
    _VELOCITY_P_GAIN_ADDR = 0x25
    _OVERCURRENT_PROTECTION_TIME_ADDR = 0x26
    _VELOCITY_I_GAIN_ADDR = 0x27
    _TORQUE_ENABLE_ADDR = 0x28
    _GOAL_ACCELERATION_ADDR = 0x29
    _GOAL_POSITION_ADDR = 0x2A
    _RUNNING_TIME_ADDR = 0x2C
    _GOAL_VELOCITY_ADDR = 0x2E
    _TORQUE_LIMIT_ADDR = 0x30
    _LOCK_ADDR = 0x37
    _PRESENT_POSITION_ADDR = 0x38
    _PRESENT_VELOCITY_ADDR = 0x3A
    _PRESENT_LOAD_ADDR = 0x3C
    _PRESENT_INPUT_VOLTAGE_ADDR = 0x3E
    _PRESENT_TEMPERATURE_ADDR = 0x3F
    _SYNC_WRITE_FLAG_ADDR = 0x40
    _HARDWARE_ERROR_STATUS_ADDR = 0x41
    _MOVING_STATUS_ADDR = 0x42
    _PRESENT_CURRENT_ADDR = 0x45

    MIN_POS_PROTECTION_BIT = 1 << 0
    MAX_POS_PROTECTION_BIT = 1 << 1
    MAX_TEMP_PROTECTION_BIT = 1 << 2
    MAX_VOLTAGE_PROTECTION_BIT = 1 << 3
    MIN_VOLTAGE_PROTECTION_BIT = 1 << 4
    MAX_TORQUE_PROTECTION_BIT = 1 << 5

    WORK_MODE_POSITION_SERVO = 0
    WORK_MODE_CONSTANT_SPEED = 1
    WORK_MODE_PWM_OPEN_LOOP = 2

    _PING_INSTRUCTION = 0x01
    _READ_INSTRUCTION = 0x02
    _WRITE_INSTRUCTION = 0x03
    _REG_WRITE_INSTRUCTION = 0x04
    _ACTION_INSTRUCTION = 0x05
    _RESET_INSTRUCTION = 0x06
    _SYNC_WRITE_INSTRUCTION = 0x83
    _SERVO_BROADCAST_ID = 0xFE

    OVERLOAD_ERROR_BIT = 32
    COMMUNICATION_ERROR_BIT = 16
    CURRENT_ERROR_BIT = 8
    TEMPERATURE_ERROR_BIT = 4
    SENSOR_ERROR_BIT = 2
    VOLTAGE_ERROR_BIT = 1

    device = None  # type: FeetechDevice

    def __init__(
        self,
        feetech_device,
        servo_id,
        retry_count=3,
        exception_on_error_response=True,
    ):
        self.retry_count = retry_count
        """ Number of retries on communication errors."""
        self.exception_on_error_response = True
        """ Raise exception on error response."""
        self.enable_async_write = False
        """ Execute asynchronous write commands, requires manual call of execute_async_write to apply changes."""
        self._error_status = 0

        if feetech_device is None:
            raise RuntimeError("Feetech servo requires a feetech USB device")
        else:
            self.device = feetech_device

        self._servo_id = servo_id
        try:
            self.ping()
            retry = False
        except CommunicationError as e:
            logger.warning(f"Exception: {e}")
            logger.warning("Pinging servo failed, retrying...")
            retry = True
        if retry:
            self.device.flush()
            try:
                self.ping()
            except CommunicationError as exc:
                raise CommunicationError(
                    f"lib_feetech: Error encountered. "
                    f"Could not ping servo with ID {self._servo_id} "
                    f"on bus {self.device.device}.\n'"
                ) from exc

        self.exception_on_error_response = exception_on_error_response

        # Set Return Delay time -
        # Used to determine when next status can be requested
        data = self._read_address(0x07, 1)
        self._return_delay = data[0] * 2e-6

    def _send_instruction(
        self,
        instruction,
        response_length,
        exception_on_error_response=True,
        servo_id=None,
    ):
        """
        send instruction with retries
        """
        if servo_id is None:
            servo_id = self._servo_id
        msg = [servo_id, len(instruction) + 1] + instruction
        checksum = self._calc_checksum(msg)
        msg = [0xFF, 0xFF] + msg + [checksum]

        with self.device.lock:
            failures = 0
            while True:
                try:
                    self.device.flush()
                    data, err = self._send_receive(msg, response_length)
                    if err & self.COMMUNICATION_ERROR_BIT:
                        raise CommunicationError(
                            "Servo error 16 - sent packet checksum invalid"
                        )
                    break
                except (CommunicationError, serial.SerialException) as e:
                    failures += 1
                    if failures > self.retry_count:
                        raise
                    logger.warning(
                        f"send_instruction retry {failures}, error: {e}"
                    )
        self._error_status = err
        if not exception_on_error_response:
            return data
        if err != 0:
            raise ResponseError(err, self.decode_error_status(err))
        return data

    def ping(self):
        """
        Ping the servo.
        """
        msg = [self._PING_INSTRUCTION]
        response_length = 6
        return self._send_instruction(
            msg,
            response_length,
            exception_on_error_response=self.exception_on_error_response,
        )

    def _read_address(self, address, n_bytes=1):
        """
        reads nBytes from start address on the servo.
        returns [n1,n2 ...] (list of parameters)
        """
        msg = [self._READ_INSTRUCTION, address, n_bytes]
        response_length = 6 + n_bytes
        return self._send_instruction(
            msg,
            response_length,
            exception_on_error_response=self.exception_on_error_response,
        )

    def _write_address(self, address, data):
        """
        writes data to the start address.
        data = [n1,n2 ...] list of numbers.
        return [n1,n2 ...] (list of return parameters)
        """
        msg = [self._WRITE_INSTRUCTION, address] + data
        response_length = 6
        return self._send_instruction(
            msg,
            response_length,
            exception_on_error_response=self.exception_on_error_response,
        )

    def _write_async_address(self, address, data):
        """
        writes data to the start address.
        data = [n1,n2 ...] list of numbers.
        return [n1,n2 ...] (list of return parameters)
        """
        msg = [self._REG_WRITE_INSTRUCTION, address] + data
        response_length = 6
        return self._send_instruction(
            msg,
            response_length,
            exception_on_error_response=self.exception_on_error_response,
        )

    def execute_async_write(self):
        """
        executes the async write command via broadcast on all servos

        Note: only applies last async write command
        """
        msg = [self._ACTION_INSTRUCTION]
        response_length = 6
        return self._send_instruction(
            msg,
            response_length,
            exception_on_error_response=self.exception_on_error_response,
            servo_id=0xFE,
        )

    def reset(self):
        """
        Reset the servo.
        """
        msg = [self._RESET_INSTRUCTION]
        response_length = 6
        return self._send_instruction(
            msg,
            response_length,
            exception_on_error_response=self.exception_on_error_response,
        )

    def _write(self, address, data):
        """Executes sync or async commands depending on setting."""
        if self.enable_async_write:
            return self._write_async_address(address, data)
        else:
            return self._write_address(address, data)

    @staticmethod
    def _receive_reply(
        data: Generator[bytes, None, None],
        servo_id,
        timeout,
        start_byte=b'\xff',
    ) -> Tuple[bytes, int]:
        """
        Picks out the start sequence from the received servo data and extracts the payload from the package.
        raises CommunicationError in case of errors.
        :param data: Generator of bytes received from the servo
        :param servo_id: Servo id used fro matching the start sequence
        :param timeout: Maximum time to wait for the start sequence
        :param start_byte: The start bye of the start sequence
        :return: The payload and the error code from the package
        """
        data = iter(data)
        start_byte_received = False
        second_byte_received = False
        skipped_bytes = []

        start_time = time.time()
        while not start_byte_received or not second_byte_received:
            if timeout and time.time() - start_time > timeout:
                raise CommunicationError(
                    f"Timeout receiving reply start byte.\n"
                    f" Received: bytes {[hex(b) for b in skipped_bytes]}"
                )
            if not start_byte_received:
                try:
                    rcv_start_byte = next(data)
                except StopIteration as exc:
                    raise CommunicationError(
                        f"Not enough data received.\n"
                        f" Received bytes {[hex(b) for b in skipped_bytes]}"
                    ) from exc
                if rcv_start_byte == start_byte:
                    start_byte_received = True
            elif not second_byte_received:
                try:
                    rcv_servo_id = next(data)
                except StopIteration as exc:
                    raise CommunicationError(
                        f"Not enough data received.\n"
                        f" Received bytes {[hex(b) for b in skipped_bytes]}"
                    ) from exc
                if rcv_servo_id[0] == servo_id:
                    second_byte_received = True
                elif rcv_servo_id == start_byte:
                    second_byte_received = False
                    skipped_bytes += rcv_start_byte
                else:
                    skipped_bytes += rcv_start_byte + rcv_servo_id
                    start_byte_received = False
            else:
                skipped_bytes += rcv_start_byte

        received = [start_byte[0], rcv_servo_id[0]]

        try:
            data_len = next(data)
            received.append(data_len[0])
            err = next(data)
            received.append(err[0])
        except StopIteration as exc:
            raise CommunicationError(
                f"Incomplete data received.\n"
                f"Received bytes {[hex(b) for b in received]}"
            ) from exc

        out_data = b''
        while len(out_data) < data_len[0] - 2:
            try:
                out_data += next(data)
                received.append(out_data[-1])
            except StopIteration as exc:
                raise CommunicationError(
                    f"Incomplete data received.\n"
                    f" Received bytes {[hex(b) for b in received]}"
                ) from exc
        try:
            chksum_in = next(data)[0]
            received.append(chksum_in)
        except StopIteration as exc:
            raise CommunicationError(
                f"Incomplete data received.\n"
                f" Received bytes {[hex(b) for b in received]}"
            ) from exc

        chksum_calc = FeetechServo._calc_checksum(
            rcv_servo_id + data_len + err + out_data
        )
        if chksum_calc != chksum_in:
            raise CommunicationError(
                f'Checksum mismatch: calculated {hex(chksum_calc)} vs received {hex(chksum_in)}'
                f' Received bytes {[hex(b) for b in received]}'
            )

        return out_data, err[0]

    def _send_receive(self, msg, response_length):
        if self.device.supports_read_write:
            # in case the device supports read_write we first use read_write to
            # send the message and receive the expected number of bytes in bulk
            # then we continue to read until we get a timeout or the data is
            # complete
            def get_data():
                reply = self.device.read_write(bytes(msg), response_length)
                for b in reply:
                    yield bytes([b])
                while True:
                    yield self.device.read(1)

        else:
            # in case the device does not support read_write we first send the
            # message and then read one byte at a time untilwe get a timeout or
            # the data is complete
            def get_data():
                while True:
                    yield self.device.read(1)

            self.device.write(bytes(msg))

        data, err = self._receive_reply(
            get_data(),
            servo_id=self._servo_id,
            timeout=self.device.RW_TIMEOUT_S,
        )

        return data, err

    @staticmethod
    def _calc_checksum(msg):
        chksum = sum(msg)
        chksum = (~chksum) % 256
        return chksum

    @staticmethod
    def decode_error_status(error_byte):
        error_bits = {
            FeetechServo.OVERLOAD_ERROR_BIT: "Overload",
            FeetechServo.COMMUNICATION_ERROR_BIT: "Communication",
            FeetechServo.CURRENT_ERROR_BIT: "Current",
            FeetechServo.TEMPERATURE_ERROR_BIT: "Temperature",
            FeetechServo.SENSOR_ERROR_BIT: "Sensor",
            FeetechServo.VOLTAGE_ERROR_BIT: "Voltage",
        }
        return [
            description
            for bit, description in error_bits.items()
            if error_byte & bit
        ]

    @property
    def error_status(self):
        """
        Error status of the servo, see error bits for details.
        """
        data = self._read_address(self._HARDWARE_ERROR_STATUS_ADDR, 1)
        return data[0]

    @property
    def cached_error_status(self):
        """
        Error status of the servo, see error bits for details.
        Updated when executing a read or write command.
        """
        return self._error_status

    @property
    def firmware_version(self):
        data1 = self._read_address(self._FIRMWARE_MAIN_VERSION_ADDR, 1)
        data2 = self._read_address(self._FIRMWARE_SECONDARY_VERSION_ADDR, 1)
        return f'{data1[0]}.{data2[0]}'

    @property
    def servo_version(self):
        data1 = self._read_address(self._SERVO_MAIN_VERSION_ADDR, 1)
        data2 = self._read_address(self._SERVO_SECONDARY_VERSION_ADDR, 1)
        return f'{data1[0]}.{data2[0]}'

    @property
    def servo_id(self):
        return self._servo_id

    @servo_id.setter
    def servo_id(self, value):
        if not 0 <= value <= 253:
            raise ValueError("Servo ID must be 0-253")
        self._write(self._ID_ADDR, [value & 0xFF])
        self._servo_id = value

    @property
    def baudrate(self):
        data = self._read_address(self._BAUDRATE_ADDR, 1)
        index = data[0]
        return (
            self.BAUDRATE_VALUES[index]
            if 0 <= index < len(self.BAUDRATE_VALUES)
            else None
        )

    @baudrate.setter
    def baudrate(self, value):
        if value not in self.BAUDRATE_VALUES:
            raise ValueError(f"Baudrate must be one of {self.BAUDRATE_VALUES}")
        i = self.BAUDRATE_VALUES.index(value)
        self._write(self._BAUDRATE_ADDR, [i])

    @property
    def return_delay_time(self):
        data = self._read_address(self._RETURN_DELAY_TIME_ADDR, 1)
        return data[0] * 2

    @return_delay_time.setter
    def return_delay_time(self, value):
        if not 0 <= value <= 508:
            raise ValueError("Return delay time must be between 0 and 508us")
        data = [value // 2]
        self._write(self._RETURN_DELAY_TIME_ADDR, data)

    @property
    def status_return_level(self):
        data = self._read_address(self._STATUS_RETURN_LEVEL_ADDR, 1)
        return data[0]

    @status_return_level.setter
    def status_return_level(self, value):
        data = [int(bool(value))]
        self._write(self._STATUS_RETURN_LEVEL_ADDR, data)

    @property
    def min_position_limit(self):
        data = self._read_address(self._MIN_POSITION_LIMIT_ADDR, 2)
        return int(data[0] | data[1] << 8)

    @min_position_limit.setter
    def min_position_limit(self, value):
        if not 0 <= value <= 4094:
            raise ValueError(
                "Minimum position limit must be between 0 and 4094"
            )
        data = [value & 0xFF, value >> 8 & 0xFF]
        self._write(self._MIN_POSITION_LIMIT_ADDR, data)

    @property
    def max_position_limit(self):
        data = self._read_address(self._MAX_POSITION_LIMIT_ADDR, 2)
        return int(data[0] | data[1] << 8)

    @max_position_limit.setter
    def max_position_limit(self, value):
        if not 1 <= value <= 4095:
            raise ValueError(
                "Maximum position limit must be between 0 and 4094"
            )
        data = [value & 0xFF, value >> 8 & 0xFF]
        self._write(self._MAX_POSITION_LIMIT_ADDR, data)

    @property
    def max_temperature_limit(self):
        data = self._read_address(self._MAX_TEMPERATURE_LIMIT_ADDR, 1)
        return data[0]

    @max_temperature_limit.setter
    def max_temperature_limit(self, value):
        if not 0 <= value <= 100:
            raise ValueError(
                "Maximum temperature limit must be between 0 and 100"
            )
        data = [value & 0xFF]
        self._write(self._MAX_TEMPERATURE_LIMIT_ADDR, data)

    @property
    def max_input_voltage(self):
        data = self._read_address(self._MAX_INPUT_VOLTAGE_ADDR, 1)
        return data[0] * 0.1

    @max_input_voltage.setter
    def max_input_voltage(self, value):
        if not 0.0 <= value <= 25.4:
            raise ValueError(
                "Maximum input voltage must be between 0 and 25.4V"
            )
        data = [int(value * 10)]
        self._write(self._MAX_INPUT_VOLTAGE_ADDR, data)

    @property
    def min_input_voltage(self):
        data = self._read_address(self._MIN_INPUT_VOLTAGE_ADDR, 1)
        return data[0] * 0.1

    @min_input_voltage.setter
    def min_input_voltage(self, value):
        if not 0.0 <= value <= 25.4:
            raise ValueError(
                "Maximum input voltage must be between 0 and 25.4V"
            )
        data = [int(value * 10)]
        self._write(self._MIN_INPUT_VOLTAGE_ADDR, data)

    @property
    def max_torque_limit(self):
        """
        Maximum output torque limit in percent of stall torque.

        Note that this does not seem to have any other effect than
        beeing the default value for torque_limit on power-cycle.
        """
        data = self._read_address(self._MAX_TORQUE_LIMIT_ADDR, 2)
        return int(data[0] | data[1] << 8) * 0.1

    @max_torque_limit.setter
    def max_torque_limit(self, value):
        if not 0.0 <= value <= 100.0:
            raise ValueError("Maximum torque must be between 0 and 100%")
        value = int(value * 10)
        data = [value & 0xFF, value >> 8 & 0xFF]
        self._write(self._MAX_TORQUE_LIMIT_ADDR, data)

    @property
    def setting_byte(self):
        return self._read_address(self._SETTING_BYTE_ADDR, 1)

    @setting_byte.setter
    def setting_byte(self, value):
        data = [value & 0xFF]
        self._write(self._SETTING_BYTE_ADDR, data)

    @property
    def protection_switch(self):
        data = self._read_address(self._PROTECTION_SWITCH_ADDR, 1)
        return data[0]

    @protection_switch.setter
    def protection_switch(self, value):
        data = [value & 0xFF]
        self._write(self._PROTECTION_SWITCH_ADDR, data)

    @property
    def led_alarm_condition(self):
        data = self._read_address(self._LED_ALARM_CONDITION_ADDR, 1)
        return data[0]

    @led_alarm_condition.setter
    def led_alarm_condition(self, value):
        data = [value & 0xFF]
        self._write(self._LED_ALARM_CONDITION_ADDR, data)

    @property
    def position_p_gain(self):
        data = self._read_address(self._POSITION_P_GAIN_ADDR, 1)
        return data[0]

    @position_p_gain.setter
    def position_p_gain(self, value):
        if not 0 <= value <= 254:
            raise ValueError("Position P coefficient must be between 0 and 254")
        self._write(self._POSITION_P_GAIN_ADDR, [value])

    @property
    def position_d_gain(self):
        data = self._read_address(self._POSITION_D_GAIN_ADDR, 1)
        return data[0]

    @position_d_gain.setter
    def position_d_gain(self, value):
        if not 0 <= value <= 254:
            raise ValueError("Position D coefficient must be between 0 and 254")
        self._write(self._POSITION_D_GAIN_ADDR, [value])

    @property
    def position_i_gain(self):
        data = self._read_address(self._POSITION_I_GAIN_ADDR, 1)
        return data[0]

    @position_i_gain.setter
    def position_i_gain(self, value):
        if not 0 <= value <= 254:
            raise ValueError("Position P coefficient must be between 0 and 254")
        self._write(self._POSITION_I_GAIN_ADDR, [value])

    @property
    def minimum_startup_force(self):
        """
        Minimum force which needs to be applied, before the servo starts to act in percent of stall torque.
        """
        data = self._read_address(self._MINIMUM_STARTUP_FORCE_ADDR, 2)
        return int(data[0] | data[1] << 8) * 0.1

    @minimum_startup_force.setter
    def minimum_startup_force(self, value):
        if not 0.0 <= value <= 100.0:
            raise ValueError("Minimum startup force must be between 0 and 100%")
        value = int(value * 10)
        data = [value & 0xFF, value >> 8 & 0xFF]
        self._write(self._MINIMUM_STARTUP_FORCE_ADDR, data)

    @property
    def cw_dead_band(self):
        data = self._read_address(self._CW_DEAD_BAND_ADDR, 1)
        return data[0]

    @cw_dead_band.setter
    def cw_dead_band(self, value):
        if not 0 <= value <= 32:
            raise ValueError("CW insensitive zone must be between 0 and 32")
        self._write(self._CW_DEAD_BAND_ADDR, [value])

    @property
    def ccw_dead_band(self):
        data = self._read_address(self._CCW_DEAD_BAND_ADDR, 1)
        return data[0]

    @ccw_dead_band.setter
    def ccw_dead_band(self, value):
        if not 0 <= value <= 32:
            raise ValueError("CCW insensitive zone must be between 0 and 32")
        self._write(self._CCW_DEAD_BAND_ADDR, [value])

    @property
    def overload_current(self):
        data = self._read_address(self._OVERLOAD_CURRENT_ADDR, 2)
        return int(data[0] | data[1] << 8) * 6.5

    @overload_current.setter
    def overload_current(self, value):
        if not 0 <= value <= 3250:
            raise ValueError("Protective current must be between 0 and 3250mA")
        value = value // 6.5
        data = [value & 0xFF, value >> 8 & 0xFF]
        self._write(self._OVERLOAD_CURRENT_ADDR, data)

    @property
    def angular_resolution(self):
        """Amplifies the resolution of the angle measurement. Smaller means more precise. 1 means 0.0879 degrees per step."""
        data = self._read_address(self._ANGULAR_RESOLUTION_ADDR, 1)
        return data[0]

    @angular_resolution.setter
    def angular_resolution(self, value):
        if not 1 <= value <= 100:
            raise ValueError("Angle Resolution must be between 1 and 100")
        self._write(self._ANGULAR_RESOLUTION_ADDR, [int(value)])

    @property
    def position_offset(self):
        data = self._read_address(self._POSITION_OFFSET_ADDR, 2)
        return int(data[0] | (data[1] & 0x7) << 8) * (
            -1 if data[1] & 0x8 else 1
        )

    @position_offset.setter
    def position_offset(self, value):
        if not -2047 <= value <= 2047:
            raise ValueError(
                "Position correction must be between -2047 and 2047"
            )
        value = int(value)
        sign = 1 if value < -1 else 0
        data = [value & 0xFF, value & 0x7 | sign << 3]
        self._write(self._POSITION_OFFSET_ADDR, data)

    @property
    def work_mode(self):
        """Servo work or drive mode. position servo, constant speed or pwm open loop."""
        data = self._read_address(self._WORK_MODE_ADDR, 1)
        return data[0]

    @work_mode.setter
    def work_mode(self, value):
        if value not in (0, 1, 2):
            raise ValueError("Drive mode must be 0, 1 or 2")
        self._write(self._WORK_MODE_ADDR, [value])

    @property
    def protection_torque(self):
        """
        Torque which is applied when overload condition is detected in percent of maximum output torque limit.
        """
        data = self._read_address(self._PROTECTION_TORQUE_ADDR, 1)
        return data[0]

    @protection_torque.setter
    def protection_torque(self, value):
        if not 0 <= value <= 254:
            raise ValueError("Protection torque must be between 0 and 254%")
        self._write(self._PROTECTION_TORQUE_ADDR, [int(value)])

    @property
    def overload_protection_time(self):
        """
        Time for which torque needs to exceed overload torque before overload condition
        and applying protection torque in milliseconds.
        """
        data = self._read_address(self._OVERLOAD_PROTECTION_TIME_ADDR, 1)
        return data[0] * 10

    @overload_protection_time.setter
    def overload_protection_time(self, value):
        if not 0 <= value <= 2540:
            raise ValueError("Protection time must be between 0 and 2540ms")
        self._write(self._OVERLOAD_PROTECTION_TIME_ADDR, [value // 10])

    @property
    def overload_torque(self):
        """Overload torque in percent of maximum torque output limit."""
        data = self._read_address(self._OVERLOAD_TORQUE_ADDR, 1)
        return data[0]

    @overload_torque.setter
    def overload_torque(self, value):
        if not 0 <= value <= 254:
            raise ValueError("Overload torque must be between 0 and 254%")
        self._write(self._OVERLOAD_TORQUE_ADDR, [int(value)])

    @property
    def velocity_p_gain(self):
        data = self._read_address(self._VELOCITY_P_GAIN_ADDR, 1)
        return data[0]

    @velocity_p_gain.setter
    def velocity_p_gain(self, value):
        if not 0 <= value <= 254:
            raise ValueError("Velocity P coefficient must be between 0 and 254")
        self._write(self._VELOCITY_P_GAIN_ADDR, [value])

    @property
    def overcurrent_protection_time(self):
        data = self._read_address(self._OVERCURRENT_PROTECTION_TIME_ADDR, 1)
        return data[0] * 10

    @overcurrent_protection_time.setter
    def overcurrent_protection_time(self, value):
        if not 0 <= value <= 2540:
            raise ValueError(
                "Overcurrent protection time must be between 0 and 2540ms"
            )
        self._write(self._OVERCURRENT_PROTECTION_TIME_ADDR, [value // 10])

    @property
    def velocity_i_gain(self):
        data = self._read_address(self._VELOCITY_I_GAIN_ADDR, 1)
        return data[0]

    @velocity_i_gain.setter
    def velocity_i_gain(self, value):
        if not 0 <= value <= 254:
            raise ValueError("Velocity I coefficient must be between 0 and 254")
        self._write(self._VELOCITY_I_GAIN_ADDR, [value])

    @property
    def torque_enable(self):
        """Enable or disable torque mode."""
        data = self._read_address(self._TORQUE_ENABLE_ADDR, 1)
        return bool(data[0])

    @torque_enable.setter
    def torque_enable(self, value):
        self._write(self._TORQUE_ENABLE_ADDR, [int(bool(value))])

    @property
    def goal_acceleration(self):
        """
        Acceleration in steps/s2, 0 means no acceleration limit, 25400 is the maximum.
        """
        data = self._read_address(self._GOAL_ACCELERATION_ADDR, 1)
        return data[0] * 100

    @goal_acceleration.setter
    def goal_acceleration(self, value):
        if not 0 <= value <= 25400:
            raise ValueError(
                "Acceleration must be between 0 and 25400 steps/s2."
            )
        self._write(self._GOAL_ACCELERATION_ADDR, [value // 100])

    @property
    def goal_position(self):
        data = self._read_address(self._GOAL_POSITION_ADDR, 2)
        return int(data[0] | (data[1] & 0x7F) << 8) * (
            -1 if data[1] & 0x80 else 1
        )

    @goal_position.setter
    def goal_position(self, value):
        if not -32766 <= value <= 32766:
            raise ValueError(
                "Goal position must be between -32766 and 32766 steps."
            )
        value = int(value)
        sign = 1 if value < -1 else 0
        data = [value & 0xFF, value >> 8 & 0x7F | sign << 7]
        self._write(self._GOAL_POSITION_ADDR, data)

    @property
    def running_time(self):
        """Target running time for the command in milliseconds. 0 means execute as fast as possible."""
        data = self._read_address(self._RUNNING_TIME_ADDR, 2)
        return int(data[0] | (data[1] & 0xFF) << 8)

    @running_time.setter
    def running_time(self, value):
        if not 0 <= value <= 65532:
            raise ValueError("running time must be between 0 and 65532.")
        value = int(value)
        data = [value & 0xFF, value >> 8 & 0xFF]
        self._write(self._RUNNING_TIME_ADDR, data)

    @property
    def goal_velocity(self):
        """
        Goal velocity in steps/s, maximum value is 65532 * 50 steps/s, physical limit is unknown.
        """
        data = self._read_address(self._GOAL_VELOCITY_ADDR, 2)
        return int(data[0] | data[1] << 8) * 50

    @goal_velocity.setter
    def goal_velocity(self, value):
        max_vel = 65532 * 50
        if not 0 <= value <= max_vel:
            raise ValueError(
                f"Drive speed must be between 0 and {max_vel} steps/s"
            )
        value = value // 50
        data = [value & 0xFF, value >> 8 & 0xFF]
        self._write(
            self._GOAL_VELOCITY_ADDR,
            data,
        )

    @property
    def torque_limit(self):
        """Maximum applied output torque in percent. Defaults to max_torque_limit limit on startup."""
        data = self._read_address(self._TORQUE_LIMIT_ADDR, 2)
        return int(data[0] | data[1] << 8) * 0.1

    @torque_limit.setter
    def torque_limit(self, value):
        if not 0.0 <= value <= 100.0:
            raise ValueError("Torque limit must be between 0 and 100%")
        value = int(value * 10)
        data = [value & 0xFF, value >> 8 & 0xFF]
        self._write(self._TORQUE_LIMIT_ADDR, data)

    @property
    def write_lock(self):
        """Enable or disable writing values to the EEPROM. 1 means values are locked and not saved on power down."""
        data = self._read_address(self._LOCK_ADDR, 1)
        return data[0]

    @write_lock.setter
    def write_lock(self, value):
        if value not in (0, 1):
            raise ValueError("Write lock must be 0 or 1.")
        self._write(self._LOCK_ADDR, [int(value)])

    @property
    def present_position(self):
        """Current position in steps."""
        data = self._read_address(self._PRESENT_POSITION_ADDR, 2)
        return int(data[0] | (data[1] & 0x7F) << 8) * (
            -1 if data[1] & 0x80 else 1
        )

    @property
    def present_velocity(self):
        """Current velocity in steps/s."""
        data = self._read_address(self._PRESENT_VELOCITY_ADDR, 2)
        return int(data[0] | data[1] << 8) * 50

    @property
    def present_load(self):
        """Voltage duty cycle of the motor in percent."""
        data = self._read_address(self._PRESENT_LOAD_ADDR, 2)
        return int(data[0] | data[1] << 8) * 0.1

    @property
    def present_input_voltage(self):
        """Current input voltage in Volts."""
        data = self._read_address(self._PRESENT_INPUT_VOLTAGE_ADDR, 1)
        return data[0] / 10.0

    @property
    def present_temperature(self):
        """Current temperature in degrees Celsius."""
        data = self._read_address(self._PRESENT_TEMPERATURE_ADDR, 1)
        return data[0]

    @property
    def sync_write_flag(self):
        data = self._read_address(self._SYNC_WRITE_FLAG_ADDR, 1)
        return data[0]

    @property
    def moving_status(self):
        """Returns True if the motor is currently moving."""
        data = self._read_address(self._MOVING_STATUS_ADDR, 1)
        return bool(data[0])

    @property
    def present_current(self):
        """Present current in mA."""
        data = self._read_address(self._PRESENT_CURRENT_ADDR, 2)
        return int(data[0] | data[1] << 8) * 6.5

    def reset_current_position(self):
        """
        Sets current position to 2048.
        """
        self._write(self._TORQUE_ENABLE_ADDR, [128])

    def flush_all(self):
        self.device.flush()

    def check_overload_and_recover(self):
        pass  # we don't need it yet

    def dump_config(self):
        props = [
            p
            for p in dir(self.__class__)
            if isinstance(getattr(self.__class__, p), property)
        ]
        return "\n".join(f"{prop}: {getattr(self, prop)}" for prop in props)


class ServoAsyncWrite:
    """
    Context manager for executing async write commands on a group of servos.
    """

    def __init__(self, servos: Tuple[FeetechServo]):
        self.servos = servos

    def __enter__(self):
        for servo in self.servos:
            servo.enable_async_write = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        for servo in self.servos:
            servo.enable_async_write = False
        if self.servos:
            self.servos[0].execute_async_write()
