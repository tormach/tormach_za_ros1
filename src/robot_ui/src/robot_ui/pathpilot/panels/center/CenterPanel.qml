import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.frame
import pathpilot.handlers

PathPilotPanel {
  id: root

  GridLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
    rowSpacing: Sizes.singleSpacing
    columnSpacing: Sizes.doubleSpacing * 3
    columns: 2

    RowLayout {
      Layout.columnSpan: 2

      PathPilotLabel {
        text: qsTr("User Frame:")
      }

      FrameComboBox {
        id: frameComboBox
        Layout.fillWidth: true
        frames: Handlers.state.userFrames
        readOnly: !Handlers.app.changeFramesAllowed
        defaultFrameName: qsTr("none")
      }

      PathPilotLabel {
        text: qsTr("Tool Frame:")
      }

      FrameComboBox {
        id: toolFrameComboBox
        Layout.fillWidth: true
        frames: Handlers.state.toolFrames
        readOnly: !Handlers.app.changeFramesAllowed
        defaultFrameName: qsTr("none")
      }
    }

    Spacer {
      Layout.columnSpan: 2
      Layout.fillWidth: true
    }

    AxisDroPanel {
      id: axisDroPanel
      Layout.preferredWidth: root.width * 0.4
      Layout.fillWidth: true
      Layout.fillHeight: true
      readOnly: !Handlers.app.modifyFramesAllowed || !Handlers.state.userFrames.activeFrame

      onTouchOff: function (axis, position) {
        Handlers.state.userFrames.touchOffAxis(axis, position);
      }
      onReset: function (axis) {
        Handlers.state.userFrames.resetAxis(axis);
      }
    }

    JointDroPanel {
      id: jointDroPanel
      Layout.preferredWidth: root.width * 0.4
      Layout.fillWidth: true
      Layout.fillHeight: true
    }

    Spacer {
      Layout.columnSpan: 2
      Layout.fillWidth: true
    }

    RowLayout {
      Layout.fillHeight: false
      spacing: Sizes.doubleSpacing * 2

      PathPilotLabel {
        Layout.fillHeight: true
        text: qsTr("Status:")
        font.pixelSize: Fonts.centerPanel.size1
      }

      Text {
        Layout.fillHeight: true
        Layout.fillWidth: true

        text: Handlers.program.programStatus
        font.pixelSize: Fonts.centerPanel.size2
        color: Colors.white2
        verticalAlignment: Text.AlignVCenter
      }
    }

    RowLayout {
      Layout.fillHeight: false
      spacing: Sizes.doubleSpacing * 2

      PathPilotLabel {
        Layout.fillHeight: true
        text: qsTr("Units:")
        font.pixelSize: Fonts.centerPanel.size1
      }

      Text {
        Layout.fillHeight: true
        Layout.fillWidth: true
        text: Config.user.linearUnit + " / " + Config.user.angularUnit + " / " + Config.user.timeUnit
        font.pixelSize: Fonts.centerPanel.size2
        color: Colors.white2
        verticalAlignment: Text.AlignVCenter
      }
    }
  }
}
