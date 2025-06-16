import os

from PySide6.QtCore import QObject, Property
from PySide6.QtQml import QmlElement, QmlSingleton

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))

QML_IMPORT_NAME = 'pathpilot.robot.frame.wizards'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class FrameWizards(QObject):
    TOOL_FRAME_WIZARD_PROGRAM = "tool_frame_wizard.py"
    USER_FRAME_WIZARD_PROGRAM = "user_frame_wizard.py"

    def __init__(self, parent=None):
        super().__init__(parent)

    @Property(str, constant=True)
    def toolFrameWizard(self):
        return os.path.join(MODULE_PATH, "tool_frame_wizard.py")

    @Property(str, constant=True)
    def userFrameWizard(self):
        return os.path.join(MODULE_PATH, "user_frame_wizard.py")
