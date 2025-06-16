import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls
import pathpilot.core
import pathpilot.controls

Page {
  id: root
  property alias model: repeater.model
  property alias currentIndex: bar.currentIndex
  default property alias data_: stack.data

  property int focusedIndex: -1

  property Item popupSpace: null
  background: Item {
  }

  Rectangle {
    anchors.fill: parent
    color: Colors.white3
  }

  StackLayout {
    id: stack
    anchors.fill: parent
    currentIndex: bar.currentIndex

    Repeater {
      id: repeater
      ConversationalNotebookTab {
        id: tab
        source: modelData.mainFile
        title: modelData.title
        active: false

        onLoaded: {
          item.focused = Qt.binding(function () {
              return stack.currentIndex === index;
            });
          item.popupSpace = root.popupSpace;
          item.forceFocus.connect(function () {
              root.focusedIndex = index;
              root.currentIndex = index;
            });
          item.releaseFocus.connect(function () {
              root.focusedIndex = -1;
            });
        }

        Component.onCompleted: {
          modelData.loadPlugin();
          tab.active = true;
        }
      }
    }
  }

  PathPilotTabButton {
    id: dummyTabButton
    visible: false
  }

  header: TabBar {
    id: bar
    height: dummyTabButton.implicitHeight + Sizes.singleMargin
    spacing: (root.focusedIndex === -1) ? Sizes.singleSpacing : 0
    readonly property int calculatedTabWidth: repeater.model.length > 0 ? (bar.width - (repeater.model.length - 1) * spacing) / repeater.model.length : 0
    readonly property int tabWidth: Math.min(dummyTabButton.implicitWidth, calculatedTabWidth)
    background: Item {
    }

    Repeater {
      model: repeater.model

      PathPilotTabButton {
        text: modelData.title
        iconObject: IconObject {
          source: modelData.iconSource
          size: "16x16"
        }
        alignment: Qt.AlignTop
        visible: (root.focusedIndex == -1) || (root.focusedIndex == index)
        width: visible ? bar.tabWidth : 0

        PathPilotToolTip {
          itemId: modelData.toolTipItemId
          sidePosition: modelData.toolTipPosRight ? PathPilotToolTip.Side.Left : PathPilotToolTip.Side.Left
        }
      }
    }
  }
}
