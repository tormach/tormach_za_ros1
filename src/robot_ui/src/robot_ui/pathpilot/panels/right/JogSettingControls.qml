import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers

ColumnLayout {
  id: root
  readonly property var linearSteps: Handlers.jog.incremental.linearSteps
  readonly property var angularSteps: Handlers.jog.incremental.angularSteps

  RowLayout {
    id: buttonLayout

    Layout.fillWidth: true
    PathPilotLabel {
      text: qsTr("Step:")
    }

    Repeater {
      model: root.linearSteps

      PathPilotButtonWithLed {
        Layout.fillWidth: true
        Layout.preferredHeight: 50
        font.pixelSize: Fonts.jogControls.size1
        labelMargin: 0
        text: root.linearSteps[index] + "\n" + root.angularSteps[index]
        checkable: true
        checked: index === Config.user.jog.stepSize
        onClicked: {
          Config.user.jog.stepSize = index;
          Config.user.jog.continuous = false;
        }

        PathPilotToolTip {
          itemId: "jog_step_size_" + (root.linearSteps[index]).toLowerCase()
          sidePosition: PathPilotToolTip.Side.Left
        }
      }
    }
  }

  ButtonGroup {
    buttons: buttonLayout.children
    exclusive: true
  }

  GridLayout {
    Layout.fillWidth: true
    columns: 3

    PathPilotSlider {
      id: jograteSlider
      Layout.fillWidth: true
      Layout.rowSpan: 2
      from: 0.0
      to: 1.0
      stepSize: 0.01

      onValueChanged: {
        jograteUpdateTimer.stop();
        jograteUpdateTimer.start();
      }

      Binding {
        target: jograteSlider
        property: "value"
        value: Config.user.jograte
      }

      Timer {
        id: jograteUpdateTimer
        interval: 20
        onTriggered: {
          Config.user.jograte = jograteSlider.value;
        }
      }

      PathPilotToolTip {
        itemId: "jograte_slider"
        sidePosition: PathPilotToolTip.Side.Left
      }

      Timer {
        id: decreaseTimer
        interval: 50
        repeat: true
        running: decreaseShortcut.keyPressed
        onTriggered: jograteSlider.decrease()
      }

      Timer {
        id: increaseTimer
        interval: 50
        repeat: true
        running: increaseShortcut.keyPressed
        onTriggered: jograteSlider.increase()
      }

      GlobalShortcut {
        id: decreaseShortcut
        globalShortcuts: GlobalShortcuts
        key: Qt.Key_Q
        enabled: Handlers.app.activePanel == Panels.JogPanel
      }

      GlobalShortcut {
        id: increaseShortcut
        globalShortcuts: GlobalShortcuts
        key: Qt.Key_W
        enabled: Handlers.app.activePanel == Panels.JogPanel
      }
    }

    PathPilotToggleButton {
      id: contStepButton
      implicitWidth: 90
      text: qsTr("Jog")
      propertyText1: qsTr("Cont")
      propertyText2: qsTr("Step")
      checked: !Config.user.jog.continuous
      onClicked: {
        Config.user.jog.continuous = !checked;
        if (Config.user.jog.continuous) {
          Config.user.jog.stepSize = -1;
        } else {
          Config.user.jog.stepSize = 1;
        }
      }

      PathPilotToolTip {
        itemId: "jog_type_switch"
        sidePosition: PathPilotToolTip.Side.Left
      }
    }

    PathPilotToggleButton {
      id: toolWorldButton
      implicitWidth: 120
      text: qsTr("Frame")
      propertyText1: qsTr("User")
      propertyText2: qsTr("Tool")
      checked: Config.user.jog.toolFrame
      onClicked: Config.user.jog.toolFrame = checked

      PathPilotToolTip {
        itemId: "msg_frame_user_or_tool_toggle"
        sidePosition: PathPilotToolTip.Side.Left
      }
    }

    PathPilotButtonWithLed {
      id: jogIgnoreProbe
      Layout.columnSpan: 2
      Layout.fillWidth: true
      implicitWidth: 210
      text: qsTr("Jog Ignore Probe")
      checked: Config.user.jog.ignoreprobe
      onClicked: {
        Config.user.jog.ignoreprobe = !Config.user.jog.ignoreprobe;
        if (Config.user.jog.ignoreprobe) {
          Config.user.jog.continuous = false;
        }
      }

      PathPilotToolTip {
        itemId: "msg_jog_ignore_probe"
        sidePosition: PathPilotToolTip.Side.Left
      }
    }
  }
}
