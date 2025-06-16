import socket
from enum import IntEnum
from typing import Optional
from .exceptions import ConfigurationError, CommunicationError
from .feetech_device import FeetechDevice


class EthIoRs485Interface:
    rs485_bytes = [0x80, 0x00, 0x00, 0x00, 0x00]
    # 0x80 rs485 driver ID
    # data(0)/conf(1)
    # command
    # payload size 0
    # payload size 1
    # payload

    BAUDRATES = {
        9600: 0,
        19200: 1,
        38400: 2,
        57600: 3,
        115200: 4,
        230400: 5,
        250000: 6,
        921600: 7,
        1000000: 8,
    }

    class Parity(IntEnum):
        NONE = 0
        EVEN = 1
        ODD = 2

    def __init__(
        self,
        target_ip: str,
        host_ip: str,
        port: int = 8000,
        timeout: float = 1,
    ):
        self.ip = target_ip
        self.port = port
        self.timeout = timeout
        self.host_ip = host_ip
        self._sock = None

    def _create_socket(self):
        # create UDP socket and configure non-blocking
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.setblocking(False)
            self._sock.settimeout(self.timeout)
            self._sock.bind((self.host_ip, self.port))
        except Exception as exc:
            raise CommunicationError("Failed to create UDP socket") from exc

    def config(
        self,
        speed: int = 115200,
        stopbits: int = 1,
        parity: Parity = Parity.NONE,
        wordlen: int = 8,
        invert_polarity=False,
    ) -> bool:
        self._create_socket()

        self.rs485_bytes = [0x80, 0x00, 0x00, 0x00, 0x00]
        self.rs485_bytes[1] = 0x01  # configuration
        self.rs485_bytes[2] = 0x00  # 0x00 constant
        self.rs485_bytes[3] = 0x05  # payload size 0
        self.rs485_bytes[4] = 0x00  # payload size 1

        try:
            speed = self.BAUDRATES[speed]
        except KeyError as e:
            raise ConfigurationError(
                "Baudrate must be 9600, 19200, 38400, 57600, "
                "115200, 230400, 250000, 921600 or 1000000"
            ) from e

        if stopbits < 1 or stopbits > 2:
            raise ConfigurationError("Stopbits must be 1 or 2")

        if parity < 0 or parity > 2:
            raise ConfigurationError("Parity must be 0, 1 or 2")

        if wordlen < 5 or wordlen > 8:
            raise ConfigurationError("Word length must between 5 and 8")

        stops = stopbits  # stop bits
        par = int(parity)  # parity
        invert = int(bool(invert_polarity))  # None
        bits = wordlen - 5  # word length

        payload = [speed, stops, par, invert, bits]

        try:
            self._sock.sendto(
                bytes(self.rs485_bytes + payload), (self.ip, self.port)
            )
            data, address = self._sock.recvfrom(1)
        except Exception as exc:
            raise CommunicationError(
                "Failed to configure RS485 interface"
            ) from exc

        if data[0] == 0xAA:
            return True
        elif data[0] == 0x55:
            return False
        else:
            raise CommunicationError("Unknown response from RS485 interface")

    def flush(self) -> bool:
        self.rs485_bytes = [0x80, 0x00, 0x00, 0x00, 0x00]
        self.rs485_bytes[1] = 0x01  # data
        self.rs485_bytes[2] = 0x87  # flush
        self.rs485_bytes[3] = 0x00  # payload size 0
        self.rs485_bytes[4] = 0x00  # payload size 1

        try:
            self._sock.sendto(bytes(self.rs485_bytes), (self.ip, 8000))
            data, address = self._sock.recvfrom(1)
        except Exception as exc:
            raise CommunicationError("Failed to flush RS485 interface") from exc

        return data[0] == 0xAA

    def available(self) -> Optional[int]:
        self.rs485_bytes = [0x80, 0x00, 0x00, 0x00, 0x00]
        self.rs485_bytes[1] = 0x01  # data
        self.rs485_bytes[2] = 0x83  # get available
        self.rs485_bytes[3] = 0x00  # payload size 0
        self.rs485_bytes[4] = 0x00  # payload size 1

        try:
            self._sock.sendto(bytes(self.rs485_bytes), (self.ip, 8000))
            data, address = self._sock.recvfrom(3)
        except Exception as exc:
            raise CommunicationError("Failed to get available bytes") from exc

        if data[0] == 0xAA:
            return data[2] << 8 | data[1]
        elif data[0] == 0x55:
            return None
        else:
            raise CommunicationError("Unknown response from RS485 interface")

    def transmit(self, buffer: bytes) -> bool:
        if not isinstance(buffer, bytes):
            raise ConfigurationError("Buffer must be bytes")
        bsize = len(buffer)

        if bsize > 255 or bsize < 1:
            raise ConfigurationError("Buffer must be between 1 and 255 bytes")

        bsize += 1

        self.rs485_bytes = [0x80, 0x00, 0x00, 0x00, 0x00]
        self.rs485_bytes[1] = 0x00  # data
        self.rs485_bytes[2] = 0x81  # transmit
        payload_size = bsize + 1
        self.rs485_bytes[3] = payload_size & 0xFF  # payload size 0
        self.rs485_bytes[4] = (payload_size >> 8) & 0xFF  # payload size 1
        self.rs485_bytes.append(bsize)  # bytes to transmit

        try:
            payload = bytes(self.rs485_bytes) + buffer
            print(payload)
            self._sock.sendto(payload, (self.ip, 8000))
            data, address = self._sock.recvfrom(1)
        except Exception as exc:
            raise CommunicationError("Failed to transmit data") from exc

        if data[0] == 0xAA:
            return True
        elif data[0] == 0x55:
            return False
        else:
            raise CommunicationError("Unknown response from RS485 interface")

    def receive(self, words: int, timeout_ms: int) -> Optional[bytes]:
        if words < 1 or words > 255:
            raise ConfigurationError("Words must be between 1 and 255")

        if timeout_ms < 0 or timeout_ms > 255:
            raise ConfigurationError("Timeout must be between 0 and 255")

        self.rs485_bytes = [0x80, 0x00, 0x00, 0x00, 0x00]
        self.rs485_bytes[1] = 0x00  # data
        self.rs485_bytes[2] = 0x82  # receive
        self.rs485_bytes[3] = 2  # payload size 0
        self.rs485_bytes[4] = 0  # payload size 1
        self.rs485_bytes.append(words)  # bytes to receive
        self.rs485_bytes.append(timeout_ms)

        try:
            self._sock.sendto(bytes(self.rs485_bytes), (self.ip, 8000))
            data, address = self._sock.recvfrom(words + 1)
        except Exception as exc:
            raise CommunicationError("Failed to receive data") from exc

        if data[0] == 0xAA:
            return data[1:]
        elif data[0] == 0x55:
            return None
        else:
            raise CommunicationError("Unknown response from RS485 interface")

    def trans_recv(
        self, buffer: bytes, to_read: int, wait_ms: int
    ) -> Optional[bytes]:
        if not isinstance(buffer, bytes):
            raise ConfigurationError("Buffer must be bytes")
        bsize = len(buffer)

        if to_read < 0 or to_read > 255:
            raise ConfigurationError("Bytes to read must be between 0 and 255")

        if wait_ms < 0 or wait_ms > 255:
            raise ConfigurationError("Wait time must be between 0 and 255")

        if bsize < 1 or bsize > 255:
            raise ConfigurationError("Buffer must be between 1 and 255 bytes")

        self.rs485_bytes = [0x80, 0x00, 0x00, 0x00, 0x00]
        self.rs485_bytes[1] = 0x00  # data
        self.rs485_bytes[2] = 0x86  # transmit/receive
        payload_size = bsize + 3
        self.rs485_bytes[3] = payload_size & 0xFF  # payload size 0
        self.rs485_bytes[4] = (payload_size >> 8) & 0xFF  # payload size 1
        self.rs485_bytes.append(bsize)  # bytes to transmit
        self.rs485_bytes.append(to_read)  # bytes to read

        try:
            self._sock.sendto(
                bytes(self.rs485_bytes) + buffer + bytes([wait_ms]),
                (self.ip, 8000),
            )
            data, address = self._sock.recvfrom(1 + to_read)
        except Exception as exc:
            raise CommunicationError("Failed to transmit/receive data") from exc

        if data[0] == 0xAA:
            return data[1:]
        elif data[0] == 0x55:
            return None
        else:
            raise CommunicationError("Unknown response from RS485 interface")


class UDPFeetechDevice(FeetechDevice):
    """
    UDP connection to Feetech devices on RS485 bus.
    """

    RW_TIMEOUT_S = 0.20

    def __init__(self, host_ip, target_ip, baudrate=115200):
        super().__init__()
        self.device = f"udp://{host_ip}:{target_ip}"  # for compatibility
        self.supports_read_write = True

        with self.lock:
            self._create_eth_io_interface(baudrate, host_ip, target_ip)

    def write(self, msg: bytes):
        if not self._servo_dev.transmit(msg):
            raise CommunicationError("Failed to write data")

    def read(self, n_bytes: int = 1, strict: bool = False):
        reply = self._servo_dev.receive(
            n_bytes,
            timeout_ms=0,
        )
        if not reply or (strict and len(reply) < n_bytes):
            raise CommunicationError(f"Failed to read {n_bytes} bytes")
        return reply

    def read_write(self, msg: bytes, n_bytes: int = 1, strict: bool = False):
        reply = self._servo_dev.trans_recv(
            msg, n_bytes, int(self.RW_TIMEOUT_S * 1000)
        )
        if not reply or (strict and len(reply) < n_bytes):
            raise CommunicationError(
                f"Failed to read {n_bytes} bytes, got {reply}"
            )
        return reply

    def flush(self):
        self._servo_dev.flush()

    def _create_eth_io_interface(self, baudrate, host_ip, target_ip):
        network_timeout = self.RW_TIMEOUT_S * 1.5
        self._servo_dev = EthIoRs485Interface(
            host_ip=host_ip, target_ip=target_ip, timeout=network_timeout
        )
        if self._servo_dev.config(
            speed=baudrate,
            parity=EthIoRs485Interface.Parity.NONE,
            stopbits=1,
        ):
            self._servo_dev.flush()
        else:
            raise ConfigurationError("Failed to configure RS485 interface")
