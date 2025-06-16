import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.robot.program.notification

ColumnLayout {
  id: root
  signal okClicked
  signal abortClicked

  property string message: ""
  property string imagePath: ""
  property int notifyType: NotificationMessage.Notification
  property alias userInput: inputTextField.text

  property int _width: 400
  Layout.preferredWidth: _width
  spacing: Sizes.singleSpacing

  function opened() {
    if (notifyType === NotificationMessage.Notification) {
      okButton.forceActiveFocus();
    } else if (notifyType === NotificationMessage.UserInput) {
      inputTextField.forceActiveFocus();
    } else {
      abortButton.forceActiveFocus();
    }
  }

  RowLayout {
    spacing: Sizes.doubleSpacing
    Icon {
      icon: (root.notifyType === NotificationMessage.Warning) ? Icons.popup.warning : (root.notifyType === NotificationMessage.Error) ? Icons.popup.error : Icons.popup.notification
    }

    PathPilotLabel {
      text: (root.notifyType === NotificationMessage.Warning) ? qsTr("Warning") : (root.notifyType === NotificationMessage.Error) ? qsTr("Error") : qsTr("Notification")
      font.pixelSize: Fonts.notificationPopup.size2
    }
  }

  PathPilotLabel {
    Layout.fillWidth: true
    font.family: Fonts.font2
    font.pixelSize: Fonts.notificationPopup.size1
    font.bold: true
    horizontalAlignment: Text.AlignLeft
    wrapMode: Text.Wrap
    text: root.message
  }

  Image {
    id: image
    Layout.fillWidth: true
    fillMode: Image.PreserveAspectFit
    autoTransform: true
    sourceSize.width: root._width
    source: root.imagePath
    cache: false
  }

  PathPilotTextField {
    id: inputTextField
    Layout.fillWidth: true
    visible: root.notifyType === NotificationMessage.UserInput

    Keys.onReturnPressed: function (event) {
      event.accepted = true;
    }
    Keys.onEnterPressed: function (event) {
      event.accepted = true;
    }
    Keys.onReleased: function (event) {
      if ([Qt.Key_Return, Qt.Key_Enter].includes(event.key) && (!event.isAutoRepeat)) {
        root.okClicked();
      }
    }
  }

  RowLayout {
    HorizontalFiller {
    }

    PathPilotButton {
      id: abortButton
      visible: root.notifyType !== NotificationMessage.Notification
      implicitWidth: 120
      text: qsTr("Abort")
      onClicked: root.abortClicked()
    }

    PathPilotButton {
      id: okButton
      visible: root.notifyType !== NotificationMessage.Error
      implicitWidth: 120
      text: qsTr("OK")
      onClicked: root.okClicked()
    }
  }
}
