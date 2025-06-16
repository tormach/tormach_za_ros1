import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.base
import pathpilot.core
import pathpilot.controls
import pathpilot.file
import pathpilot.robot.program
import pathpilot.handlers

Item {
  id: root

  QtObject {
    id: d
    property bool wasVisible: false
  }

  onVisibleChanged: {
    var templates = Handlers.conversational.programTemplates.templates;
    if (root.visible) {
      d.wasVisible = true;
      if (templates.length === 1) {
        // auto select template if just one is available
        Handlers.conversational.createProgramFromTemplate(templates[0]);
      }
      return;
    }
    // automatically select a template when the user exits the screen and nothing was selected
    if (!root.visible && d.wasVisible && !Handlers.program.programLoaded) {
      Handlers.conversational.createProgramFromTemplate(templates[0]);
    }
    d.wasVisible = false;
  }

  Column {
    anchors.centerIn: parent
    spacing: Sizes.singleSpacing

    PathPilotGroupBox {
      title: qsTr("Create New")

      Column {
        id: column2
        spacing: Sizes.singleSpacing

        Repeater {
          model: Handlers.conversational.programTemplates.templates

          PathPilotButton {
            required property ProgramTemplateItem modelData
            text: modelData.title
            implicitWidth: 180
            onClicked: Handlers.conversational.createProgramFromTemplate(modelData)
          }
        }
      }
    }
  }
}
