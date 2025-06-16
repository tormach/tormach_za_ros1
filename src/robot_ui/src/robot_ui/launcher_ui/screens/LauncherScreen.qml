import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import launcher_ui.panels.update 1.0
import launcher_ui.panels.config 1.0
import launcher_ui.panels.running 1.0
import launcher_ui.panels.shutdown 1.0
import launcher_ui.panels.default 1.0
import launcher_ui.panels.local 1.0
import launcher_ui.panels.eula 1.0
import launcher_ui.panels.load 1.0
import launcher_ui.panels.account 1.0
import launcher_ui.panels.internet 1.0
import launcher_ui.logic 1.0
import QtScxml

Item {
  id: root
  property alias stateMachine: scxmlLoader.stateMachine

  property RobotUILauncher robotLauncher: RobotUILauncher {
  }
  readonly property AccountProvider accountProvider: AccountProvider {
  }

  Image {
    anchors.fill: parent
    source: Icons.splashscreen.background
  }

  Connections {
    target: ShutdownSingleton

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onShutdownRequested() {
      root.stateMachine.submitEvent("shutdown");
    }
  }

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleMargin

    RowLayout {
      Layout.fillHeight: false
      Layout.alignment: Qt.AlignRight

      RowLayout {
        id: topInfoContainer
      }
    }

    Item {
      Layout.fillWidth: true
      Layout.fillHeight: true

      InternetPanel {
        id: internetPanel
        anchors.fill: parent
        stateMachine: root.stateMachine
        visible: root.stateMachine?.internet ?? false
      }

      AccountPanel {
        id: accountPanel
        anchors.fill: parent
        accountProvider: root.accountProvider
        buttonContainer: buttonContainer
        stateMachine: root.stateMachine
        visible: root.stateMachine?.account ?? false
      }

      UserAccountPanel {
        id: userAccountPanel
        stateMachine: root.stateMachine
        accountProvider: root.accountProvider
        buttonContainer: buttonContainer
        infoContainer: topInfoContainer
      }

      DefaultPanel {
        id: defaultPanel
        anchors.fill: parent
        buttonContainer: buttonContainer
        stateMachine: root.stateMachine
        visible: root.stateMachine?.defaultImageCheck ?? false
      }

      LocalImagesPanel {
        id: imagePanel
        anchors.fill: parent
        buttonContainer: buttonContainer
        stateMachine: root.stateMachine
        visible: root.stateMachine?.localSelection ?? false
      }

      EULAPanel {
        id: eulaPanel
        anchors.fill: parent
        buttonContainer: buttonContainer
        stateMachine: root.stateMachine
        visible: root.stateMachine?.eula ?? false
      }

      UpdatePanel {
        id: updatePanel
        anchors.fill: parent
        infoContainer: infoContainer
        stateMachine: root.stateMachine
        accountProvider: root.accountProvider
        visible: root.stateMachine?.update ?? false
      }

      ConfigPanel {
        id: configPanel
        anchors.fill: parent
        buttonContainer: buttonContainer
        stateMachine: root.stateMachine
        robotLauncher: root.robotLauncher
        visible: root.stateMachine?.config ?? false
      }

      LoadPanel {
        id: loadPanel
        anchors.fill: parent
        buttonContainer: buttonContainer
        stateMachine: root.stateMachine
        visible: root.stateMachine?.usbSelection ?? false
      }

      RunningPanel {
        id: runningPanel
        anchors.fill: parent
        stateMachine: root.stateMachine
        robotLauncher: root.robotLauncher
        visible: root.stateMachine?.running ?? false
        onVisibleChanged: visible ? RunningSingleton.start() : RunningSingleton.stop()
      }

      ShutdownPanel {
        id: shutdownPanel
        anchors.fill: parent
        robotLauncher: root.robotLauncher
        visible: root.stateMachine?.launcher_final ?? false
      }
    }

    RowLayout {
      Layout.fillHeight: false
      Layout.alignment: Qt.AlignRight

      Layout.minimumHeight: shutdownButton.height * 1.3

      RowLayout {
        id: infoContainer
      }

      RowLayout {
        id: buttonContainer
      }

      PathPilotButton {
        id: shutdownButton
        visible: !(root.stateMachine?.launcher_final ?? false)

        text: qsTr("Shutdown")
        horizontalAlignment: Text.AlignHCenter

        onClicked: ShutdownSingleton.requestShutdown()
      }
    }
  }

  StateMachineLoader {
    id: scxmlLoader
    source: Qt.resolvedUrl("launcher.scxml")
  }
}
