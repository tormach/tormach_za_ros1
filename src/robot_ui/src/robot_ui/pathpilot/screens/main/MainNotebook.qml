import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import pathpilot.core
import pathpilot.controls
import pathpilot.panels.main
import pathpilot.panels.status
import pathpilot.panels.conversational
import pathpilot.panels.settings
import pathpilot.panels.file
import pathpilot.panels.jog
import pathpilot.panels.frames
import pathpilot.handlers

PathPilotNotebook {
  id: root

  Binding {
    target: root
    property: "activePanel"
    value: Handlers.app.activePanel
  }

  Binding {
    target: root
    property: "switchingDisabled"
    value: Handlers.app.panelLocked
  }

  requestPanelSwitch: function (newPanel) {
    var result = Handlers.app.trySwitchPanel(newPanel);
    if (!result) {
      root.sychronize();
    }
  }

  MainPanel {
    id: mainPanel
  }

  FilePanel {
    id: filePanel
  }

  FramesPanel {
    id: framesPanel
  }

  SettingsPanel {
    id: settingsPanel
  }

  ConversationalPanel {
    id: conversationalPanel
  }

  JogPanel {
    id: jogPanel
  }

  StatusPanel {
    id: statusPanel
  }
}
