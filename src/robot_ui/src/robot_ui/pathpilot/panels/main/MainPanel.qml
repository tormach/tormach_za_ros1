import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.robot.program.notification
import pathpilot.handlers

MainPanelBase {
  id: root
  title: qsTr("Main")

  RowLayout {
    id: container
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin

    SourcePanel {
      Layout.fillHeight: true
      mdiVisible: true
      recentFilesVisible: true
      visible: !programUiLoader.visible || errorLabel.visible
    }

    PreviewPanel {
      Layout.fillWidth: true
      Layout.fillHeight: true
      visible: !programUiLoader.visible
    }

    ColumnLayout {
      Layout.fillHeight: true
      Layout.fillWidth: true
      visible: programUiLoader.visible && programUiLoader.status === Loader.Error

      RowLayout {
        Layout.fillWidth: true

        HorizontalFiller {
        }

        Icon {
          icon: Icons.program.warning
        }

        PathPilotLabel {
          id: errorLabel
          wrapMode: Text.Wrap
          font.family: Fonts.notoSansRegular.name
          font.pixelSize: Fonts.mainPanel.size1
          text: qsTr("Error loading Program UI")
          color: Colors.orange1
        }

        HorizontalFiller {
        }
      }

      PathPilotTextArea {
        Layout.fillWidth: true
        Layout.fillHeight: true
        text: programUiLoader.errorString
        font.pixelSize: Fonts.mainPanel.size2
        readOnly: true
      }
    }
  }

  Loader {
    id: programUiLoader
    property string errorString: ""
    anchors.fill: parent
    anchors.margins: Sizes.doubleMargin
    visible: active
    active: Handlers.program.programUiPath != ""
    source: active ? Handlers.program.programUiPath + "?t=" + Handlers.program.programUiTimestamp : ""

    onSourceChanged: ApplicationHelpers.clearQmlComponentCache()

    onStatusChanged: {
      if (status !== Loader.Error) {
        return;
      }
      var msg = programUiLoader.sourceComponent.errorString();
      programUiLoader.errorString = qsTr("QML Error:\n") + msg;
    }
  }

  NotificationPopup {
    id: notificationPopup
    message: Handlers.program.notifications.message.message
    imagePath: Handlers.program.notifications.message.imagePath
    notifyType: Handlers.program.notifications.message.type
    popupVisible: Handlers.program.notifications.message.active

    onAccepted: close()
    onAborted: close()
    onClosed: Handlers.program.notifications.notificationClosed(Handlers.program.notifications.message)
  }

  NotificationPopup {
    id: alertPopup
    message: Handlers.program.notifications.alertMessage.message
    imagePath: Handlers.program.notifications.alertMessage.imagePath
    notifyType: Handlers.program.notifications.alertMessage.type
    popupVisible: Handlers.program.notifications.alertMessage.active

    onOpened: {
      userInput = Handlers.program.notifications.alertMessage.default;
    }

    onAccepted: {
      if (notifyType === NotificationMessage.UserInput) {
        Handlers.program.notifications.accept(alertPopup.userInput);
      } else {
        Handlers.program.notifications.accept();
      }
    }
    onAborted: Handlers.program.notifications.abort()
  }

  AddWaypointPopup {
    id: addWaypointPopup
    Connections {
      target: Handlers.conversational

      // ignoreUnknownSignals: true // might need to reactivate with Qt6
      function onAddWaypointPopupRequested(globalMode) {
        if (globalMode !== undefined) {
          addWaypointPopup.globalMode = globalMode;
        }
        addWaypointPopup.updateMode = false;
        addWaypointPopup.open();
      }

      function onUpdateWaypointPopupRequested(name, poseMode, globalMode, hasExactPose) {
        addWaypointPopup.name = name;
        addWaypointPopup.poseMode = poseMode;
        addWaypointPopup.globalMode = globalMode;
        addWaypointPopup.updateMode = true;
        addWaypointPopup.exactPoseMode = hasExactPose;
        addWaypointPopup.open();
      }
    }
  }

  ProgramWarningsPopup {
    id: programWarningsPopup
    property var callback

    onContinueClicked: callback()

    Connections {
      target: Handlers.conversational

      // ignoreUnknownSignals: true // might need to reactivate with Qt6
      function onProgramWarningsPopupRequested(callback) {
        programWarningsPopup.callback = callback;
        programWarningsPopup.open();
      }
    }
  }
}
