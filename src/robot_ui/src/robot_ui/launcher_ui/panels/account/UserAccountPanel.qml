import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import launcher_ui.logic 1.0
import launcher_ui.panels.shutdown 1.0
import QtScxml

Item {
  id: root
  property StateMachine stateMachine
  property AccountProvider accountProvider
  property Item buttonContainer
  property Item infoContainer

  readonly property QtObject _d: QtObject {
    id: d

    property bool remoteCommunication: false

    function logout() {
      console.log("User requested complete logout");
      accountProvider.logout();
    }

    function login() {
      console.log("User requested login");
      root.stateMachine.submitEvent("login_requested");
    }
  }

  EventConnection {
    events: ["internet_available"]
    stateMachine: root.stateMachine
    onOccurred: function () {
      d.remoteCommunication = true;
    }
  }

  PathPilotLabel {
    parent: infoContainer
    visible: accountProvider.userAccountExists
    text: qsTr("Logged in: %1 %2, %3").arg(root.accountProvider.userForename).arg(root.accountProvider.userSurname).arg(root.accountProvider.userEmailAddress)
  }

  PathPilotButton {
    horizontalAlignment: Text.AlignHCenter
    text: qsTr("Logout")
    parent: buttonContainer
    visible: accountProvider.userAccountExists && (root.stateMachine?.select ?? false)

    onClicked: d.logout()
  }

  PathPilotButton {
    horizontalAlignment: Text.AlignHCenter
    text: qsTr("Login")
    parent: buttonContainer
    visible: !root.accountProvider.userAccountExists && (root.stateMachine?.select ?? false) && d.remoteCommunication

    onClicked: d.login()
  }
}
