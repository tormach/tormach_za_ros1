import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program.notification

PathPilotPopup {
  id: root
  signal accepted
  signal aborted

  property alias message: content.message
  property alias imagePath: content.imagePath
  property alias notifyType: content.notifyType
  property alias userInput: content.userInput
  closePolicy: !modal ? Popup.CloseOnEscape | Popup.CloseOnPressOutside : Popup.NoAutoClose
  modal: notifyType == NotificationMessage.Notification ? false : true
  dim: true

  onOpened: content.opened()

  NotificationPopupContent {
    id: content

    onOkClicked: {
      root.accepted();
    }
    onAbortClicked: {
      root.aborted();
    }
  }
}
