import QtQuick
import QtQuick.Window
import QtCore
import pathpilot.core
import pathpilot.controls
import pathpilot.conversational

ConversationalItem {
  id: root

  PathPilotNotebook {
    id: notebook
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
    alignment: Qt.AlignTop

    onFocusedIndexChanged: {
      if (focusedIndex === -1) {
        root.releaseFocus();
      } else {
        root.forceFocus();
      }
    }

    IfElseTab {
    }

    LoopTab {
    }
  }

  Settings {
    // super convenient during development
    id: settings
    category: "development"
    property int controlStructuresNotebookIndex: notebook.currentIndex
  }

  Binding {
    target: notebook
    property: "currentIndex"
    value: settings.controlStructuresNotebookIndex
    when: devMode
  }

  Binding {
    target: settings
    property: "controlStructuresNotebookIndex"
    value: notebook.currentIndex
    when: devMode
  }
}
