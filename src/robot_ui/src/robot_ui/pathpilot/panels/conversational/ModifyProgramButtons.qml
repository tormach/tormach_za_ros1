import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.robot.program.blocks
import pathpilot.handlers

ColumnLayout {
  id: root
  spacing: Sizes.singleSpacing

  BlockData {
    id: blockData
    uuid: Handlers.conversational.selectedBlockUuid
    program: Handlers.conversational.program
  }

  PathPilotIconButton {
    id: copyButton
    icon_: Icons.program.copy
    enabled: Handlers.conversational.copyAllowed
    onClicked: Handlers.conversational.copy(blockData.uuid)

    PathPilotToolTip {
      itemId: "msg_copy"
    }
  }

  PathPilotIconButton {
    id: cutButton
    icon_: Icons.program.cut
    enabled: Handlers.conversational.cutAllowed
    onClicked: Handlers.conversational.cut(blockData.uuid)

    PathPilotToolTip {
      itemId: "msg_cut"
    }
  }

  PathPilotIconButton {
    id: pasteButton
    icon_: Icons.program.paste
    enabled: Handlers.conversational.pasteAllowed
    onClicked: Handlers.conversational.paste(blockData.uuid)

    PathPilotToolTip {
      itemId: "msg_paste"
    }
  }

  PathPilotIconButton {
    id: upButton
    icon_: Icons.program.up
    enabled: Handlers.conversational.moveBlockUpAllowed
    onClicked: Handlers.conversational.moveBlockUp()

    PathPilotToolTip {
      itemId: "msg_move_up"
    }
  }

  PathPilotIconButton {
    id: downButton
    icon_: Icons.program.down
    enabled: Handlers.conversational.moveBlockDownAllowed
    onClicked: Handlers.conversational.moveBlockDown()

    PathPilotToolTip {
      itemId: "msg_move_down"
    }
  }

  PathPilotIconButton {
    id: toggleEnabledButton
    icon_: Icons.program.toggleEnabled
    enabled: Handlers.conversational.toggleEnabledAllowed
    onClicked: Handlers.conversational.toggleBlockEnabled()
    PathPilotToolTip {
      itemId: "msg_toggle_active"
    }
  }

  PathPilotIconButton {
    id: deleteButton
    icon_: Icons.program.delete_
    enabled: Handlers.conversational.deleteBlockAllowed
    onClicked: Handlers.conversational.deleteBlock()

    PathPilotToolTip {
      itemId: "msg_delete"
    }
  }

  Shortcut {
    sequences: [StandardKey.Delete]
    enabled: deleteButton.enabled && root.visible
    onActivated: deleteButton.clicked()
  }

  Shortcut {
    sequences: [StandardKey.Copy]
    enabled: copyButton.enabled && root.visible
    onActivated: copyButton.clicked()
  }

  Shortcut {
    sequences: [StandardKey.Cut]
    enabled: cutButton.enabled && root.visible
    onActivated: cutButton.clicked()
  }

  Shortcut {
    sequences: [StandardKey.Paste]
    enabled: pasteButton.enabled && root.visible
    onActivated: pasteButton.clicked()
  }

  Shortcut {
    sequence: "Shift+Up"
    enabled: root.visible
    onActivated: upButton.clicked()
  }

  Shortcut {
    sequence: "Shift+Down"
    enabled: root.visible
    onActivated: downButton.clicked()
  }

  Shortcut {
    sequence: "Space"
    enabled: toggleEnabledButton.enabled && root.visible
    onActivated: toggleEnabledButton.clicked()
  }

  HorizontalFiller {
  }
}
