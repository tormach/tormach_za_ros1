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
        color: selected ? Colors.green2 : "#00000000"
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
            text: qsTr("<b>Version:</b> %1 %2").arg(version).arg(codename)
          }
          PathPilotLabel {
            font.family: Fonts.font2
            font.pixelSize: Fonts.launcher.size1
            text: qsTr("<b>Channel:</b> %1").arg(channel)
            visible: root.model.channelFilter == ""
          }
          PathPilotLabel {
            font.family: Fonts.font2
            font.pixelSize: Fonts.launcher.size1
            text: qsTr("<b>Description:</b> %1").arg(description)
          }
          PathPilotLabel {
            font.family: Fonts.font2
            font.pixelSize: Fonts.launcher.size1
            text: qsTr("<b>Created:</b> %1").arg(creationDate)
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
      acceptedButtons: Qt.LeftButton | Qt.RightButton
      onClicked: function (mouse) {
        if (mouse.button === Qt.RightButton) {
          // Should this happen or should nothing happen on right-click?
          root.model.selectToggleSingle(index, !selected);
        }
        if (mouse.button === Qt.LeftButton) {
          switch (mouse.modifiers) {
          case Qt.ControlModifier:
            root.model.selectToggleSingle(index, !selected);
            break;
          case Qt.ShiftModifier:
            root.model.selectMulti(index);
            break;
          default:
            root.model.selectSingle(index);
            break;
          }
        }
      }
    }
  }
}
