import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.base
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.handlers
import QtCore

Item {
  id: root

  QtObject {
    id: d
    property bool loaded: false
    property int realIndex: 0
  }

  ApplicationPlugins {
    id: applicationPlugins
    searchPaths: [ResourcePaths.conversationalPluginPath, ResourcePaths.userPluginPath]
    Component.onCompleted: {
      updatePlugins();
      d.loaded = true;
    }
  }

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
    spacing: 0

    RowLayout {
      Layout.fillHeight: true
      Layout.fillWidth: false
      Layout.preferredWidth: 400
      Layout.margins: Sizes.singleMargin

      ProgramTreeView {
        Layout.fillHeight: true
        Layout.fillWidth: true
        model: Handlers.conversational.programModel
        selection: Handlers.conversational.programSelectionModel
        readOnly: Handlers.conversational.editingActive
        copyPasteCommand: Handlers.conversational.copyPasteCommand
        copyPasteSourceUuid: Handlers.conversational.copyPasteSourceUuid

        onDoubleClicked: Handlers.conversational.requestEditing()
        onDragAndDropCompleted: function (sourceUuid, targetUuid) {
          Handlers.conversational.manipulator.moveBlock(sourceUuid, targetUuid);
        }

        Keys.onReturnPressed: Handlers.conversational.requestEditing()
        Keys.onEnterPressed: Handlers.conversational.requestEditing()
        Keys.forwardTo: buttons

        onVisibleChanged: {
          if (!root.visible) {
            Handlers.conversational.endEditing();
          }
        }
      }

      ColumnLayout {
        Layout.fillWidth: false
        spacing: 0

        SaveProgramButtons {
          id: saveButtons
        }
        VerticalFiller {
        }
        ModifyProgramButtons {
          id: buttons
        }
      }
    }

    ConversationalNotebook {
      id: notebook
      Layout.fillHeight: true
      Layout.fillWidth: true
      Layout.margins: Sizes.halfMargin
      Layout.leftMargin: 0
      model: applicationPlugins.plugins
      popupSpace: root
    }
  }

  Binding {
    target: d
    property: "realIndex"
    value: notebook.currentIndex
    when: d.loaded
  }

  Binding {
    target: notebook
    property: "currentIndex"
    value: d.realIndex
    when: d.loaded
  }

  // save notebook index during development
  Loader {
    active: devMode
    sourceComponent: Settings {
      category: "development"
      property int conversationalNotebookIndex: d.realIndex
      Component.onCompleted: d.realIndex = conversationalNotebookIndex
    }
  }
}
