import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.controls
import pathpilot.conversational
import pathpilot.handlers

ConversationalPanelBase {
  id: root
  title: qsTr("Conversational")
  enabled: Handlers.conversational.conversationalAllowed

  EditProgramPanel {
    id: editProgramPanel
    anchors.fill: parent
    visible: Handlers.program.programLoaded
  }

  NewProgramPanel {
    id: newProgramPanel
    anchors.fill: parent
    visible: !editProgramPanel.visible
  }
}
