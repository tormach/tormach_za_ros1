import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import launcher_ui.logic 1.0
import QtScxml

Item {
  id: root
  property StateMachine stateMachine
  property AccountProvider accountProvider
  property Item infoContainer
  signal updateCompleted

  Component.onCompleted: updateCheckerModel.updateCompleted.connect(updateCompleted)

  readonly property QtObject d: QtObject {
    property bool remoteCommunication: false
    property alias dockerSpaceAvailable: spaceChecker.dockerSpaceAvailable

    // Transitions from updateCheck
    function updateAvailable() {
      root.stateMachine.submitEvent("update_available");
    }

    function noUpdateAvailable() {
      root.stateMachine.submitEvent("no_update_available");
    }

    function checkError() {
      root.stateMachine.submitEvent("check_error");
    }

    function pullUpdate() {
      root.stateMachine.submitEvent("pull_update");
      if (dockerSpaceAvailable) {
        updateCheckerModel.downloadUpdate(updateListView.currentIndex);
      }
    }

    // Transitions from updatePulling
    function updateComplete(versionName) {
      Updater.setImage(versionName);
      root.stateMachine.submitEvent("pull_complete");
    }

    function pullError() {
      root.stateMachine.submitEvent("pull_error");
    }

    // Transitions from updateComplete
    // - Only 'selected_image'
    function acceptUpdate() {
      root.stateMachine.submitEvent("accept_update");
    }

    function skipUpdate() {
      console.log("User decided to skip updating the PathPilot Robot suite");
      root.stateMachine.submitEvent("skip_update");
    }

    function abortUpdateTasks() {
      console.log("User decided to abort all update tasks");
      updateCheckerModel.abort();
    }
  }

  EventConnection {
    events: ["account_present"]
    stateMachine: root.stateMachine
    onOccurred: function () {
      console.log("Account remotely validated");
      d.remoteCommunication = true;
      spaceChecker.check();
    }
  }

  EventConnection {
    events: ["space_checked"]
    stateMachine: root.stateMachine
    onOccurred: function () {
      console.log("Space for version checked. Available: " + d.dockerSpaceAvailable);
      d.remoteCommunication = true;
      updateCheckerModel.checkForUpdates();
    }
  }

  EventConnection {
    events: ["accept_update"]
    stateMachine: root.stateMachine
    onOccurred: function () {
      console.log("accept_update occured");
    }
  }

  Connections {
    target: root.stateMachine
    function onSystemUpdateStartChanged(state) {
      if (state) {
        baseOSUpdate.updateBaseSystem();
      }
    }
  }

  Connections {
    target: root.accountProvider
    function onDeletedAllAccount() {
      d.abortUpdateTasks();
    }
  }

  UpdateChecker {
    id: updateCheckerModel

    onCheckingCompleted: {
      if (error) {
        d.checkError();
      } else if (updatesAvailable) {
        d.updateAvailable();
      } else {
        d.noUpdateAvailable();
      }
    }
    onUpdateCompleted: function (name) {
      if (error) {
        d.pullError();
      } else {
        d.updateComplete(name);
      }
    }
  }

  BaseOSUpdate {
    id: baseOSUpdate
  }

  SpaceChecker {
    id: spaceChecker

    onCheckCompleted: {
      root.stateMachine.submitEvent('space_checked');
    }
  }

  RowLayout {
    id: updatePullingIndicator
    Layout.alignment: Qt.AlignLeft
    parent: root.infoContainer
    spacing: Sizes.doubleSpacing
    visible: (root.stateMachine?.updatePulling ?? false) && !updatePullingPopup.visible

    MouseArea {
      width: informationBlock.width
      height: informationBlock.height

      property color baseLabelColor

      z: 10
      onEntered: {
        baseLabelColor = updatePullingLabel.color;
        updatePullingLabel.color = Colors.green2;
      }
      onExited: updatePullingLabel.color = baseLabelColor
      hoverEnabled: true
      onClicked: {
        updatePullingPopup.open();
      }

      RowLayout {
        id: informationBlock

        PathPilotLabel {
          id: updatePullingLabel
          text: qsTr("Downloading new version...")
        }

        PathPilotBusyIndicator {
          Layout.alignment: Qt.AlignVCenter
          Layout.preferredHeight: 40
          Layout.preferredWidth: 40
        }
      }
    }

    HorizontalFiller {
    }
  }

  RowLayout {
    id: checkPanel
    Layout.alignment: Qt.AlignVCenter
    parent: root.infoContainer
    spacing: Sizes.doubleSpacing
    visible: (root.stateMachine?.updateCheck ?? false) && d.remoteCommunication

    PathPilotLabel {
      id: checkLabel
      text: qsTr("Checking for Updates...")
    }

    PathPilotBusyIndicator {
      Layout.alignment: Qt.AlignVCenter
      Layout.preferredHeight: 40
      Layout.preferredWidth: 40
    }

    HorizontalFiller {
    }
  }

  PathPilotPopupBase {
    id: askUserPopup
    spacing: Sizes.doubleSpacing
    visible: root.stateMachine?.updateAskUser ?? false

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
      text: qsTr("New updates available")
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
      color: Colors.orange1
      text: qsTr("No available space, remove unused versions!")
      visible: !d.dockerSpaceAvailable
    }

    UpdateListView {
      id: updateListView
      Layout.fillWidth: true
      Layout.fillHeight: true
      Layout.preferredWidth: 500
      Layout.minimumHeight: 100
      model: updateCheckerModel
    }

    RowLayout {
      PathPilotButton {
        Layout.fillWidth: true
        enabled: updateListView.versionSelected && d.dockerSpaceAvailable
        implicitWidth: 200
        horizontalAlignment: Text.AlignHCenter
        text: qsTr("Download now")
        onClicked: d.pullUpdate()
      }

      PathPilotButton {
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignHCenter
        text: qsTr("Close")
        onClicked: d.skipUpdate()
      }
    }
  }

  PathPilotPopupBase {
    id: updatePullingPopup
    visible: root.stateMachine?.updatePulling ?? false

    ColumnLayout {
      id: updatePullingPanel
      spacing: Sizes.doubleSpacing

      Component.onCompleted: {
        updatePullingPopup.width = width * 1.2;
      }

      VerticalFiller {
      }

      PathPilotLabel {
        Layout.alignment: Qt.AlignHCenter
        text: qsTr("Downloading new image")
      }

      PathPilotBusyIndicator {
        Layout.alignment: Qt.AlignHCenter
      }

      PathPilotLabel {
        Layout.alignment: Qt.AlignHCenter
        font.family: Fonts.font2
        text: qsTr("Progress:\nLayers downloaded %1%\nCurrent layer download %2%").arg(updateCheckerModel.pullProgressOverall).arg(updateCheckerModel.pullProgressCurrent)
      }

      RowLayout {
        PathPilotButton {
          Layout.fillWidth: true
          implicitWidth: 200
          horizontalAlignment: Text.AlignHCenter
          text: qsTr("Download in background")
          onClicked: updatePullingPopup.close()
        }
      }
    }
  }

  PathPilotPopupBase {
    id: updateCompletePopup
    implicitWidth: root.width * 0.8
    spacing: Sizes.doubleSpacing
    visible: root.stateMachine?.updateComplete ?? false

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr(updateCheckerModel.statusMessage)
    }

    PathPilotTextArea {
      Layout.alignment: Qt.AlignHCenter
      Layout.fillWidth: true
      font.pixelSize: Fonts.launcher.size1
      text: qsTr(updateCheckerModel.errorMessage)
      visible: updateCheckerModel.error
      wrapMode: TextArea.WrapAnywhere
    }

    RowLayout {
      HorizontalFiller {
      }

      PathPilotButton {
        id: okButton
        Layout.alignment: Qt.AlignHCenter
        text: qsTr("Close")
        onClicked: {
          d.acceptUpdate();
        }
      }
    }
  }
}
