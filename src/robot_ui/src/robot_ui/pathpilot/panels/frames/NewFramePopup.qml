import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.frame

PathPilotPopup {
  id: root
  property alias text: textInput.text
  property QtObject frames: none // Frames type, prevent type conflict
  property alias defaultPrefix: frameNameValidator.defaultPrefix

  signal accepted(string name)

  onOpened: {
    textInput.text = frameNameValidator.generateDefaultName();
    textInput.forceActiveFocus();
  }

  NameValidator {
    id: frameNameValidator
    names: frames.frameNames
    defaultPrefix: "frame_"
  }

  RowLayout {
    PathPilotLabel {
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      font.bold: true
      text: qsTr("Name:")
    }

    PathPilotTextField {
      id: textInput
      Layout.fillWidth: true
      implicitWidth: 300

      validator: FrameNameValidator {
      }

      function validate() {
        error = !frameNameValidator.validate(text, 0);
      }

      onTextEdited: {
        text = text.replace(/\s/g, '_');
        validate();
      }

      Keys.onReturnPressed: okButton.forceActiveFocus()
      Keys.onEnterPressed: okButton.forceActiveFocus()
    }
  }

  RowLayout {
    HorizontalFiller {
    }

    PathPilotButton {
      id: cancelButton
      text: qsTr("Cancel")
      onClicked: root.close()
    }

    PathPilotButton {
      id: okButton
      enabled: !textInput.error
      text: qsTr("OK")
      onClicked: {
        root.close();
        root.accepted(textInput.text);
      }
    }
  }
}
