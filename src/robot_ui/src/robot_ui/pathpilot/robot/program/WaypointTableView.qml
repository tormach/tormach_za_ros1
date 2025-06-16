import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQml.Models
import Qt.labs.qmlmodels
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.robot.program
import pathpilot.models
import "."

PathPilotTableView {
  id: root
  property WaypointTableModel waypointsModel: null
  readonly property string currentUuid: d.uuidData ? d.uuidData : ""
  property string linearUnit: "m"
  property string angularUnit: "rad"
  model: sortFilterModel
  font.pixelSize: Fonts.waypointTableView.size1

  readonly property QtObject _d: QtObject {
    id: d
    readonly property var uuidData: root.model.data(root.model.index(root.currentRow, 0), WaypointTableModel.UuidRole)
    readonly property real valueFieldWidth: 100
    readonly property real userFrameFieldWidth: 120
    readonly property real typeFieldWidth: 80
    readonly property real warningFieldWidth: 20

    readonly property bool selectedIsPose: root.currentRow == -1 || root.model.data(root.model.index(root.currentRow, 0), WaypointTableModel.TargetTypeRole) == WaypointTableModel.Pose
  }

  function selectWaypointByName(name) {
    var model = root.model;
    for (var i = 0; i < root.rowCount; ++i) {
      var data = model.data(model.index(i, 0), WaypointTableModel.NameRole);
      if (data == name) {
        root.selectRow(i);
        return true;
      }
    }
    return false;
  }

  SortFilterProxyModel {
    id: sortFilterModel
    source: root.waypointsModel
    fields: [WaypointTableModel.NameRole, WaypointTableModel.TargetTypeRole, WaypointTableModel.XRole, WaypointTableModel.YRole, WaypointTableModel.ZRole, WaypointTableModel.ARole, WaypointTableModel.BRole, WaypointTableModel.CRole, WaypointTableModel.ConfigRole, WaypointTableModel.RevCountRole, WaypointTableModel.FrameRole]
    columnWidthOverrides: {
      "type": d.typeFieldWidth,
      "x": d.valueFieldWidth,
      "y": d.valueFieldWidth,
      "z": d.valueFieldWidth,
      "a": d.valueFieldWidth,
      "b": d.valueFieldWidth,
      "c": d.valueFieldWidth,
      "arm_config": d.valueFieldWidth,
      "rev_count": d.valueFieldWidth,
      "frame": d.userFrameFieldWidth
    }
    headerTitles: {
      "name": qsTr("Name"),
      "targetType": qsTr("Type"),
      "frame": qsTr("User Frame"),
      "x": d.selectedIsPose ? qsTr("X") : qsTr("J1"),
      "y": d.selectedIsPose ? qsTr("Y") : qsTr("J2"),
      "z": d.selectedIsPose ? qsTr("Z") : qsTr("J3"),
      "a": d.selectedIsPose ? qsTr("A") : qsTr("J4"),
      "b": d.selectedIsPose ? qsTr("B") : qsTr("J5"),
      "c": d.selectedIsPose ? qsTr("C") : qsTr("J6"),
      "arm_config": qsTr("Config"),
      "rev_count": qsTr("RevCount")
    }
  }

  delegate: DelegateChooser {
    role: "type"

    DelegateChoice {
      roleValue: "linear_number"
      PathPilotTableViewDelegateBase {
        id: item
        table: root

        PathPilotDroField {
          id: cell
          anchors.fill: parent
          readOnly: true
          decimals: Config.data.dro.decimals[Config.user.linearUnit]
          font.pixelSize: Fonts.waypointTableView.size1
          color: model.modified ? Colors.green3 : item.textColor
          background: Item {
          }

          Binding {
            target: cell
            property: "value"
            value: Units.fromTo(model.number, root.linearUnit, Config.user.linearUnit)
          }
        }
      }
    }

    DelegateChoice {
      roleValue: "angular_number"
      PathPilotTableViewDelegateBase {
        id: item
        table: root

        PathPilotDroField {
          id: cell
          anchors.fill: parent
          readOnly: true
          decimals: Config.data.dro.decimals[Config.user.angularUnit]
          font.pixelSize: Fonts.waypointTableView.size1
          color: model.modified ? Colors.green3 : item.textColor
          background: Item {
          }

          Binding {
            target: cell
            property: "value"
            value: Units.fromTo(model.number, root.angularUnit, Config.user.angularUnit)
          }
        }
      }
    }

    DelegateChoice {
      roleValue: "targetType"
      PathPilotTableViewDelegateBase {
        id: item
        table: root

        Text {
          id: cell
          anchors.fill: parent
          text: (model.targetType == WaypointTableModel.Pose) ? qsTr("Pose") : qsTr("Joints")
          font.pixelSize: Fonts.waypointTableView.size1
          verticalAlignment: Text.AlignVCenter
          color: model.modified ? Colors.green3 : item.textColor
        }
      }
    }

    DelegateChoice {
      roleValue: "warning"
      PathPilotTableViewDelegateBase {
        id: item
        table: root

        WarningIndicator {
          id: warningIndicator
          anchors.centerIn: parent
          warnings: model.warning
        }
      }
    }

    DelegateChoice {
      PathPilotTableViewDelegateBase {
        id: item
        table: root

        Text {
          anchors.fill: parent
          anchors.leftMargin: Sizes.singleMargin
          anchors.rightMargin: Sizes.singleMargin
          font: root.font
          verticalAlignment: Text.AlignVCenter
          text: model.display ?? ""
          elide: Text.ElideRight
          color: item.textColor
        }
      }
    }
  }
}
