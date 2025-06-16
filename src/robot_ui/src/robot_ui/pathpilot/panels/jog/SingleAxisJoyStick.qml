import QtQuick
import QtQuick.Window
import QtQuick.Shapes
import pathpilot.core
import pathpilot.controls

Item {
  id: root
  property string axisName: "Z"
  readonly property bool minusPressed: joyStick.yMinusActive || minusActiveExternal
  readonly property bool plusPressed: joyStick.yPlusActive || plusActiveExternal
  readonly property bool minusHovered: joyStick.yMinusHovered || minusActiveExternal
  readonly property bool plusHovered: joyStick.yPlusHovered || plusActiveExternal
  readonly property bool active: plusPressed || minusPressed
  property bool minusActiveExternal: false
  property bool plusActiveExternal: false
  property color highlightColor: Colors.cyan1
  property color defaultColor: Colors.white1
  property color disabledColor: Colors.gray1
  implicitHeight: 300
  implicitWidth: height * 0.3

  QtObject {
    id: d
    readonly property int size: Math.max(root.width, root.height)
    readonly property int arrowMargin: size * 0.03
    readonly property int arrowSize: size * 0.15
    readonly property int sideMargin: 30
    readonly property int textMargin: Sizes.singleMargin
  }

  PathPilotLabel {
    anchors.bottom: body.top
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.margins: d.textMargin
    text: qsTr("%1+").arg(root.axisName)
    color: enabled ? (root.plusHovered ? root.highlightColor : root.defaultColor) : root.disabledColor
  }

  PathPilotLabel {
    anchors.top: body.bottom
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.margins: d.textMargin
    text: qsTr(" %1-").arg(root.axisName)
    color: enabled ? (root.minusHovered ? root.highlightColor : root.defaultColor) : root.disabledColor
  }

  Rectangle {
    id: body
    anchors.fill: parent
    anchors.topMargin: d.sideMargin
    anchors.bottomMargin: d.sideMargin
    radius: width / 2
    border.width: 3
    border.color: Colors.gray2
    gradient: Gradient {
      GradientStop {
        position: 0
        color: "#29393e"
      }
      GradientStop {
        position: 0.5
        color: "#5c696e"
      }
      GradientStop {
        position: 1
        color: "#29393e"
      }
    }

    JoyStickArrow {
      anchors.horizontalCenter: parent.horizontalCenter
      anchors.top: parent.top
      anchors.topMargin: d.arrowMargin
      active: root.plusHovered
      size: d.arrowSize
      rotation: 90
    }

    JoyStickArrow {
      anchors.horizontalCenter: parent.horizontalCenter
      anchors.bottom: parent.bottom
      anchors.bottomMargin: d.arrowMargin
      active: root.minusHovered
      size: d.arrowSize
      rotation: 270
    }

    XYJoyStickControl {
      id: joyStick
      anchors.fill: parent
      xEnabled: false
      hoverEnabled: true
    }
  }
}
