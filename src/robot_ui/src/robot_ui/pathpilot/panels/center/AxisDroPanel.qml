import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.handlers

Item {
  id: root
  property var axisNames: Config.data.axisNames
  property var axisPosition: Handlers.state.cartesianState.pose.axisPositions
  property bool readOnly: false

  signal touchOff(int axis, double position)
  signal reset(int axis)

  QtObject {
    id: d
    readonly property int axes: root.axisNames.length
  }

  ColumnLayout {
    id: container
    anchors.fill: parent
    Repeater {
      model: d.axes

      AxisPositionControl {
        id: control
        readonly property string unitType: index > 2 ? Config.user.angularUnit : Config.user.linearUnit
        Layout.fillWidth: true
        axis: index
        axisName: root.axisNames[index]
        axisPosition: root.axisPosition ? Units.fromRos(root.axisPosition[root.axisNames[index].toLowerCase()], control.unitType) : 0
        readOnly: root.readOnly
        decimals: Config.data.dro.decimals[control.unitType]

        onTouchOff: function (position) {
          root.touchOff(axis, Units.toRos(position, control.unitType));
        }
        onReset: root.reset(axis)

        PathPilotToolTip {
          activationActor: control.buttonHovered
          itemId: "dro_zero_" + root.axisNames[index].toLowerCase()
        }
      }
    }
  }
}
