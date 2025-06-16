import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.handlers
import pathpilot.logging

PathPilotPanel {
  id: root

  GlobalShortcut {
    globalShortcuts: GlobalShortcuts
    key: Qt.Key_Space
    enabled: Handlers.program.programRunning

    onKeyPressedChanged: {
      if (keyPressed) {
        feedholdButton.clicked();
      }
    }
  }

  GlobalShortcut {
    globalShortcuts: GlobalShortcuts
    key: Qt.Key_Escape
    enabled: Handlers.program.programRunning

    onKeyPressedChanged: {
      if (keyPressed) {
        stopButton.clicked();
      }
    }
  }

  ColumnLayout {
    id: columnLayout1
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
    spacing: Sizes.singleSpacing

    CycleStartButton {
      id: cycleStartButton
      Layout.fillWidth: true
      paused: (Handlers.program.interpreterState === ProgramInterpreter.PausedState || Handlers.program.interpreterState === ProgramInterpreter.PausedActiveState)
      running: Handlers.program.interpreterState === ProgramInterpreter.RunningState
      onClicked: {
        if (running) {
          return;
        }
        if (!Handlers.state.driveStart.inEffect) {
          Logging.log(qsTr("Robot must be powered on before starting a program."), LogLevel.Warn);
          return;
        }
        if (Handlers.app.activePanel !== Panels.MainPanel) {
          Logging.log(qsTr("Cannot start program while not on Main screen"), LogLevel.Warn);
          return;
        }
        if (singleBlockButton.checked) {
          Handlers.conversational.commitChanges(Handlers.program.stepProgram, qsTr("executing single step"));
        } else if (Handlers.program.interpreterState === ProgramInterpreter.StoppedState) {
          Handlers.conversational.commitChanges(Handlers.program.startProgram, qsTr("starting program"));
        } else {
          Handlers.program.continueProgram();
        }
      }
      PathPilotToolTip {
        itemId: "cycle_start"
      }
    }

    GridLayout {
      id: rowLayout2
      Layout.fillWidth: true
      columns: 2
      rowSpacing: Sizes.singleSpacing
      columnSpacing: Sizes.singleSpacing

      PathPilotButtonWithLed {
        id: singleBlockButton
        Layout.fillWidth: true
        text: qsTr("Single block")
        font.pixelSize: Fonts.leftPanel.size2
        bigLed: true
        checkable: true
        enabled: Handlers.program.stepProgramAllowed || Handlers.program.pauseProgramAllowed
        onClicked: {
          if (Handlers.program.interpreterState === ProgramInterpreter.RunningState) {
            if (checked) {
              Handlers.program.pauseProgram();
            } else {
              Handlers.program.continueProgram();
            }
          }
        }
        PathPilotToolTip {
          itemId: "single_block"
        }
      }

      PathPilotButtonWithLed {
        id: optionalStopButton
        Layout.fillWidth: true
        text: qsTr("Optional Pause")
        font.pixelSize: Fonts.leftPanel.size2
        bigLed: true
        checked: Config.user.optionalStop
        onClicked: Config.user.optionalStop = !Config.user.optionalStop
        PathPilotToolTip {
          itemId: "optional_pause"
        }
      }

      PathPilotButtonWithLed {
        id: feedholdButton
        Layout.fillWidth: true
        text: qsTr("Feedhold")
        font.pixelSize: Fonts.leftPanel.size2
        bigLed: true
        checkable: false
        checked: Handlers.program.interpreterState === ProgramInterpreter.PausedState
        onClicked: {
          if (Handlers.program.pauseProgramAllowed) {
            Handlers.program.pauseProgram();
          }
        }
        PathPilotToolTip {
          itemId: "feedhold"
        }
      }

      PathPilotButton {
        id: stopButton
        Layout.fillWidth: true
        text: qsTr("Stop")
        font.pixelSize: Fonts.leftPanel.size2
        onClicked: Handlers.program.stopProgram()
        PathPilotToolTip {
          itemId: "stop"
        }
      }

      PathPilotButtonWithLed {
        Layout.fillWidth: true
        enabled: Handlers.app.dryRunSwitchAllowed
        text: qsTr("Dry Run")
        checked: Config.user.dryRunMode
        onClicked: {
          Config.user.dryRunMode = !Config.user.dryRunMode;
        }
        PathPilotToolTip {
          itemId: "dry_run"
        }
      }

      PathPilotButton {
        id: resetButton
        Layout.fillWidth: true
        text: qsTr("Reset")
        font.pixelSize: Fonts.leftPanel.size2
        blinkEnabled: true
        blinkColor: Handlers.program.programError ? Colors.red1 : Colors.blue3
        blink: Handlers.program.programError || !Handlers.state.driveStart.inEffect

        onClicked: {
          Handlers.program.stopProgram();
          Handlers.state.driveStart.effectCmd();
        }

        PathPilotToolTip {
          itemId: "reset"
        }
      }
    }

    RowLayout {
      Layout.fillWidth: true
      readonly property bool hovered: maximumVelocityScaleSlider.hovered || feedPathPilotButton.hovered

      MaximumVelocityScaleSlider {
        id: maximumVelocityScaleSlider
      }

      PathPilotButton {
        id: feedPathPilotButton
        Layout.preferredWidth: 45
        text: qsTr("MAX\nVEL\n100%")
        font.pixelSize: Fonts.leftPanel.size3
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        onClicked: maximumVelocityScaleSlider.update(Math.min(1.0, Config.machine.maxVelocityLimits.safetyInput))
      }

      PathPilotToolTip {
        itemId: "uniform_velocity_slider"
      }
    }

    RowLayout {
      Layout.fillWidth: true
      readonly property bool hovered: uniformVelocityScaleSlider.hovered || maxvelPathPilotButton.hovered

      UniformVelocityScaleSlider {
        id: uniformVelocityScaleSlider
      }

      PathPilotButton {
        id: maxvelPathPilotButton
        Layout.preferredWidth: 45
        text: qsTr("VEL\nSCALE\n100%")
        font.pixelSize: Fonts.leftPanel.size3
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        onClicked: uniformVelocityScaleSlider.update(1.0)
      }

      PathPilotToolTip {
        itemId: "feedrate_override_slider"
      }
    }

    Item {
      Layout.fillHeight: true
      Layout.fillWidth: true
    }
  }
}
