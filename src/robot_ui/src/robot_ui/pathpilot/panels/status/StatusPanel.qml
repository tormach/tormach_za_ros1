import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.logging
import pathpilot.handlers
import pathpilot.robot

StatusPanelBase {
  id: root
  title: qsTr("Status (F1)")
  highlighted: highlightTrigger.triggered
  highlightedColor: messageBrowser.highestSeverity == LogLevel.Warn ? Colors.orange1 : Colors.red1

  onVisibleChanged: {
    if (!visible) {
      messageTrigger.reset();
      highlightTrigger.reset();
    }
  }

  GlobalShortcut {
    id: globalShortcut
    property int previousPanel: 0
    globalShortcuts: GlobalShortcuts
    key: Qt.Key_F1

    onKeyPressedChanged: {
      if (keyPressed) {
        globalShortcut.previousPanel = Handlers.app.activePanel;
        Handlers.app.switchPanel(Panels.StatusPanel);
      } else {
        Handlers.app.switchPanel(globalShortcut.previousPanel);
      }
    }
  }

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleMargin

    LogMessageBrowser {
      id: messageBrowser
      Layout.fillWidth: true
      Layout.fillHeight: true

      logFilter {
        severityThreshold: severityCombo.level
        nodes: []
      }
    }

    MessageTrigger {
      id: messageTrigger
      topics: ["rosout_agg"]
      ready: true
      filter {
        severityThreshold: severityCombo.level > LogLevel.Error ? severityCombo.level : LogLevel.Error
      }

      onTriggeredChanged: {
        if (triggered) {
          Handlers.app.switchPanel(Panels.StatusPanel);
        }
      }
    }

    MessageTrigger {
      id: highlightTrigger
      topics: ["rosout_agg"]
      ready: true
      filter {
        severityThreshold: severityCombo.level > LogLevel.Warn ? severityCombo.level : LogLevel.Warn
      }
    }

    LogReporter {
      id: logReporter
      outputPath: Config.data.programHomePath
      rosLogPath: ROS.getLogPath()

      onLogReportCompleted: function (path) {
        Logging.log(qsTr("Log data written to file %1").arg(path), LogLevel.info);
        if (Handlers.state.hubConnector.loggedIn) {
          Handlers.state.hubConnector.uploadMachineLogdata("ZA6-Robot", path); // todo: replaced with actual machine GUID
        }
      }
    }

    ColumnLayout {
      Layout.fillWidth: false
      spacing: Sizes.singleSpacing

      IoPanel {
        id: ioPanel
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.preferredWidth: 450
      }

      RowLayout {
        PathPilotLabel {
          Layout.fillWidth: true
          horizontalAlignment: Text.AlignLeft
          text: qsTr("Log\nLevel:")
        }

        LogLevelComboBox {
          id: severityCombo
          Layout.preferredWidth: 120
          PathPilotToolTip {
            itemId: "msg_log_level"
            sidePosition: PathPilotToolTip.Side.Left
          }
        }

        PathPilotButton {
          Layout.fillWidth: true
          text: qsTr("Clear Messages")
          onClicked: {
            messageBrowser.removeAll();
            messageTrigger.reset();
            highlightTrigger.reset();
          }
          PathPilotToolTip {
            itemId: "msg_clear_messages"
            sidePosition: PathPilotToolTip.Side.Left
          }
        }

        PathPilotButton {
          Layout.fillWidth: true
          Layout.preferredWidth: 80
          text: qsTr("Log Data")
          onClicked: logReporter.createLogReport()

          PathPilotToolTip {
            itemId: "msg_log_data"
            sidePosition: PathPilotToolTip.Side.Left
          }
        }
      }
    }
  }
}
