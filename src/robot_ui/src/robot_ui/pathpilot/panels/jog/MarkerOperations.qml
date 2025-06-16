import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.robot.jog
import pathpilot.handlers

RowLayout {
  id: root
  signal resetMarkerPose
  signal setMarkerPoseToCurrent
  signal setMarkerOrientation(double a, double b, double c)

  property alias inverse: toolOrientationSelector.inverse
  readonly property alias a: toolOrientationSelector.a
  readonly property alias b: toolOrientationSelector.b
  readonly property alias c: toolOrientationSelector.c
  property alias currentPose: toolOrientationSelector.currentPose

  readonly property QtObject _d: QtObject {
    id: d
    property int zIndex: -1
    property int xIndex: -1
    property int yIndex: -1
    readonly property int selected: (zIndex > -1) + (xIndex > -1) + (yIndex > -1)

    function resetSelection() {
      d.xIndex = -1;
      d.yIndex = -1;
      d.zIndex = -1;
    }

    function calculateOrientation() {
      toolOrientationSelector.setAxes(d.xIndex, d.yIndex, d.zIndex);
      root.setMarkerOrientation(toolOrientationSelector.a, toolOrientationSelector.b, toolOrientationSelector.c);
    }
  }

  onVisibleChanged: {
    if (visible) {
      d.resetSelection();
    }
  }

  ToolOrientationSelector {
    id: toolOrientationSelector
  }

  GridLayout {
    id: advancedLayout
    Layout.fillWidth: true
    visible: advancedToggleButton.checked

    Repeater {
      model: [qsTr("User"), qsTr("Tool X"), qsTr("Tool Y"), qsTr("Tool Z")]
      PathPilotLabel {
        Layout.fillWidth: true
        Layout.row: 0
        Layout.column: index
        text: modelData
        //color: [Colors.white1, Colors.red1, Colors.green1, Colors.blue4][index]
        horizontalAlignment: Text.AlignHCenter
      }
    }

    Repeater {
      model: ["X+", "X-", "Y+", "Y-", "Z+", "Z-"]
      PathPilotLabel {
        Layout.row: index + 1
        Layout.column: 0
        Layout.alignment: Qt.AlignHCenter
        text: modelData
      }
    }

    Repeater {
      model: 6
      PathPilotRadioButton {
        Layout.row: index + 1
        Layout.column: 1
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredHeight: 20
        Layout.preferredWidth: 20
        ButtonGroup.group: xButtonGroup
        checked: d.xIndex === index
        enabled: !(d.selected == 1 && (d.xIndex > -1 || Math.floor(d.xIndex / 2) == Math.floor(index / 2) || Math.floor(d.yIndex / 2) == Math.floor(index / 2) || Math.floor(d.zIndex / 2) == Math.floor(index / 2)))

        onClicked: {
          if (d.selected == 2) {
            d.resetSelection();
          }
          d.xIndex = index;
          if (d.selected == 2) {
            d.calculateOrientation();
          }
        }
      }
    }

    Repeater {
      model: 6
      PathPilotRadioButton {
        Layout.row: index + 1
        Layout.column: 2
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredHeight: 20
        Layout.preferredWidth: 20
        ButtonGroup.group: yButtonGroup
        checked: d.yIndex === index
        enabled: !(d.selected == 1 && (d.yIndex > -1 || Math.floor(d.xIndex / 2) == Math.floor(index / 2) || Math.floor(d.yIndex / 2) == Math.floor(index / 2) || Math.floor(d.zIndex / 2) == Math.floor(index / 2)))

        onClicked: {
          if (d.selected == 2) {
            d.resetSelection();
          }
          d.yIndex = index;
          if (d.selected == 2) {
            d.calculateOrientation();
          }
        }
      }
    }

    Repeater {
      model: 6
      PathPilotRadioButton {
        Layout.row: index + 1
        Layout.column: 3
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredHeight: 20
        Layout.preferredWidth: 20
        ButtonGroup.group: zButtonGroup
        checked: d.zIndex === index
        enabled: !(d.selected == 1 && (d.zIndex > -1 || Math.floor(d.xIndex / 2) == Math.floor(index / 2) || Math.floor(d.yIndex / 2) == Math.floor(index / 2) || Math.floor(d.zIndex / 2) == Math.floor(index / 2)))

        onClicked: {
          if (d.selected == 2) {
            d.resetSelection();
          }
          d.zIndex = index;
          if (d.selected == 2) {
            d.calculateOrientation();
          }
        }
      }
    }
  }

  GridLayout {
    Layout.fillWidth: true
    Layout.preferredHeight: advancedLayout.height
    visible: !advancedToggleButton.checked
    columns: 3
    rows: 3

    PathPilotButton {
      Layout.row: 1
      Layout.fillWidth: true
      Layout.fillHeight: true
      implicitWidth: 80
      text: qsTr("Left")
      horizontalAlignment: Text.AlignHCenter
      onClicked: {
        d.xIndex = 4;
        d.zIndex = 2;
        d.calculateOrientation();
      }
      PathPilotToolTip {
        itemId: "msg_left"
        sidePosition: PathPilotToolTip.Side.Right
      }
    }

    PathPilotButton {
      Layout.row: 0
      Layout.column: 1
      Layout.fillWidth: true
      Layout.fillHeight: true
      implicitWidth: 80
      text: qsTr("Top")
      horizontalAlignment: Text.AlignHCenter
      onClicked: {
        d.xIndex = 0;
        d.zIndex = 5;
        d.calculateOrientation();
      }
      PathPilotToolTip {
        sidePosition: PathPilotToolTip.Side.Bottom
        xOffset: -50
        notchPosX: 30
        itemId: "msg_top"
      }
    }

    PathPilotButton {
      Layout.row: 1
      Layout.column: 2
      Layout.fillWidth: true
      Layout.fillHeight: true
      implicitWidth: 80
      text: qsTr("Right")
      horizontalAlignment: Text.AlignHCenter
      onClicked: {
        d.xIndex = 4;
        d.zIndex = 3;
        d.calculateOrientation();
      }
      PathPilotToolTip {
        itemId: "msg_right"
        sidePosition: PathPilotToolTip.Side.Bottom
        xOffset: -200
        notchPosX: 200
      }
    }

    PathPilotButton {
      Layout.row: 0
      Layout.column: 0
      Layout.fillWidth: true
      Layout.fillHeight: true
      implicitWidth: 80
      text: qsTr("Back")
      horizontalAlignment: Text.AlignHCenter
      onClicked: {
        d.xIndex = 4;
        d.zIndex = 0;
        d.calculateOrientation();
      }
      PathPilotToolTip {
        itemId: "msg_back"
      }
    }

    PathPilotButton {
      Layout.row: 2
      Layout.column: 2
      Layout.fillWidth: true
      Layout.fillHeight: true
      implicitWidth: 80
      text: qsTr("Front")
      horizontalAlignment: Text.AlignHCenter
      onClicked: {
        d.xIndex = 4;
        d.zIndex = 1;
        d.calculateOrientation();
      }
      PathPilotToolTip {
        itemId: "msg_front"
        sidePosition: PathPilotToolTip.Side.Bottom
        xOffset: -150
        notchPosX: 120
      }
    }

    PathPilotButton {
      Layout.row: 2
      Layout.column: 1
      Layout.fillWidth: true
      Layout.fillHeight: true
      implicitWidth: 80
      text: qsTr("Bottom")
      horizontalAlignment: Text.AlignHCenter
      onClicked: {
        d.xIndex = 1;
        d.zIndex = 4;
        d.calculateOrientation();
      }
      PathPilotToolTip {
        itemId: "msg_bottom"
        sidePosition: PathPilotToolTip.Side.Bottom
        xOffset: -70
        notchPosX: 50
      }
    }

    PathPilotLabel {
      Layout.row: 1
      Layout.column: 1
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("Align<br>Tool")
    }
  }

  ColumnLayout {
    Layout.fillHeight: true

    PathPilotToggleButton {
      id: advancedToggleButton
      implicitHeight: 60
      propertyText1: qsTr("Basic")
      propertyText2: qsTr("Advanced")
      propertyHorizontalAlignment: Text.AlignHCenter
      propertyFont.pixelSize: 16
      checked: Config.user.jog.advancedMarkerOps
      onClicked: Config.user.jog.advancedMarkerOps = advancedToggleButton.checked

      PathPilotToolTip {
        itemId: "msg_basic_advanced"
        sidePosition: PathPilotToolTip.Side.Left
      }
    }

    PathPilotButton {
      Layout.fillWidth: false
      Layout.fillHeight: true
      visible: !root.inverse
      horizontalAlignment: Text.AlignHCenter
      text: qsTr("Reset")

      onClicked: {
        d.resetSelection();
        root.resetMarkerPose();
      }
      PathPilotToolTip {
        itemId: "msg_reset"
        sidePosition: PathPilotToolTip.Side.Left
      }
    }

    PathPilotButton {
      Layout.fillWidth: false
      Layout.fillHeight: true
      visible: !root.inverse
      horizontalAlignment: Text.AlignHCenter
      text: qsTr("Current")

      onClicked: {
        d.resetSelection();
        root.setMarkerPoseToCurrent();
      }
      PathPilotToolTip {
        itemId: "msg_current"
        sidePosition: PathPilotToolTip.Side.Left
      }
    }
  }

  ButtonGroup {
    id: xButtonGroup
  }

  ButtonGroup {
    id: yButtonGroup
  }

  ButtonGroup {
    id: zButtonGroup
  }
}
