import QtQuick
import QtQuick.Controls
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
    readonly property string programPath: DevelopmentPaths.programPath + "/example_program4.py"
  }

  ProgramReader {
    id: reader
    path: d.programPath
  }

  GlobalWaypoints {
    id: globalWaypoints
    Component.onCompleted: globalWaypoints.readFromStore()
  }

  GlobalWaypointsManipulator {
    id: waypointsManipulator
    sourceWaypoints: globalWaypoints
  }

  ProgramManipulator {
    id: programManipulator
    sourceProgram: reader.program
  }

  WaypointsListModel {
    id: waypointsModel
    source: waypointsManipulator.modifiedWaypoints
  }

  WaypointData {
    id: waypointData
    uuid: view.currentUuid
    source: waypointsManipulator.modifiedWaypoints
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
          checked: waypointData.targetType == WaypointsListModel.Pose
        }

        RadioButton {
          id: jointsRadio
          text: qsTr("Joints")
          checked: waypointData.targetType == WaypointsListModel.Joints
        }

        VerticalFiller {
        }
      }
    }

    RowLayout {
      PathPilotButton {
        text: qsTr("Add")
        onClicked: {
          waypointsManipulator.addWaypoint({
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
              var uuid = view.model.data(index, WaypointsListModel.UuidRole);
              uuids.push(uuid);
            });
          view.selection.clear();
          for (var i = 0; i < uuids.length; ++i) {
            waypointsManipulator.removeWaypoint(uuids[i]);
          }
        }
      }
      PathPilotButton {
        text: qsTr("Update")
        enabled: view.selection.count == 1
        onClicked: {
          var targetType = poseRadio.checked ? WaypointData.Pose : WaypointData.Joints;
          waypointsManipulator.updateWaypoint(waypointData.uuid, {
              "name": nameInput.text,
              "target": JSON.parse(targetInput.text),
              "target_type": poseRadio.checked ? WaypointData.Pose : WaypointData.Joints
            });
        }
      }

      PathPilotButton {
        text: qsTr("Undo")
        enabled: waypointsManipulator.undoPossible
        onClicked: {
          view.selection.clear();
          waypointsManipulator.undo();
        }
      }

      PathPilotButton {
        text: qsTr("Redo")
        enabled: waypointsManipulator.redoPossible
        onClicked: {
          view.selection.clear();
          waypointsManipulator.redo();
        }
      }

      PathPilotButton {
        text: qsTr("Save")
        enabled: waypointsManipulator.undoPossible
        onClicked: {
          waypointsManipulator.modifiedWaypoints.writeToStore();
          globalWaypoints.readFromStore();
        }
      }

      PathPilotButton {
        text: qsTr("Load")
        onClicked: globalWaypoints.readFromStore()
      }
    }
  }
}
