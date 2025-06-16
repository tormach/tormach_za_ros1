import rospy
import unique_id

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QmlElement

from robot_ui_msgs.msg import Panels, ActivePanel
from robot_ui_msgs.srv import (
    SwitchPanel,
    SwitchPanelRequest,
    SwitchPanelResponse,
    LockPanel,
    LockPanelRequest,
    LockPanelResponse,
)
from std_msgs.msg import Bool, Header

from uuid import UUID, uuid1
from typing import Union, List

from .panels import PanelEnum
from .panels import Panels as PanelsQML

from ..qt_helpers import ensure_cleanup

MODULE = "robot_ui"

QML_IMPORT_NAME = 'pathpilot.handlers'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class PanelSwitcher(QObject):
    ACTIVE_PANEL_TOPIC = f"{MODULE}/active_panel"
    PANEL_LOCKED_TOPIC = f"{MODULE}/panel_locked"

    SWITCH_PANEL_SERVICE = f"{MODULE}/switch_panel"
    LOCK_PANEL_SERVICE = f"{MODULE}/lock_panel"

    activePanelChanged = Signal(int)
    panelLockedChanged = Signal(bool)

    ################################################################################
    # Initialization and destruction functionality
    ################################################################################

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_panel = PanelEnum.MainPanel
        self._panel_locked = False
        self._panel_lock_applicants: List[UUID] = list()
        self._qml_uuid = uuid1()
        self._staged_panel: Union[int, PanelEnum, None] = None

        self._active_panel_publisher = rospy.Publisher(
            self.ACTIVE_PANEL_TOPIC, ActivePanel, latch=True, queue_size=1
        )
        self._panel_locked_publisher = rospy.Publisher(
            self.PANEL_LOCKED_TOPIC, Bool, latch=True, queue_size=1
        )

        self._switch_panel_service = rospy.Service(
            self.SWITCH_PANEL_SERVICE,
            SwitchPanel,
            self._on_switch_panel_request,
        )
        self._lock_panel_service = rospy.Service(
            self.LOCK_PANEL_SERVICE, LockPanel, self._on_lock_panel_request
        )

        self._active_panel_publisher.publish(
            ActivePanel(
                header=Header(stamp=rospy.Time.now()),
                active_panel=Panels(data=self._active_panel),
            )
        )
        self._panel_locked_publisher.publish(self._panel_locked)

        ensure_cleanup(self._dismantle)

    @Slot()
    def _dismantle(self):
        self._active_panel_publisher.unregister()
        self._panel_locked_publisher.unregister()

        self._switch_panel_service.shutdown()
        self._lock_panel_service.shutdown()

    ################################################################################
    # Main functionality
    ################################################################################

    def _switch_panel(self, new_panel: int):
        self._active_panel = new_panel
        self._signal_active_panel_change()

    def _lock_panel(self, applicant: Union[UUID, str]) -> bool:
        if isinstance(applicant, str):
            applicant = UUID(applicant)

        if not self._panel_locked:
            self._panel_locked = True
            self._signal_panel_locked_change()
        if applicant not in self._panel_lock_applicants:
            self._panel_lock_applicants.append(applicant)
        return True

    def _unlock_panel(self, applicant: Union[UUID, str]) -> bool:
        if isinstance(applicant, str):
            applicant = UUID(applicant)

        if applicant not in self._panel_lock_applicants:
            return False
        self._panel_lock_applicants.remove(applicant)
        if len(self._panel_lock_applicants) == 0:
            self._panel_locked = False
            self._signal_panel_locked_change()
            if self._staged_panel is not None:
                self._active_panel = self._staged_panel
                self._staged_panel = None
                self._signal_active_panel_change()
            return True
        else:
            return False

    ################################################################################
    # Common ROS and Qt helper functions
    ################################################################################

    def _signal_active_panel_change(self):
        self._active_panel_publisher.publish(
            ActivePanel(
                header=Header(stamp=rospy.Time.now()),
                active_panel=Panels(data=self._active_panel),
            )
        )
        self.activePanelChanged.emit(self._active_panel)

    def _signal_panel_locked_change(self):
        self._panel_locked_publisher.publish(self._panel_locked)
        self.panelLockedChanged.emit(self._panel_locked)

    ################################################################################
    # ROS "public" facing functions
    ################################################################################

    def _on_switch_panel_request(
        self, request: SwitchPanelRequest
    ) -> SwitchPanelResponse:
        if self._panel_locked:
            return SwitchPanelResponse(result=False)
        self._switch_panel(request.new_panel.data)
        return SwitchPanelResponse(result=True)

    def _on_lock_panel_request(
        self, request: LockPanelRequest
    ) -> LockPanelResponse:
        if request.lock:
            return LockPanelResponse(
                result=self._lock_panel(unique_id.fromMsg(request.identifier))
            )
        else:
            return LockPanelResponse(
                result=self._unlock_panel(unique_id.fromMsg(request.identifier))
            )

    ################################################################################
    # Qt QML "public" facing functions
    ################################################################################

    @Property(int, notify=activePanelChanged)
    def activePanel(self) -> PanelsQML:
        return self._active_panel

    @activePanel.setter
    def activePanel(self, value):
        if not self._panel_locked and self._active_panel != value:
            self._active_panel = value
            self._signal_active_panel_change()

    @Property(bool, notify=panelLockedChanged)
    def panelLocked(self) -> bool:
        return self._panel_locked

    @Slot(bool, result=bool)
    def lockPanel(self, state: bool) -> bool:
        if state:
            return self._lock_panel(self._qml_uuid)
        else:
            return self._unlock_panel(self._qml_uuid)

    @Slot(int, result=bool)
    def trySwitchPanelWithNextItem(self, new_panel: int) -> bool:
        if self._active_panel != new_panel:
            if not self._panel_locked:
                self._active_panel = new_panel
                self._signal_active_panel_change()
                return True
            else:
                self._staged_panel = (
                    new_panel  # What if there already is a staged panel?
                )
                return False
        return True

    @Slot(int, result=bool)
    def trySwitchPanel(self, new_panel: int) -> bool:
        if new_panel is None:
            return False

        if self._active_panel != new_panel:
            if not self._panel_locked:
                self._active_panel = new_panel
                self._signal_active_panel_change()
                return True
            else:
                return False
        return True
