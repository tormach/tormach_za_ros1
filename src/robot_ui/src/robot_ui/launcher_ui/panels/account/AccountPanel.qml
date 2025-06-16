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
  property bool attention: false

  readonly property QtObject _d: QtObject {
    id: d

    function checkAccount() {
      root.accountProvider.verifyDefaultAccount();
    }

    function checkToken(token) {
      root.accountProvider.verifyNewAccount(token);
    }

    function acquireToken() {
      login.activate();
    }

    function accountValid() {
      root.stateMachine.submitEvent("account_present");
    }

    function accountNotValid() {
      console.log("Account is not valid!");
      root.stateMachine.submitEvent('account_not_present');
    }

    function skipAccount() {
      console.log("User is skipping the PathPilot HUB account");
      root.stateMachine.submitEvent('account_skipped');
    }

    function programShutdown() {
      ShutdownSingleton.requestShutdown();
    }
  }

  EventConnection {
    events: ["token_acquired"]
    stateMachine: root.stateMachine
    onOccurred: function (event) {
      d.checkToken(event.data);
    }
  }

  EventConnection {
    events: ["account_not_present"]
    stateMachine: root.stateMachine
    onOccurred: function () {
      d.acquireToken();
    }
  }

  onVisibleChanged: {
    if (visible) {
      d.checkAccount();
    }
  }

  Connections {
    target: root.accountProvider

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onNoValidAccount() {
      d.accountNotValid();
    }

    function onValidAccount() {
      console.log('Valid account present on the machine');
      d.accountValid();
    }

    function onUserUncooperative() {
      console.log("SecretService Prompt dismissed");
      d.programShutdown();
    }
  }

  PathPilotLogin {
    id: login
    anchors.fill: parent
    visible: root.stateMachine?.acquireAccount ?? false

    onTokenReceived: function (t) {
      root.stateMachine.submitEvent('token_acquired', t);
    }

    onVisibleChanged: {
      if (visible) {
        console.log("Starting the internal web browser");
      }
    }
  }

  ColumnLayout {
    anchors.fill: parent
    spacing: Sizes.doubleSpacing

    visible: !login.active

    VerticalFiller {
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("PathPilot HUB account retrieval")
    }

    PathPilotBusyIndicator {
      Layout.alignment: Qt.AlignHCenter
    }

    VerticalFiller {
    }
  }

  PathPilotButton {
    visible: root.visible
    parent: root.buttonContainer
    text: qsTr("Skip account")
    onClicked: {
      d.skipAccount();
    }
  }
}
