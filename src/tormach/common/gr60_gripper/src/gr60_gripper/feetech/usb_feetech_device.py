import serial

from .exceptions import CommunicationError
from .feetech_device import FeetechDevice


class USB2FeetechDevice(FeetechDevice):
    """
    Serial connection to Feetech devices on RS485 bus.
    """

    RW_TIMEOUT_S = 0.2

    def __init__(self, device, baudrate=115200):
        super().__init__()
        try:
            self.device = int(
                device
            )  # stores the serial port as 0-based integer for Windows
        except ValueError:
            self.device = (
                device  # stores it as a /dev-mapped string for Linux / Mac
            )

        self._servo_dev = None

        with self.lock:
            self._open_serial(baudrate)

    @property
    def servo_dev(self):
        return self._servo_dev

    def write(self, msg):
        """Caller must acquire/release the mutex"""
        self._servo_dev.write(msg)

    def flush(self):
        self._servo_dev.flushInput()

    def read(self, n_bytes: int = 1, strict: bool = False):
        """Caller must acquire/release the mutex"""
        reply = self._servo_dev.read(n_bytes)
        if not reply or (strict and len(reply) < n_bytes):
            raise CommunicationError(
                f"read_serial: not enough bytes received (expected {n_bytes},"
                f" received {len(reply)})"
            )
        return reply

    def _open_serial(self, baudrate):
        try:
            self._servo_dev = serial.serial_for_url(
                url=self.device,
                baudrate=baudrate,
                timeout=self.RW_TIMEOUT_S,
                writeTimeout=self.RW_TIMEOUT_S,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
        except serial.serialutil.SerialException as e:
            raise RuntimeError(
                "lib_feetech: Serial port not found!\n%s" % e
            ) from e
        if self._servo_dev is None:
            raise RuntimeError('lib_feetech: Serial port not found!\n')
        self._servo_dev.flushOutput()
        self._servo_dev.flushInput()
