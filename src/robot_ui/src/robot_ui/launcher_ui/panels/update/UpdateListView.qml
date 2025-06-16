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
  property string currentTag: ""
  property string currentName: ""
  property string currentChangelog
  readonly property bool versionSelected: root.currentIndex != -1

  spacing: Sizes.singleSpacing
  clip: true
  snapMode: ListView.SnapToItem

  Connections {
    target: model

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onModelReset() {
      root.currentIndex = -1;
    }

    function onCheckingCompleted() {
      if (root.count === 1) {
        root.currentIndex = 0;
      }
    }
  }

  ScrollBar.vertical: ScrollBar {
    visible: root.count > 1
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
            text: qsTr("<b>Channel:</b> %1").arg(model.channel)
          }
          PathPilotLabel {
            font.family: Fonts.font2
            font.pixelSize: Fonts.launcher.size1
            text: qsTr("<b>Version:</b> %1 %2").arg(model.version).arg(model.codename)
          }
          PathPilotLabel {
            font.family: Fonts.font2
            font.pixelSize: Fonts.launcher.size1
            text: qsTr("<b>Description:</b> %1").arg(model.description)
          }
          PathPilotLabel {
            font.family: Fonts.font2
            font.pixelSize: Fonts.launcher.size1
            text: qsTr("<b>Created:</b> %1").arg(model.creationDate)
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
        root.currentName = name;
        root.currentTag = tag;
        root.currentChangelog = changelog;
        root.currentIndex = index;
      }
    }
  }
}
