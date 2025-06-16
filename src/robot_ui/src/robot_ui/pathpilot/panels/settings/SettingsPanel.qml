import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.conversational
import pathpilot.handlers

SettingsPanelBase {
  id: root
  title: qsTr("Settings")
  enabled: Handlers.app.modifySettingsAllowed

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleMargin

    PathPilotInstanceSelection {
      id: instanceSelection
      Layout.fillHeight: true
      Layout.fillWidth: true
      Layout.preferredWidth: 400
      model: Handlers.state.machinetalk.instanceModel
    }

    ColumnLayout {
      Layout.fillHeight: true

      CommissioningPanel {
        id: commissioningPanel
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.preferredWidth: 400
      }

      PreviewSettingsPanel {
        id: previewPanel
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.preferredWidth: 400
      }
    }

    UserSettingsPanel {
      id: userSettingsPanel
      Layout.fillHeight: true
      Layout.fillWidth: true
      Layout.preferredWidth: 400
    }

    ColumnLayout {
      Layout.fillHeight: true

      InterpreterPanel {
        id: interpreterPanel
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.preferredWidth: 400
      }

      ToolsPanel {
        id: toolsPanel
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.preferredWidth: 400
      }
    }

    HorizontalFiller {
    }
  }
}
