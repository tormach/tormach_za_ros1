import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import pathpilot.core
import pathpilot.controls
import launcher_ui.logic 1.0

ListView {
  id: root
  property int itemHeight: dummyButton.implicitHeight
  property int itemWidth: width
  property string pathPilotRobotLaunchArguments: ''
  property string robotOperatingSystemLaunchArguments: ''

  spacing: Sizes.singleSpacing
  clip: true
  snapMode: ListView.SnapToItem

  Connections {
    target: model
    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onModelReset() {
      root.currentIndex = -1;
    }
  }

  ScrollBar.vertical: ScrollBar {
    snapMode: ScrollBar.SnapAlways
    policy: ScrollBar.AlwaysOn
  }

  PathPilotButton {
    id: dummyButton

    visible: false
  }

  delegate: Item {
    id: item
    height: col.height + Sizes.singleMargin * 2
    width: root.itemWidth - Sizes.doubleMargin

    RowLayout {
      anchors.fill: parent

      Rectangle {
        Layout.fillHeight: true
        Layout.minimumWidth: 10
        color: root.currentIndex === index ? Colors.green2 : "#00000000"
      }

      Rectangle {
        id: rect
        Layout.fillHeight: true
        Layout.fillWidth: true
        anchors.rightMargin: Sizes.doubleMargin
        color: Colors.gray1

        Column {
          id: col
          x: Sizes.doubleMargin
          y: (parent.height - height) / 2
          anchors.leftMargin: Sizes.singleMargin
          anchors.rightMargin: Sizes.doubleMargin

          PathPilotLabel {
            font.family: Fonts.font2
            font.pixelSize: Fonts.launcher.size1
            text: qsTr("<b>Configuration:</b> %1").arg(name)
          }
        }
      }
    }

    MouseArea {
      anchors.fill: parent
      height: parent.height
      width: parent.width

      z: 10
      onEntered: rect.color = Colors.green2
      onExited: rect.color = Colors.gray1
      hoverEnabled: true
      onClicked: {
        root.currentIndex = index;
        root.pathPilotRobotLaunchArguments = pprlargs;
        root.robotOperatingSystemLaunchArguments = roslargs;
      }
    }
  }
}
