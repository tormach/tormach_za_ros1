import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.file
import pathpilot.robot.program
import pathpilot.handlers

ColumnLayout {
  id: root
  spacing: Sizes.singleSpacing

  PathPilotIconButton {
    id: saveButton
    icon_: Icons.program.save
    enabled: Handlers.conversational.saveAllowed
    onClicked: Handlers.conversational.save()
    PathPilotToolTip {
      itemId: "msg_save"
    }
  }

  PathPilotIconButton {
    id: saveAsButton
    icon_: Icons.program.saveAs
    enabled: Handlers.conversational.saveAsAllowed
    onClicked: Handlers.conversational.saveAs()

    PathPilotToolTip {
      itemId: "msg_save_as"
    }
  }

  PathPilotIconButton {
    id: newButton
    icon_: Icons.program.new_
    enabled: Handlers.conversational.newAllowed
    onClicked: Handlers.conversational.commitChanges(Handlers.conversational.new_, qsTr("creating new program"))
    PathPilotToolTip {
      itemId: "msg_new_program"
    }
  }

  PathPilotIconButton {
    id: undoButton
    icon_: Icons.program.undo
    enabled: Handlers.conversational.undoAllowed
    onClicked: Handlers.conversational.undo()

    PathPilotToolTip {
      itemId: "msg_undo"
    }
  }

  PathPilotIconButton {
    id: redoButton
    icon_: Icons.program.redo
    enabled: Handlers.conversational.redoAllowed
    onClicked: Handlers.conversational.redo()

    PathPilotToolTip {
      itemId: "msg_redo"
    }
  }

  Shortcut {
    sequence: StandardKey.Save
    enabled: saveButton.enabled
    onActivated: saveButton.clicked()
  }

  Shortcut {
    sequences: [StandardKey.SaveAs]
    enabled: saveAsButton.enabled
    onActivated: saveAsButton.clicked()
  }

  Shortcut {
    sequences: [StandardKey.Undo]
    enabled: undoButton.enabled
    onActivated: undoButton.clicked()
  }

  Shortcut {
    sequences: [StandardKey.Redo]
    enabled: redoButton.enabled
    onActivated: redoButton.clicked()
  }

  HorizontalFiller {
  }
}
