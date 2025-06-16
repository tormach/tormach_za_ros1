import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls
import QtCore
import pathpilot.core
import pathpilot.controls

Page {
  id: root

  default property alias stackData: stack.data
  property int alignment: Qt.AlignBottom
  property int activePanel: 0
  property alias currentIndex: root.activePanel // ToDo: Find and change all occurences

  property int focusedIndex: -1

  property bool switchingDisabled: false
  property var requestPanelSwitch: function (newPanel) {
    if (root.activePanel != newPanel) {
      root.activePanel = newPanel;
    }
  }

  onActivePanelChanged: synchronize()

  function synchronize() {
    if (bar.currentIndex != root.activePanel) {
      bar.isSyncing = true;
      bar.currentIndex = root.activePanel;
      bar.isSyncing = false;
    }
  }

  background: Item {
    objectName: "notebook_background"
  }

  Rectangle {
    anchors.fill: parent
    color: Colors.white3
  }

  Rectangle {
    parent: root
    anchors.fill: parent
    color: "yellow"
    visible: false
  }

  StackLayout {
    id: stack
    anchors.fill: parent
    currentIndex: bar.currentIndex

    Instantiator {
      model: stack.count
      delegate: Connections {
        required property int index
        target: enabled ? stack.children[index] : null
        function onForceFocus() {
          root.focusedIndex = index;
          root.currentIndex = index;
        }
        function onReleaseFocus() {
          root.focusedIndex = -1;
        }
      }
    }

    Instantiator {
      model: stack.count
      delegate: Binding {
        required property int index
        target: (stack.count > index) ? stack.children[index] : null
        property: "focused"
        value: root.focusedIndex == index
      }
    }
  }

  header: root.alignment === Qt.AlignTop ? bar : null
  footer: root.alignment === Qt.AlignBottom ? bar : null

  PathPilotTabButton {
    id: dummyTabButton
    visible: false
  }

  TabBar {
    id: bar
    property bool isSyncing: false
    height: dummyTabButton.height + Sizes.singleMargin
    spacing: (root.focusedIndex === -1) ? Sizes.singleSpacing : 0
    enabled: !switchingDisabled

    background: Item {
    }

    Repeater {
      id: repeater
      model: stack.children

      PathPilotTabButton {
        alignment: root.alignment
        width: visible ? implicitWidth : 0
        text: stack.children[index].title
        iconObject: stack.children[index].icon
        highlighted: stack.children[index].highlighted
        highlightedColor: stack.children[index].highlightedColor
        visible: (root.focusedIndex == -1) || (root.focusedIndex == index)
      }
    }

    onCurrentIndexChanged: {
      if (root.activePanel != currentIndex) {
        root.requestPanelSwitch(currentIndex);
      }
      if (!isSyncing) {
        root.synchronize();
      }
    }
  }
}
