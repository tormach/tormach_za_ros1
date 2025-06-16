import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers

PathPilotPanel {
  id: root

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleSpacing
    spacing: Sizes.doubleSpacing

    PathPilotLabel {
      text: qsTr("Units")
    }

    Spacer {
      Layout.fillWidth: true
    }

    GridLayout {
      columns: 2
      PathPilotLabel {
        text: qsTr("Linear Unit")
      }

      PathPilotComboBox {
        Layout.fillWidth: true
        model: Config.data.jog.linearUnits
        currentIndex: model.indexOf(Config.user.linearUnit)
        onActivated: function (index) {
          Config.user.linearUnit = model[index];
        }
      }

      PathPilotLabel {
        text: qsTr("Angular Unit")
      }

      PathPilotComboBox {
        Layout.fillWidth: true
        model: Config.data.jog.angularUnits
        currentIndex: model.indexOf(Config.user.angularUnit)
        onActivated: function (index) {
          Config.user.angularUnit = model[index];
        }
      }

      PathPilotLabel {
        text: qsTr("Time Unit")
      }

      PathPilotComboBox {
        Layout.fillWidth: true
        model: Config.data.jog.timeUnits
        currentIndex: model.indexOf(Config.user.timeUnit)
        onActivated: function (index) {
          Config.user.timeUnit = model[index];
        }
      }
    }

    Spacer {
      Layout.fillWidth: true
    }

    PathPilotLabel {
      text: qsTr("Code Editor")
    }

    Spacer {
      Layout.fillWidth: true
    }

    PathPilotTextField {
      Layout.fillWidth: true
      horizontalAlignment: Text.AlignLeft
      text: Config.user.codeEditor
      onEditingFinished: Config.user.codeEditor = text

      PathPilotToolTip {
        itemId: "msg_code_editor_name_inpute"
      }
    }

    Spacer {
      Layout.fillWidth: true
    }

    PathPilotToggleButton {
      id: probePolarityButton
      Layout.fillWidth: true
      text: qsTr("Probe Setting")
      propertyText1: qsTr("Active")
      propertyText2: qsTr("Passive")
      enabled: Handlers.state.probePolarity.allowed
      checked: Config.user.probe.passive
      onClicked: {
        Config.user.probe.passive = checked;
        Handlers.state.probePolarity.setProbePolarity(Config.user.probe.passive);
      }

      PathPilotToolTip {
        itemId: "msg_probe_setting_toggle"
      }
    }

    Spacer {
      Layout.fillWidth: true
    }

    PathPilotLabel {
      text: qsTr("Conversational")
    }

    Spacer {
      Layout.fillWidth: true
    }

    PathPilotCheckBox {
      Layout.fillWidth: true
      text: qsTr("Enable Main Loop Warning")
      checked: Config.user.conversational.mainLoopWarningEnabled

      onClicked: Config.user.conversational.mainLoopWarningEnabled = checked

      PathPilotToolTip {
        itemId: "msg_enable_main_loop_warning"
      }
    }

    Spacer {
      Layout.fillWidth: true
    }

    VerticalFiller {
    }
  }
}
