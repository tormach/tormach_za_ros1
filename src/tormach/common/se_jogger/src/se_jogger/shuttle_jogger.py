import threading
import enum

import logging

# import shuttle_express as se
from . import shuttle_express as se

# from typing import Int
from typing import Callable

from redis_store import ConfigClient

from rospy import Subscriber, ServiceProxy
from robot_ui_msgs.msg import ActivePanel
from robot_ui_msgs.srv import LockPanel, LockPanelRequest  # , LockPanelResponse

import unique_id
from uuid import UUID, uuid1


import robot_jog.interactive_move.interactive_move_client as interactive_move_client

import fysom

import pint

logger = logging.getLogger(__name__)


class Timer:
    def __init__(
        self,
        delay: int,
        callback: Callable,
        *args,
        **kwargs,
    ):
        self._callback = callback
        self._delay = delay
        self._args = args
        self._kwargs = kwargs
        self._timer = None

        self._start()

        logger.info(f"Timer created with expiration in {delay}.")

    @property
    def done(self) -> bool:
        return self._done

    @property
    def expired(self) -> bool:
        return self._expired

    def _start(self):
        self._done = False
        self._expired = False
        self._timer = threading.Timer(self._delay, self._execute)
        self._timer.start()

    def _execute(self):
        self._expired = True
        self._callback(*self._args, **self._kwargs)
        self._done = True

    def cancel(self):
        if self._timer:
            self._timer.cancel()
        self._timer = None
        self._done = True

    def reschedule(self, delay: int = None):
        self.cancel()
        if delay:
            self._delay = delay
        self._start()


class TormachShuttleExpressJogger:
    @enum.unique
    class Sense(enum.IntEnum):
        X = 1
        Y = 3
        Z = 5
        A = 2
        B = 6
        C = 10

    @enum.unique
    class Joints(enum.Enum):
        J1 = (1, 1)
        J2 = (3, 2)
        J3 = (5, 3)
        J4 = (2, 4)
        J5 = (6, 5)
        J6 = (10, 6)

        def __init__(self, sense, joint):
            self._value_ = joint
            self._sense = sense

        @classmethod
        def get_item(cls, *args, **kwargs):
            sense = "sense"
            value = "value"

            searched = None
            object_member = None

            if sense in kwargs.keys():
                searched = kwargs[sense]
                object_member = sense
            elif value in kwargs.keys():
                searched = kwargs[value]
                object_member = value

            if (
                searched is not None
                and object_member is not None
                and isinstance(searched, int)
            ):
                for _, item in cls.__members__.items():
                    if getattr(item, object_member) == searched:
                        return item

            return super()._missing_(*args, **kwargs)

        @property
        def joint(self) -> str:
            return f"joint_{self.value}"

        @property
        def sense(self) -> int:
            return self._sense

    @enum.unique
    class StepSize(enum.Enum):
        S1 = (0, 0.1)
        S2 = (1, 1.0)
        S3 = (2, 10.0)
        S4 = (3, 100.0)

        def __init__(self, identificator, size):
            self._value_ = size
            self._identificator = identificator

        @classmethod
        def get_item(cls, *args, **kwargs):
            identificator = "identificator"
            value = "value"

            searched = None
            object_member = None

            if identificator in kwargs.keys():
                searched = kwargs[identificator]
                object_member = identificator
            elif value in kwargs.keys():
                searched = kwargs[value]
                object_member = value

            if (
                searched is not None
                and object_member is not None
                and isinstance(searched, (float, int))
            ):
                for _, item in cls.__members__.items():
                    if getattr(item, object_member) == searched:
                        return item

            return super()._missing_(*args, **kwargs)

        def next(self):
            _next = False

            _value_list = [
                value for _, value in self.__class__.__members__.items()
            ]

            for value in _value_list:
                if _next:
                    return value
                if value == self:
                    _next = True

            return _value_list[0]

        @property
        def identificator(self) -> int:
            return self._identificator

    @enum.unique
    class States(enum.Enum):
        deactivated = "deactivated"
        # activation_started = "activation_started"
        # semi_activated = "semi_activated"
        # activation_confirmed = "activation_confirmed"
        ready = "ready"
        engaged = "engaged"
        joint_jogging_selected = "joint_jogging"
        each = "*"

        def __str__(self):
            return str(self.value)

    @enum.unique
    class Events(enum.Enum):
        activate = "activate"
        deactivate = "deactivate"
        engage = "engage"
        disengage = "disengage"
        select_joint = "select_joint"

        def __str__(self):
            return str(self.value)

    @enum.unique
    class PPROSIdentificators(enum.Enum):
        Jogger_step_size = "user_config/jog/step_size"
        Robot_linear_unit = "user_config/angular_unit"
        Jogger_joint = "user_config/jog/joint"

    @enum.unique
    class PPROSTopics(enum.Enum):
        Active_panel = "robot_ui/active_panel"

    @enum.unique
    class PPROSServices(enum.Enum):
        Lock_panel = "robot_ui/lock_panel"

    @enum.unique
    class RobotUIPanels(enum.IntEnum):
        Unknown = -1
        MainPanel = 0
        FilePanel = 1
        FramePanels = 2
        SettingsPanel = 3
        ConversationalPanel = 4
        JogPanel = 5
        StatusPanel = 6

    @enum.unique
    class Units(enum.Enum):
        ROS_angular_unit = "rad"

    @enum.unique
    class Timeouts(enum.IntEnum):
        inactivity = 120
        activation = 2

    def __init__(self):
        self.pressed_buttons = list()
        # self.activation_buttons = list()
        self._shift = False
        self._active_axis = None
        self.__active_joint = None
        self._encoder_last_direction = None

        self._error_observers = []

        self._config = ConfigClient(subscribe=True)

        self._active_joint = self.Joints.get_item(
            value=self._config.get_param(
                self.PPROSIdentificators.Jogger_joint.value
            )
        )

        self._step_size = self.StepSize.get_item(
            identificator=self._config.get_param(
                self.PPROSIdentificators.Jogger_step_size.value
            )
        )
        self._active_angular_unit = self._config.get_param(
            self.PPROSIdentificators.Robot_linear_unit.value
        )

        self._tormach_shuttle_express = se.TormachShuttleExpress()
        self._interactive_move_client = (
            interactive_move_client.InteractiveMoveClient()
        )

        self._config.on_update_received.append(self._on_config_change_received)

        # self._activation_timer: Timer = None
        self._engagement_timer: Timer = None

        self._uuid: UUID = uuid1()

        self._run_thread = None
        self._run_thread_stop_event = None

        self._unit_registry = pint.UnitRegistry()

        self._fsm = fysom.Fysom(
            initial=self.States.deactivated.value,
            events=[
                {
                    "name": f"{self.Events.deactivate}",
                    "src": f"{self.States.each}",
                    "dst": f"{self.States.deactivated}",
                },
                # {
                #    "name": f"{self.Events.activate}",
                #    "src": f"{self.States.deactivated}",
                #    "dst": f"{self.States.activation_started}",
                # },
                # {
                #    "name": f"{self.Events.activate}",
                #    "src": f"{self.States.activation_started}",
                #    "dst": f"{self.States.semi_activated}",
                # },
                # {
                #    "name": f"{self.Events.activate}",
                #    "src": f"{self.States.semi_activated}",
                #    "dst": f"{self.States.activation_confirmed}",
                # },
                {
                    "name": f"{self.Events.activate}",
                    "src": f"{self.States.deactivated}",
                    "dst": f"{self.States.ready}",
                },
                {
                    "name": f"{self.Events.engage}",
                    "src": [f"{self.States.ready}", f"{self.States.engaged}"],
                    "dst": f"{self.States.engaged}",
                },
                {
                    "name": f"{self.Events.disengage}",
                    "src": f"{self.States.engaged}",
                    "dst": f"{self.States.ready}",
                },
                {
                    "name": self.Events.select_joint.value,
                    "src": [
                        self.States.ready.value,
                        self.States.joint_jogging_selected.value,
                    ],
                    "dst": self.States.joint_jogging_selected.value,
                },
            ],
            callbacks={
                f"on_before_{self.Events.activate}": self._on_before_event_activate,
                f"on_before_{self.Events.engage}": self._on_before_event_engage,
                # f"on_before_{self.Events.disengage}": self._on_before_event_disengage,
                f"on_{self.Events.deactivate}": self._on_event_deactivate,
                f"on_{self.States.ready}": self._on_state_ready,
                f"on_before_{self.Events.select_joint}": self._on_before_event_select_joint,
                "onchangestate": self._on_enter_state,
            },
        )

        self._tormach_shuttle_express.x.observe(self.button_x_changed)
        self._tormach_shuttle_express.y.observe(self.button_y_changed)
        self._tormach_shuttle_express.z.observe(self.button_z_changed)
        self._tormach_shuttle_express.a.observe(self.button_a_changed)
        self._tormach_shuttle_express.step.observe(self.button_step_changed)

        self._tormach_shuttle_express.encoder.observe(self.encoder_changed)
        self._tormach_shuttle_express.dial.observe(self.dial_changed)

        self._active_panel_topic = Subscriber(
            self.PPROSTopics.Active_panel.value,
            ActivePanel,
            self._on_active_panel_changed,
        )

        self._lock_panel_service = ServiceProxy(
            self.PPROSServices.Lock_panel.value, LockPanel
        )

    @classmethod
    def can_open(cls) -> bool:
        return se.TormachShuttleExpress.present()

    def _destroy(self):
        self._active_panel_topic.unregister()

    def _on_config_change_received(self, *args, **kwargs):
        if args[0] == self.PPROSIdentificators.Jogger_step_size.value:
            if self._step_size.identificator != args[1]:
                self._step_size = self.StepSize.get_item(identificator=args[1])
                # self._fsm.deactivate()
        elif args[0] == self.PPROSIdentificators.Robot_linear_unit.value:
            if self._active_angular_unit != args[1]:
                self._active_angular_unit = args[1]
                # self._fsm.deactivate()
        elif args[0] == self.PPROSIdentificators.Jogger_joint.value:
            if self._active_joint.value != args[1]:
                self._active_joint = self.Joints.get_item(value=args[1])
                # self._fsm.deactivate()

    def _on_active_panel_changed(self, data: ActivePanel):
        if data.active_panel.data == self.RobotUIPanels.JogPanel.value:
            self._fsm.activate()
        else:
            self._fsm.deactivate()

    def _signal_receive(self, controller):
        if self.active:
            self._lock_panel_service(
                LockPanelRequest(
                    identifier=unique_id.toMsg(self._uuid), lock=True
                )
            )
            if not self._engagement_timer:
                self._engagement_timer = Timer(
                    self.Timeouts.activation.value, self._disengage
                )
            else:
                self._engagement_timer.reschedule(
                    self.Timeouts.activation.value
                )
        logger.info(f"Received controller action with {type(controller)}")

    def _emergency_cancellation(self):
        if self._interactive_move_client.active:
            self._interactive_move_client.stop()
            return True

        return False

    def _on_event_deactivate(self, e):
        pass
        # self.activation_buttons = list()
        # if self._activation_timer:
        #    if not self._activation_timer.expired:
        #        self._activation_timer.cancel()
        #    self._activation_timer = None

    def _on_event_disengagement(self, e):
        if self._egagement_timer:
            if not self._egagement_timer.expired:
                self._egagement_timer.cancel()
            self._egagement_timer = None

    def _on_state_ready(self, e):
        # self._activation_timer.reschedule(self.Timeouts.inactivity.value)
        if self._active_joint:
            self._fsm.select_joint()

    def _on_before_event_activate(self, e):
        pass
        # if not self._activation_timer:
        #    self._activation_timer = Timer(
        #        self.Timeouts.activation.value, self._fsm.deactivate
        #    )
        # else:
        #    self._activation_timer.reschedule(self.Timeouts.activation.value)

    def _on_before_event_engage(self, e):
        if not self._engagement_timer:
            self._engagement_timer = Timer(
                self.Timeouts.activation.value, self._fsm.disengage()
            )
        else:
            self._engagement_timer.reschedule(self.Timeouts.activation.value)

        logger.info("Locking panels")
        self._lock_panel_service(
            LockPanelRequest(identifier=unique_id.toMsg(self._uuid), lock=True)
        )

    def _disengage(self):  # _on_before_event_disengage(self, e):
        logger.info("Removing the panel lock")
        self._lock_panel_service(
            LockPanelRequest(identifier=unique_id.toMsg(self._uuid), lock=False)
        )

    def _on_enter_state(self, e):
        logger.info(
            f"The Tormach SE device entered a new state: {e.fsm.current}."
        )

    def _on_before_event_select_joint(self, e=None):
        if self._active_joint and (e is None or not hasattr(e, "joint")):
            return

        if self._shift:
            multiplier = 2
        else:
            multiplier = 1

        self._active_joint = self.Joints.get_item(
            sense=(multiplier * e.joint.value)
        )
        self._config.set_param(
            self.PPROSIdentificators.Jogger_joint.value,
            self._active_joint.value,
        )
        logger.info(f"New active joint is {self.active_joint.name}")

    def _on_before_event_select_axis(self, e=None):
        if self._active_axis and (e is None or not hasattr(e, "joint")):
            return

        if self._shift:
            multiplier = 2
        else:
            multiplier = 1

        self._active_axis = self.Sense(multiplier * e.joint.value)
        logger.info(f"New axis is {self.active_axis.name}")

    def _error_occured(self, reason=""):
        for observer in self._error_observers:
            observer(reason)

    def add_error_observer(self, error_callable: Callable[[str], None]):
        self._error_observers.append(error_callable)

    @property
    def active(self) -> bool:
        return self._fsm.current not in [
            self.States.deactivated.value,
            self.States.engaged.value,
            # self.States.activation_started.value,
            # self.States.semi_activated.value,
            # self.States.activation_confirmed.value,
        ]

    @property
    def engaged(self) -> bool:
        return self._fsm.current == self.States.engaged.value

    @property
    def active_axis(self):
        return self._active_axis if self._active_axis else "Unknown"

    @property
    def active_joint(self):
        return self._active_joint if self._active_joint else "Unknown"

    def _list_button(self, button):
        if button.state:
            if button not in self.pressed_buttons:
                self.pressed_buttons.append(button)
        else:
            if button in self.pressed_buttons:
                self.pressed_buttons.remove(button)

    def button_x_changed(self, controller, pressed):
        self._emergency_cancellation()
        self._list_button(controller)

        if self.active and not pressed:
            self._fsm.select_joint(joint=self.Sense.X)

        self._signal_receive(controller)

    def button_y_changed(self, controller, pressed):
        self._emergency_cancellation()
        self._list_button(controller)

        if self.active and not pressed:
            self._fsm.select_joint(joint=self.Sense.Y)

        self._signal_receive(controller)

    def button_z_changed(self, controller, pressed):
        self._emergency_cancellation()
        self._list_button(controller)

        if self.active and not pressed:
            self._fsm.select_joint(joint=self.Sense.Z)

        self._signal_receive(controller)

    def button_a_changed(self, controller, pressed):
        self._emergency_cancellation()
        self._list_button(controller)

        if self.active:
            self._shift = pressed

        self._signal_receive(controller)

    def button_step_changed(self, controller, pressed):
        self._emergency_cancellation()
        self._list_button(controller)

        if self.active and not pressed:
            self._step_size = self._step_size.next()
            self._config.set_param(
                self.PPROSIdentificators.Jogger_step_size.value,
                self._step_size.identificator,
            )
            logger.info(f"Setting Step size to {self._step_size}")

        self._signal_receive(controller)

    def encoder_changed(self, controller, count, last_direction):
        if self.active:
            if last_direction != self._encoder_last_direction:
                if self._emergency_cancellation():
                    return
        if (
            self.active
        ):  # self._fsm.current == f"{self.States.joint_jogging_selected}":
            size = self._unit_registry.Quantity(
                self._step_size.value, self._active_angular_unit
            ).to(self.Units.ROS_angular_unit.value)
            self._interactive_move_client.set_offset_joints_target(
                [self._active_joint.joint],
                [size if last_direction > 0 else -size],
            )
            self._encoder_last_direction = last_direction
            self._interactive_move_client.start()
        self._signal_receive(controller)

    def dial_changed(self, controller, state, last_direction):
        self._signal_receive(controller)

    def start(self):
        if self._run_thread:
            return

        self._tormach_shuttle_express.connect()
        self._run_thread_stop_event = threading.Event()
        self._run_thread = threading.Thread(
            name="tormach_jogger_working_thread", target=self.churn
        )
        self._run_thread.start()

    def stop(self):
        if not self._run_thread:
            return

        # if self._activation_timer:
        #    self._activation_timer.cancel()

        self._run_thread_stop_event.set()
        if self._run_thread.is_alive():
            self._run_thread.join()

        self._tormach_shuttle_express.disconnect()
        self._disengage()
        self._destroy()

        self._run_thread_stop_event = None
        self._run_thread = None

    def churn(self):
        try:
            while not self._run_thread_stop_event.is_set():
                self._tormach_shuttle_express.process(250)
        except Exception:
            self._error_occured(
                "Error occured during reading of the pendant hardware"
            )
