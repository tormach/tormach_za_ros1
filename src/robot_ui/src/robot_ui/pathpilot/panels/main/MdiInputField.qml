import QtQuick
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers

PathPilotTextField {
  id: root
  placeholderText: qsTr("MDI")
  horizontalAlignment: Text.AlignLeft
  font.family: Fonts.font3
  enabled: Handlers.program.executeMdiAllowed

  Keys.onUpPressed: Handlers.program.mdiHistory.previousCommand()
  Keys.onDownPressed: Handlers.program.mdiHistory.nextCommand()
  Keys.onReturnPressed: function (event) {
    event.accepted = true;
  }
  Keys.onEnterPressed: function (event) {
    event.accepted = true;
  }
  Keys.onReleased: function (event) {
    if ([Qt.Key_Return, Qt.Key_Enter].includes(event.key) && (!event.isAutoRepeat)) {
      executeMDI();
    }
  }

  Connections {
    target: Handlers.program.mdiHistory
    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onCurrentCommandChanged() {
      root.text = Handlers.program.mdiHistory.currentCommand;
    }
  }

  function executeMDI() {
    Handlers.program.executeMDI(text);
    text = "";
  }
}
