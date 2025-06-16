import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

PathPilotPopup {
  id: root
  property alias email: emailTextField.text
  property alias password: passwordTextField.text

  signal accepted(string email, string password)

  onOpened: {
    passwordTextField.text = "";
    emailTextField.forceActiveFocus();
  }

  PathPilotLabel {
    font.family: Fonts.font2
    font.pixelSize: Fonts.filePanel.size1
    font.bold: true
    text: qsTr("PathPilot HUB Sign In")
  }

  PathPilotLabel {
    font.family: Fonts.font2
    font.pixelSize: Fonts.filePanel.size1
    horizontalAlignment: Qt.AlignLeft
    text: qsTr("Sign in to PathPilot HUB to transfer files.\nTo create a free HUB account, visit\nhttps://hub.pathpilot.com")
  }

  GridLayout {
    columns: 2

    PathPilotLabel {
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      font.bold: true
      text: qsTr("Email Address:")
    }

    PathPilotTextField {
      id: emailTextField
      implicitWidth: 300
      Layout.fillWidth: true
    }

    PathPilotLabel {
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      font.bold: true
      text: qsTr("Password:")
    }

    PathPilotTextField {
      id: passwordTextField
      Layout.fillWidth: true
      echoMode: TextInput.Password

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
      enabled: root.email !== "" && root.password !== ""
      text: qsTr("Sign In")
      onClicked: {
        root.close();
        root.accepted(root.email, root.password);
      }
    }
  }
}
