import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.jog
import pathpilot.handlers

ColumnLayout {
  id: root
  property double linearVelocity: Config.data.jog.linearVelocity * Config.user.jograte
  property double angularVelocity: Config.data.jog.angularVelocity * Config.user.jograte

  QtObject {
    id: d
    readonly property QtObject jog: Handlers.jog.incremental

    function buttonPressed(axis, pressed, stepSize) {
      var frameId = Config.user.jog.toolFrame ? Config.data.preview.toolFrame : "";
      var frameId = Config.user.jog.toolFrame ? Handlers.state.toolFrames.activeFrameFrame : "";
      if (pressed) {
        if (Config.user.jog.continuous) {
          d.jog.cartesian.continuous(axis, stepSize, frameId);
        } else {
          d.jog.cartesian.step(axis, stepSize, frameId);
        }
      } else {
        d.jog.stop();
      }
    }
  }

  RowLayout {
    PathPilotLabel {
      text: qsTr("Move Tool")
      font.pixelSize: Fonts.jogPanel.size1
    }

    HorizontalFiller {
    }

    JogWarningIndicator {
    }
  }

  Spacer {
    Layout.fillWidth: true
  }

  RowLayout {
    spacing: Sizes.doubleSpacing

    SingleAxisJoyStick {
      id: joyStickA
      Layout.fillHeight: true
      Layout.fillWidth: true
      axisName: qsTr("A")
      minusActiveExternal: keyboardJogInput.aMinusPressed
      plusActiveExternal: keyboardJogInput.aPlusPressed

      onMinusPressedChanged: d.buttonPressed("a", minusPressed, -d.jog.angularStepSize)
      onPlusPressedChanged: d.buttonPressed("a", plusPressed, d.jog.angularStepSize)
    }

    SingleAxisJoyStick {
      id: joyStickB
      Layout.fillHeight: true
      Layout.fillWidth: true
      axisName: qsTr("B")
      minusActiveExternal: keyboardJogInput.bMinusPressed
      plusActiveExternal: keyboardJogInput.bPlusPressed

      onMinusPressedChanged: d.buttonPressed("b", minusPressed, -d.jog.angularStepSize)
      onPlusPressedChanged: d.buttonPressed("b", plusPressed, d.jog.angularStepSize)
    }

    SingleAxisJoyStick {
      id: joyStickC
      Layout.fillHeight: true
      Layout.fillWidth: true
      axisName: qsTr("C")
      minusActiveExternal: keyboardJogInput.cMinusPressed
      plusActiveExternal: keyboardJogInput.cPlusPressed

      onMinusPressedChanged: d.buttonPressed("c", minusPressed, -d.jog.angularStepSize)
      onPlusPressedChanged: d.buttonPressed("c", plusPressed, d.jog.angularStepSize)
    }
  }

  Item {
    implicitHeight: Sizes.singleSpacing
  }

  RowLayout {
    spacing: Sizes.singleSpacing

    TwoAxesJoyStick {
      id: joyStickXY
      Layout.fillHeight: true
      Layout.preferredWidth: height
      axis1Name: qsTr("X")
      axis2Name: qsTr("Y")
      axis1MinusActiveExternal: keyboardJogInput.xMinusPressed
      axis1PlusActiveExternal: keyboardJogInput.xPlusPressed
      axis2MinusActiveExternal: keyboardJogInput.yMinusPressed
      axis2PlusActiveExternal: keyboardJogInput.yPlusPressed

      onAxis1MinusPressedChanged: d.buttonPressed("x", axis1MinusPressed, -d.jog.linearStepSize)
      onAxis1PlusPressedChanged: d.buttonPressed("x", axis1PlusPressed, d.jog.linearStepSize)
      onAxis2MinusPressedChanged: d.buttonPressed("y", axis2MinusPressed, -d.jog.linearStepSize)
      onAxis2PlusPressedChanged: d.buttonPressed("y", axis2PlusPressed, d.jog.linearStepSize)

      PathPilotIconButton {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        icon_: Icons.jogpanel.keyboard
        onClicked: shortcutsPopup.open()
      }
    }

    SingleAxisJoyStick {
      id: joyStickZ
      Layout.fillHeight: true
      Layout.fillWidth: true
      axisName: qsTr("Z")
      minusActiveExternal: keyboardJogInput.zMinusPressed
      plusActiveExternal: keyboardJogInput.zPlusPressed

      onMinusPressedChanged: d.buttonPressed("z", minusPressed, -d.jog.linearStepSize)
      onPlusPressedChanged: d.buttonPressed("z", plusPressed, d.jog.linearStepSize)
    }
  }

  CartesianJogKeyboardInput {
    id: keyboardJogInput
    globalShortcuts: GlobalShortcuts
    enabled: parent.visible

    onToggleContinuousTriggered: Config.user.jog.continuous = !Config.user.jog.continuous
    onToggleFrameTriggered: Config.user.jog.toolFrame = !Config.user.jog.toolFrame
    onToggleStepSizeTriggered: {
      if (Config.user.jog.stepSize == Handlers.jog.incremental.linearSteps.length - 1) {
        Config.user.jog.stepSize = 0;
      } else {
        Config.user.jog.stepSize += 1;
      }
    }
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "xPlusActive"
    value: joyStickXY.axis1PlusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "xMinusActive"
    value: joyStickXY.axis1MinusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "yPlusActive"
    value: joyStickXY.axis2PlusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "yMinusActive"
    value: joyStickXY.axis2MinusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "zPlusActive"
    value: joyStickZ.plusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "zMinusActive"
    value: joyStickZ.minusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "aPlusActive"
    value: joyStickA.plusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "aMinusActive"
    value: joyStickA.minusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "bPlusActive"
    value: joyStickB.plusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "bMinusActive"
    value: joyStickB.minusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "cPlusActive"
    value: joyStickC.plusHovered
  }

  Binding {
    target: Handlers.jog.jogMarkers
    property: "cMinusActive"
    value: joyStickC.minusHovered
  }

  //  Binding {
  //    target: Handlers.jog.continuous.cartesian
  //    property: "x"
  //    value: (joyStickXY.axis1MinusPressed * -1 + joyStickXY.axis1PlusPressed) * root.linearVelocity
  //    when: Config.user.jog.continuous
  //  }
  //  Binding {
  //    target: Handlers.jog.continuous.cartesian
  //    property: "y"
  //    value: (joyStickXY.axis2MinusPressed * -1 + joyStickXY.axis2PlusPressed) * root.linearVelocity
  //    when: Config.user.jog.continuous
  //  }
  //  Binding {
  //    target: Handlers.jog.continuous.cartesian
  //    property: "z"
  //    value: (joyStickZ.minusPressed * -1 + joyStickZ.plusPressed) * root.linearVelocity
  //    when: Config.user.jog.continuous
  //  }
  //  Binding {
  //    target: Handlers.jog.continuous.cartesian
  //    property: "rx"
  //    value: (joyStickA.minusPressed * -1 + joyStickA.plusPressed) * root.angularVelocity
  //    when: Config.user.jog.continuous
  //  }
  //  Binding {
  //    target: Handlers.jog.continuous.cartesian
  //    property: "ry"
  //    value: (joyStickB.minusPressed * -1 + joyStickB.plusPressed) * root.angularVelocity
  //    when: Config.user.jog.continuous
  //  }
  //  Binding {
  //    target: Handlers.jog.continuous.cartesian
  //    property: "rz"
  //    value: (joyStickC.minusPressed * -1 + joyStickC.plusPressed) * root.angularVelocity
  //    when: Config.user.jog.continuous
  //  }
  Connections {
    target: Handlers.jog.continuous.cartesian
    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onActiveChanged(active) {
      Handlers.app.lockPanel(active);
    }
  }

  KeyboardShortcutsPopup {
    id: shortcutsPopup
  }
}
