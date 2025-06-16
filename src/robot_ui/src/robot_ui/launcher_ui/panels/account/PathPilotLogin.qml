import QtQuick
import QtQuick.Controls
import pathpilot.core
import pathpilot.controls
import pathpilot.hub
import QtQuick.Layouts

Item {
  id: root

  signal tokenReceived(string token)

  readonly property bool active: login.visible

  function activate() {
    login.visible = true;
  }

  property alias email: emailTextField.text
  property alias password: passwordTextField.text

  readonly property QtObject d: QtObject {
    readonly property string loginUrl: "https://hub.pathpilot.com"

    function accepted(email, password) {
      root.hubConnector.email = email;
      root.hubConnector.password = password;
      root.hubConnector.login();
    }

    function openHubUrl() {
      ApplicationHelpers.openUrlWithDefaultApplication(loginUrl);
    }
  }

  readonly property HubConnectorWithoutRedis hubConnector: HubConnectorWithoutRedis {
    ppHubUrl: d.loginUrl

    onStatusChanged: {
      if (hubConnector.status == HubConnector.LoginStatus) {
        error.visible = false;
        console.log("HubConnector trying to login, waiting for server reply.");
      }
      if (hubConnector.status == HubConnector.IdleStatus) {
        console.log("HubConnector idle, login attempt complete or aborted.");
      }
    }

    onLoggedInChanged: {
      if (hubConnector.loggedIn) {
        console.log("HubConnector logged in, token: " + hubConnector.token);
        root.tokenReceived(hubConnector.token);
      }
    }

    onErrorStringChanged: {
      error.text = qsTr(hubConnector.errorString);
      login.visible = true;
      error.visible = true;
    }
  }

  ColumnLayout {
    id: login
    visible: false
    anchors.fill: parent
    spacing: Sizes.doubleSpacing

    VerticalFiller {
    }

    PathPilotLabel {
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      font.bold: true
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("PathPilot HUB Sign In")
    }

    PathPilotLabel {
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("Sign in to PathPilot HUB to check for and download updates.\nTo create a free HUB account, visit:")
    }

    PathPilotLabel {
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("https://hub.pathpilot.com")
      color: "blue"

      MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
          d.openHubUrl();
        }
      }
    }

    GridLayout {
      columns: 4

      Rectangle {
        Layout.preferredWidth: parent.width / 4
      }

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

      Rectangle {
        Layout.preferredWidth: parent.width / 4
      }

      Rectangle {
        Layout.preferredWidth: parent.width / 4
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

      Rectangle {
        Layout.preferredWidth: parent.width / 4
      }
    }

    RowLayout {
      HorizontalFiller {
      }

      PathPilotButton {
        id: okButton
        enabled: root.email !== "" && root.password !== ""
        text: qsTr("Sign In")
        onClicked: {
          d.accepted(root.email, root.password);
          login.visible = false;
        }
      }

      Rectangle {
        Layout.preferredWidth: parent.width / 4
      }
    }

    PathPilotLabel {
      id: error
      visible: false
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      Layout.alignment: Qt.AlignHCenter
      color: "cyan"
      text: qsTr("")
    }

    VerticalFiller {
    }
  }
}
