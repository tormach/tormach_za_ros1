import QtQuick
import QtQuick.Controls
import QtQuick.Controls as C1
import QtQuick.Layouts
import QtQuick.Window
import QtQml.Models
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.robot.program.blocks
import pathpilot.development

UnscaledTestBase {
  id: root

  QtObject {
    id: d
    readonly property string programPath: DevelopmentPaths.programPath + "/test_program3.py"
    readonly property var uuidData: programModel.data(itemSelectionModel.currentIndex, ProgramTreeModel.UuidRole)
    readonly property string currentUuid: uuidData ? uuidData : ""
  }

  ProgramReader {
    id: reader
    path: d.programPath
  }

  ProgramManipulator {
    id: programManipulator
    sourceProgram: reader.program
  }

  ProgramTreeModel {
    id: programModel
    program: programManipulator.modifiedProgram
  }

  ItemSelectionModel {
    // Note: without the selection model, we get crashes on remove
    id: itemSelectionModel
    model: programModel
  }

  ProgramInterpreter {
    id: interpreter
    onCommandError: console.log("Error: " + message)
  }

  BlockData {
    id: blockData
    uuid: d.currentUuid
    program: programModel.program
  }

  MoveBlockData {
    id: movelBlockData
    uuid: d.currentUuid
    program: programModel.program
  }

  CodeGenerator {
    id: codeGenerator
    robotProgram: programManipulator.modifiedProgram
    autoUpdate: true
  }

  ProgramPositionSync {
    id: programPositionSync
    programModel: programModel
    selectionModel: itemSelectionModel
  }

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleMargin

    ColumnLayout {
      Layout.fillHeight: true
      Layout.fillWidth: true

      ProgramTreeView {
        id: view
        Layout.fillHeight: true
        Layout.fillWidth: true
        model: programModel
        selection: itemSelectionModel

        onDragAndDropCompleted: {
          programManipulator.moveBlock(sourceUuid, targetUuid);
        }
      }
      RowLayout {
        Layout.preferredWidth: 250

        Button {
          text: qsTr("Remove")
          enabled: view.currentIndex.valid && blockData.level > 1
          onClicked: {
            programManipulator.removeBlock(blockData.uuid);
            itemSelectionModel.clear();
          }
        }

        Button {
          text: qsTr("Move Up")
          enabled: view.currentIndex.valid && (blockData.level > 1) && (blockData.previousUuid !== "")
          onClicked: programManipulator.moveBlock(blockData.uuid, blockData.previousUuid)
        }

        Button {
          text: qsTr("Move Down")
          enabled: view.currentIndex.valid && (blockData.level > 1) && (blockData.nextUuid !== "")
          onClicked: programManipulator.moveBlock(blockData.nextUuid, blockData.uuid)
        }

        Button {
          id: undoButton
          enabled: programManipulator.undoPossible
          text: qsTr("Undo")
          onClicked: programManipulator.undo()
        }

        Button {
          id: redoButton
          enabled: programManipulator.redoPossible
          text: qsTr("Redo")
          onClicked: programManipulator.redo()
        }

        Button {
          id: resetHistoryButton
          text: qsTr("Reset")
          onClicked: programManipulator.resetHistory()
        }
      }
    }

    ColumnLayout {
      Layout.fillHeight: true
      Layout.preferredWidth: 200

      Text {
        id: text
        text: qsTr("Type: ") + (blockData.type != "" ? blockData.type : "undefined")
      }

      Text {
        text: qsTr("Level: ") + blockData.level
      }

      Text {
        id: startPos
        text: 'Start: ' + JSON.stringify(blockData.startPos) + '\nEnd: ' + JSON.stringify(blockData.endPos)
      }

      Text {
        text: qsTr("Code: ") + (blockData.code != "" ? blockData.code : "undefined")
      }

      TextEdit {
        text: qsTr("Program:\n") + codeGenerator.code
      }

      Text {
        text: qsTr("MoveL Block")
        visible: movelBlockData.valid
      }

      TextEdit {
        id: movelPoseEdit
        Layout.fillWidth: true
        visible: movelBlockData.valid
        text: JSON.stringify(movelBlockData.waypoint)
      }

      TextEdit {
        id: movelTitleEdit
        Layout.fillWidth: true
        visible: movelBlockData.valid
        text: movelBlockData.title
      }

      RowLayout {
        Button {
          text: qsTr("Update")
          enabled: movelBlockData.valid
          onClicked: {
            programManipulator.updateBlock(blockData.uuid, {
                "waypoint": JSON.parse(movelPoseEdit.text),
                "title": movelTitleEdit.text
              });
          }
        }

        Button {
          text: qsTr("Add MoveL")
          enabled: view.currentIndex.valid && blockData.level > 1
          onClicked: {
            programManipulator.beginGroup();
            var uuid = programManipulator.createBlock(blockData.uuid, "movel");
            programManipulator.updateBlock(uuid, {
                "waypoint": JSON.parse(movelPoseEdit.text),
                "title": movelTitleEdit.text
              });
            programManipulator.endGroup();
            itemSelectionModel.clear();
          }
        }
      }

      Text {
        text: qsTr("Interpreter:")
        font.bold: true
      }

      Text {
        text: qsTr("State: %1").arg(getStateText(interpreter.interpreterState))

        function getStateText(state) {
          switch (state) {
          case ProgramInterpreter.UndefinedState:
            return qsTr("Undefined");
          case ProgramInterpreter.IdleState:
            return qsTr("Idle");
          case ProgramInterpreter.StoppedState:
            return qsTr("Stopped");
          case ProgramInterpreter.RunningState:
            return qsTr("Running");
          case ProgramInterpreter.PausedState:
            return qsTr("Paused");
          default:
            return "";
          }
        }
      }

      RowLayout {
        Button {
          text: qsTr("Load")
          enabled: (interpreter.interpreterState === ProgramInterpreter.StoppedState) || (interpreter.interpreterState === ProgramInterpreter.IdleState)
          onClicked: interpreter.loadProgram(d.programPath)
        }
        Button {
          text: qsTr("Run")
          enabled: interpreter.interpreterState === ProgramInterpreter.StoppedState
          onClicked: interpreter.startProgram()
        }
        Button {
          text: qsTr("Stop")
          enabled: (interpreter.interpreterState === ProgramInterpreter.RunningState) || (interpreter.interpreterState === ProgramInterpreter.PausedState)
          onClicked: interpreter.stopProgram()
        }
      }

      RowLayout {
        Button {
          text: qsTr("Step")
          enabled: (interpreter.interpreterState === ProgramInterpreter.PausedState) || (interpreter.interpreterState === ProgramInterpreter.StoppedState)
          onClicked: interpreter.stepProgram()
        }
        Button {
          text: qsTr("Pause")
          enabled: interpreter.interpreterState === ProgramInterpreter.RunningState
          onClicked: interpreter.pauseProgram()
        }
        Button {
          text: qsTr("Continue")
          enabled: interpreter.interpreterState === ProgramInterpreter.PausedState
          onClicked: interpreter.continueProgram()
        }
      }

      RowLayout {
        TextField {
          id: mdiCommandEdit
          Layout.fillWidth: true
          enabled: (interpreter.interpreterState === ProgramInterpreter.StoppedState) || (interpreter.interpreterState === ProgramInterpreter.IdleState)
        }
        Button {
          text: qsTr("Run")
          enabled: mdiCommandEdit.enabled
          onClicked: {
            interpreter.executeMDI(mdiCommandEdit.text);
          }
        }
      }

      Item {
        Layout.fillHeight: true
      }
    }
  }
}
