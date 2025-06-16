import QtQuick
import QtQuick.Controls
import Qt.labs.qmlmodels
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.models
import pathpilot.robot.machinetalk

PathPilotTableView {
  id: root
  property MachinetalkNodeTableModel nodeModel: null
  model: sortFilterModel
  font.pixelSize: Fonts.frameTableView.size1

  readonly property QtObject _d: QtObject {
    id: d
    readonly property real valueFieldWidth: 130
    readonly property real nameFieldWidth: 200

    function setPoseAxis(name, uuid, pose, axisIndex, value) {
      root.selection.clear();
      pose[axisIndex] = value;
      root.nodeModel.updateNode(name, uuid, pose);
    }
  }

  SortFilterProxyModel {
    id: sortFilterModel
    source: root.nodeModel
    fields: [MachinetalkNodeTableModel.NameRole, MachinetalkNodeTableModel.XRole, MachinetalkNodeTableModel.YRole, MachinetalkNodeTableModel.ZRole, MachinetalkNodeTableModel.ARole, MachinetalkNodeTableModel.BRole, MachinetalkNodeTableModel.CRole]
    columnWidthOverrides: {
      "name": d.nameFieldWidth,
      "x": d.valueFieldWidth,
      "y": d.valueFieldWidth,
      "z": d.valueFieldWidth,
      "a": d.valueFieldWidth,
      "b": d.valueFieldWidth,
      "c": d.valueFieldWidth
    }
    headerTitles: {
      "name": qsTr("Name")
    }
  }

  delegate: DelegateChooser {
    role: "type"

    DelegateChoice {
      roleValue: "linear_number"
      PathPilotTableViewDelegateBase {
        id: item
        table: root
        onClicked: droField.forceActiveFocus()

        PathPilotDroField {
          id: droField
          anchors.fill: parent

          Binding {
            target: droField
            property: "value"
            value: Units.fromRos(Number(model.number), Config.user.linearUnit)
          }
          color: error ? Colors.red1 : item.textColor
          background: Item {
          }

          onValueUpdated: function (value) {
            d.setPoseAxis(model.name, model.uuid, model.pose, model.axis, Units.toRos(value, Config.user.linearUnit));
          }
        }
      }
    }

    DelegateChoice {
      roleValue: "angular_number"
      PathPilotTableViewDelegateBase {
        id: item
        table: root
        onClicked: droField.forceActiveFocus()

        PathPilotDroField {
          id: droField
          anchors.fill: parent

          Binding {
            target: droField
            property: "value"
            value: Units.fromRos(Number(model.number), Config.user.angularUnit)
          }
          color: error ? Colors.red1 : item.textColor
          background: Item {
          }

          onValueUpdated: function (value) {
            d.setPoseAxis(model.name, model.uuid, model.pose, model.axis, Units.toRos(value, Config.user.angularUnit));
          }
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
          text: model.display
          elide: Text.ElideRight
          color: item.textColor
        }
      }
    }
  }
}
