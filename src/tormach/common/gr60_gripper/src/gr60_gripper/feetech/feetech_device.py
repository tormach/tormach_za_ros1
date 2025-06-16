from threading import Lock


class FeetechDevice:
    RW_TIMEOUT_S = 0.2

    def __init__(self):
        self.lock = Lock()
        self.device = ""
        self.supports_read_write = False

    def write(self, msg: bytes):
        """Caller must acquire/release the lock mutex"""
        raise NotImplementedError

    def read(self, n_bytes: int = 1, strict: bool = False) -> bytes:
        """
        Read n_bytes from the device. If strict is True, raise an exception if less than n_bytes are read.

        Caller must acquire/release the lock mutex
        """
        raise NotImplementedError

    def read_write(
        self, msg: bytes, n_bytes: int = 1, strict: bool = False
    ) -> bytes:
        """
        Write msg to the device and read n_bytes from the device.
        If strict is True, raise an exception if less than n_bytes are read.

        Caller must acquire/release the lock mutex
        """
        raise NotImplementedError

    def flush(self):
        raise NotImplementedError
