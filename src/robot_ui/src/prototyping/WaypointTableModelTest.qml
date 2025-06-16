import QtQuick
import QtQuick.Controls
import QtQuick.Controls as C1
import QtQuick.Layouts
import QtQuick.Window
import QtQml.Models
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.models
import pathpilot.development

UnscaledTestBase {
  id: root

  QtObject {
    id: d
    readonly property string programPath: DevelopmentPaths.programPath + "/test_program4.py"
  }

  ProgramReader {
    id: reader
    path: d.programPath
  }

  ProgramManipulator {
    id: programManipulator
    sourceProgram: reader.program
  }

  WaypointTableModel {
    id: waypointsModel
    source: programManipulator.modifiedProgram
  }

  WaypointData {
    id: waypointData
    uuid: view.currentUuid
    source: programManipulator.modifiedProgram
  }

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleMargin

    RowLayout {
      WaypointTableView {
        id: view
        Layout.fillWidth: true
        Layout.fillHeight: true

        waypointsModel: waypointsModel
      }
      ColumnLayout {
        Layout.fillWidth: false
        PathPilotLabel {
          text: qsTr("Name:")
        }

        PathPilotTextField {
          id: nameInput
          Layout.fillWidth: true
          text: waypointData.name
        }

        PathPilotLabel {
          text: qsTr("Target:")
        }

        PathPilotTextField {
          id: targetInput
          Layout.fillWidth: true
          implicitWidth: 300
          text: "[" + waypointData.target + "]"
        }

        PathPilotLabel {
          text: qsTr("Type:")
        }

        RadioButton {
          id: poseRadio
          text: qsTr("Pose")
          checked: waypointData.targetType == WaypointTableModel.Pose
        }

        RadioButton {
          id: jointsRadio
          text: qsTr("Joints")
          checked: waypointData.targetType == WaypointTableModel.Joints
        }

        VerticalFiller {
        }
      }
    }

    RowLayout {
      PathPilotButton {
        text: qsTr("Add")
        onClicked: {
          programManipulator.addWaypoint({
              "name": nameInput.text,
              "target": JSON.parse(targetInput.text),
              "target_type": poseRadio.checked ? WaypointData.Pose : WaypointData.Joints
            });
        }
      }
      PathPilotButton {
        text: qsTr("Remove")
        enabled: view.selection.count > 0
        onClicked: {
          var uuids = [];
          view.selection.forEach(function (rowIndex) {
              var index = view.model.index(rowIndex, 0);
              var uuid = view.model.data(index, WaypointTableModel.UuidRole);
              uuids.push(uuid);
            });
          view.selection.clear();
          for (var i = 0; i < uuids.length; ++i) {
            programManipulator.removeWaypoint(uuids[i]);
          }
        }
      }
      PathPilotButton {
        text: qsTr("Update")
        enabled: view.selection.count == 1
        onClicked: {
          var targetType = poseRadio.checked ? WaypointData.Pose : WaypointData.Joints;
          programManipulator.updateWaypoint(waypointData.uuid, {
              "name": nameInput.text,
              "target": JSON.parse(targetInput.text),
              "target_type": poseRadio.checked ? WaypointData.Pose : WaypointData.Joints
            });
        }
      }

      PathPilotButton {
        text: qsTr("Undo")
        enabled: programManipulator.undoPossible
        onClicked: {
          view.selection.clear();
          programManipulator.undo();
        }
      }

      PathPilotButton {
        text: qsTr("Redo")
        enabled: programManipulator.redoPossible
        onClicked: {
          view.selection.clear();
          programManipulator.redo();
        }
      }
    }
  }
}
