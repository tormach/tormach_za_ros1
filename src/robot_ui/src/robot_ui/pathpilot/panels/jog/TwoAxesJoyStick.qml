import QtQuick
import QtQuick.Window
import QtQuick.Shapes
import pathpilot.core
import pathpilot.controls

Item {
  id: root
  property string axis1Name: "X"
  property string axis2Name: "Y"
  readonly property bool axis1MinusPressed: joyStick.xMinusActive || axis1MinusActiveExternal
  readonly property bool axis1PlusPressed: joyStick.xPlusActive || axis1PlusActiveExternal
  readonly property bool axis2MinusPressed: joyStick.yMinusActive || axis2MinusActiveExternal
  readonly property bool axis2PlusPressed: joyStick.yPlusActive || axis2PlusActiveExternal
  readonly property bool axis1MinusHovered: joyStick.xMinusHovered || axis1MinusActiveExternal
  readonly property bool axis1PlusHovered: joyStick.xPlusHovered || axis1PlusActiveExternal
  readonly property bool axis2MinusHovered: joyStick.yMinusHovered || axis2MinusActiveExternal
  readonly property bool axis2PlusHovered: joyStick.yPlusHovered || axis2PlusActiveExternal
  readonly property bool xActive: axis1PlusPressed || axis1MinusPressed
  readonly property bool yActive: axis2PlusPressed || axis2MinusPressed
  property bool axis1MinusActiveExternal: false
  property bool axis1PlusActiveExternal: false
  property bool axis2MinusActiveExternal: false
  property bool axis2PlusActiveExternal: false
  property color axis1HighlightColor: Colors.cyan1
  property color axis2HighlightColor: Colors.cyan1
  property color defaultColor: Colors.white1
  property color disabledColor: Colors.gray1
  implicitWidth: 200
  implicitHeight: width

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
    text: qsTr("%1+").arg(root.axis2Name)
    color: enabled ? (root.axis2PlusHovered ? root.axis2HighlightColor : root.defaultColor) : root.disabledColor
  }

  PathPilotLabel {
    anchors.top: body.bottom
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.margins: d.textMargin
    text: qsTr("%1-").arg(root.axis2Name)
    color: enabled ? (root.axis2MinusHovered ? root.axis2HighlightColor : root.defaultColor) : root.disabledColor
  }

  PathPilotLabel {
    anchors.left: body.right
    anchors.verticalCenter: parent.verticalCenter
    anchors.margins: d.textMargin
    text: qsTr("%1+").arg(root.axis1Name)
    color: enabled ? (root.axis1PlusHovered ? root.axis1HighlightColor : root.defaultColor) : root.disabledColor
  }

  PathPilotLabel {
    anchors.right: body.left
    anchors.verticalCenter: parent.verticalCenter
    anchors.margins: d.textMargin
    text: qsTr("%1-").arg(root.axis1Name)
    color: enabled ? (root.axis1MinusHovered ? root.axis1HighlightColor : root.defaultColor) : root.disabledColor
  }

  Shape {
    id: body
    anchors.fill: parent
    anchors.margins: d.sideMargin
    smooth: true

    ShapePath {
      strokeColor: Colors.gray2
      strokeWidth: 3
      fillGradient: RadialGradient {
        centerX: body.width / 2
        centerY: body.height / 2
        centerRadius: body.height
        focalX: centerX
        focalY: centerY
        GradientStop {
          position: 0
          color: "#5c696e"
        }
        GradientStop {
          position: 0.7
          color: "#29393e"
        }
        GradientStop {
          position: 1
          color: "#161718"
        }
      }
      startX: 0
      startY: body.height / 2
      PathArc {
        x: 0
        y: body.height / 2 + 0.5
        radiusX: body.width / 2
        radiusY: body.height / 2
        useLargeArc: true
      }
    }

    JoyStickArrow {
      anchors.horizontalCenter: parent.horizontalCenter
      anchors.top: parent.top
      anchors.topMargin: d.arrowMargin
      active: root.axis2PlusHovered
      size: d.arrowSize
      higlightColor: root.axis2HighlightColor
      defaultColor: root.defaultColor
      disabledColor: root.disabledColor
      rotation: 90
    }

    JoyStickArrow {
      anchors.horizontalCenter: parent.horizontalCenter
      anchors.bottom: parent.bottom
      anchors.bottomMargin: d.arrowMargin
      active: root.axis2MinusHovered
      size: d.arrowSize
      higlightColor: root.axis2HighlightColor
      defaultColor: root.defaultColor
      disabledColor: root.disabledColor
      rotation: 270
    }

    JoyStickArrow {
      anchors.verticalCenter: parent.verticalCenter
      anchors.left: parent.left
      anchors.leftMargin: d.arrowMargin
      active: root.axis1MinusHovered
      higlightColor: root.axis1HighlightColor
      defaultColor: root.defaultColor
      disabledColor: root.disabledColor
      size: d.arrowSize
    }

    JoyStickArrow {
      anchors.verticalCenter: parent.verticalCenter
      anchors.right: parent.right
      anchors.rightMargin: d.arrowMargin
      active: root.axis1PlusHovered
      size: d.arrowSize
      higlightColor: root.axis1HighlightColor
      defaultColor: root.defaultColor
      disabledColor: root.disabledColor
      rotation: 180
    }

    XYJoyStickControl {
      id: joyStick
      anchors.fill: parent
      hoverEnabled: true
    }
  }
}
