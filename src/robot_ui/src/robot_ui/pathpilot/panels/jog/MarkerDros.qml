import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.robot.program
import pathpilot.robot.jog
import pathpilot.handlers

PathPilotPanel {
  id: root
  property var axisNames: Config.data.axisNames
  property var jointNames: Config.data.jointNames
  property bool poseMode: true
  property var axisPositions: [0, 0, 0, 0, 0, 0]
  property var jointPositions: [0, 0, 0, 0, 0, 0]

  signal updateAxisValue(int index, double value)

  readonly property QtObject _d: QtObject {
    id: d
    readonly property int axes: root.axisNames.length
    readonly property int joints: root.jointNames.length
  }

  ColumnLayout {
    id: container
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin

    Repeater {
      model: root.poseMode ? d.axes : 0

      RowLayout {
        PathPilotLabel {
          Layout.alignment: Qt.AlignVCenter
          text: root.axisNames[index]
        }

        PathPilotDroField {
          id: textField
          readonly property string unitType: index > 2 ? Config.user.angularUnit : Config.user.linearUnit
          Layout.fillWidth: true
          decimals: Config.data.dro.decimals[textField.unitType]
          font.pixelSize: Fonts.jogPanel.size2

          onValueUpdated: function (value) {
            root.updateAxisValue(index, Units.toRos(value, textField.unitType));
          }

          Binding {
            target: textField
            property: "value"
            value: Units.fromRos(root.axisPositions[index], textField.unitType)
          }
        }
      }
    }
  }
}
