import logging
import hid
import enum

from abc import ABC
from typing import List, Callable, Optional, Any, Union

logger = logging.getLogger(__name__)


@enum.unique
class Direction(enum.IntEnum):
    DOWN = -1
    UP = 1


class ControllerItem(ABC):
    def __init__(self, data: List = []):
        self._observers = list()

    def on_event(self, event: List[int]):
        raise NotImplementedError(
            f"Not implemented in {self.__class__.__name__}"
        )

    def observe(
        self,
        callback: Callable[["ControllerItem", Union[Optional[Any]]], None],
    ) -> None:
        if not callable(callback):
            raise TypeError("Argument callback is not a callable!")

        self._observers.append(callback)

    def notify(self, *args, **kwargs) -> None:
        for observer in self._observers:
            observer(self, *args, **kwargs)


class Button(ControllerItem):
    def __init__(self, event_handler: Callable[[List], None]):
        if not callable(event_handler):
            raise TypeError("Argument event_handler must be a callable!")

        super().__init__()

        self._pressed_state = False
        self._event_handler = event_handler

    def on_event(self, event: List[int]) -> None:
        new_state = self._event_handler(event)
        if new_state != self._pressed_state:
            self._pressed_state = new_state
            self.notify(self.state)

    @property
    def state(self) -> bool:
        return self._pressed_state


class Rotary(ControllerItem):
    def __init__(self, event_handler: Callable[[List], None], state: int = 0):
        super().__init__()
        self._state = state
        self._last_direction = None
        self._event_handler = event_handler

    @property
    def last_direction(self) -> Direction:
        return self._last_direction


class Encoder(Rotary):
    def __init__(self, event_handler: Callable[[List], None]):
        super().__init__(event_handler, state=None)
        self._count = 0

    def on_event(self, event) -> None:
        new_value = self._event_handler(event)
        if self._state is None:
            self._state = new_value
            return
        if new_value != self._state:
            delta = new_value - self._state
            self._last_direction = Direction.UP if delta > 0 else Direction.DOWN
            self._state = new_value
            self._count += delta
            self.notify(self.count, self.last_direction)

    @property
    def count(self) -> int:
        return self._count


class Dial(Rotary):
    @enum.unique
    class Levels(enum.IntEnum):
        MIDDLE = 0
        HIGHEST = 7
        LOWEST = -7

    def __init__(self, event_handler: Callable[[List], None]):
        super().__init__(event_handler)

    def on_event(self, event) -> None:
        new_data = self._event_handler(event)
        if new_data < self.Levels.LOWEST or new_data > self.Levels.HIGHEST:
            return
        if new_data != self._state:
            self._last_direction = (
                Direction.UP if self._state < new_data else Direction.DOWN
            )
            self._state = new_data
            self.notify(self.state, self.last_direction)

    @property
    def state(self) -> int:
        return self._state


class TormachShuttleExpress:
    SHUTTLE_EXPRESS_VID = 2867
    SHUTTLE_EXPRESS_PID = 32
    SHUTTLE_EXPRESS_DATA_LENGTH = 40

    @enum.unique
    class Controls(enum.IntEnum):
        X = 1
        Y = 2
        Z = 3
        A = 4
        STEP = 5
        ENCODER = 6
        DIAL = 7

        @property
        def attribute_name(self) -> str:
            return f"{self.name.lower()}"

    def __init__(self):
        self._connected = False
        self._controls = {
            TormachShuttleExpress.Controls.X: Button(
                lambda x: bool(x[3] & (1 << 4))
            ),
            TormachShuttleExpress.Controls.Y: Button(
                lambda x: bool(x[3] & (1 << 5))
            ),
            TormachShuttleExpress.Controls.Z: Button(
                lambda x: bool(x[3] & (1 << 6))
            ),
            TormachShuttleExpress.Controls.A: Button(
                lambda x: bool(x[3] & (1 << 7))
            ),
            TormachShuttleExpress.Controls.STEP: Button(
                lambda x: bool(x[4] & (1 << 0))
            ),
            TormachShuttleExpress.Controls.ENCODER: Encoder(lambda x: x[1]),
            TormachShuttleExpress.Controls.DIAL: Dial(
                lambda x: int.from_bytes(
                    x[0].to_bytes(1, "big"), "big", signed=True
                )
            ),
        }

        self._device = hid.device()

    def __del__(self):
        self.disconnect()

    def __getattr__(self, attribute_name):
        for key, control in self._controls.items():
            if key.attribute_name == attribute_name:
                return control
        raise AttributeError(
            f"Object {self.__class__.__name__} has no attribute {attribute_name}."
        )

    @classmethod
    def present(cls) -> bool:
        devices = hid.enumerate()
        shuttle_express_devices = [
            device
            for device in devices
            if device.get("vendor_id", -1) == cls.SHUTTLE_EXPRESS_VID
            and device.get("product_id", -1) == cls.SHUTTLE_EXPRESS_PID
        ]
        return len(shuttle_express_devices) > 0

    def connect(self) -> None:
        """Open connection to the Tormach Shuttle Express jogger device

        Raises:
            ConnectionError: raises on issue with connection (cannot find on USB etc)
        """
        try:
            self._device.open(
                self.SHUTTLE_EXPRESS_VID, self.SHUTTLE_EXPRESS_PID
            )

            logger.info(
                f"{self.__class__.__name__}: Connected to {self._device.get_product_string()}!"
            )

        except OSError as e:
            logger.error(
                f"{self.__class__.__name__}: Tornach SE device not found: {e}"
            )
            raise ConnectionError()

        self._device.set_nonblocking(True)
        self._connected = True

    def disconnect(self):
        """Close connection to the Tormach Shuttle Express jogger device"""
        if self._connected:
            self._device.close()

    def process(self, timeout: int = 0):
        """Read from connected Tormach SE device and process the received
        data streams

        Args:
            timeout (int, optional): Blocking timeout for reading from Tormach SE jogger.
                                     Defaults to 0.

        Raises:
            TypeError: Passed parameter is not an integer
            ConnectionError: Device is not connected
            IOError: Error during reading from the hardware device
        """
        if not isinstance(timeout, int):
            raise TypeError("Argument timeout must be an int!")

        if not self._connected:
            raise ConnectionError("Device not connected!")

        try:
            read_out = self._device.read(
                self.SHUTTLE_EXPRESS_DATA_LENGTH, timeout
            )
        except Exception as e:
            logger.error(
                f"During reading from Tormach SE device following error occured: {e}"
            )
            raise OSError()
        if read_out:
            for control in self._controls.values():
                control.on_event(read_out)
