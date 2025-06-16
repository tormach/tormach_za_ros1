import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.logging
import pathpilot.development

UnscaledTestBase {
  id: root

  MessageGenerator {
    id: messageGenerator
    message: "A very long and meaningful message is about to be injected into the view\nBe aware that this might cause line breaks to appear."
    verbosity: MessageGenerator.Info
    running: true
  }

  MessageGenerator {
    message: "A more severe error.\n-- EXTENDED INFO --\nWith loads of information atached to it.\nMore and more and more."
    verbosity: MessageGenerator.Error
    running: true
    interval: 3333
  }

  MessageGenerator {
    message: "Warning, systems going to fail soon."
    verbosity: MessageGenerator.Warn
    running: true
    interval: 6000
  }

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin

    LogMessageBrowser {
      id: messageBrowser
      Layout.fillWidth: true
      Layout.fillHeight: true

      logFilter {
        severityThreshold: severityCombo.level
        nodes: logAllCheck.checked ? [] : ["/robot_ui"]
      }
    }

    RowLayout {
      spacing: Sizes.doubleSpacing
      HorizontalFiller {
      }

      CheckBox {
        id: logAllCheck
        text: qsTr("Log All")
      }

      Spacer {
        vertical: true
      }

      PathPilotLabel {
        text: qsTr("Log level:")
      }

      LogLevelComboBox {
        id: severityCombo
      }

      Spacer {
        vertical: true
      }

      PathPilotButton {
        text: qsTr("Clear")
        onClicked: messageBrowser.removeAll()
      }
    }
  }
}
