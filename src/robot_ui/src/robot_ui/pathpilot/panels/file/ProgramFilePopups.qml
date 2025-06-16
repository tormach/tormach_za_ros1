import QtQuick
import QtCore
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers
import pathpilot.file

Item {
  id: root

  SaveModifiedWarningPopup {
    id: saveModifiedPopup
    property var callback
    property int nextPanel

    onSave: {
      Handlers.conversational.save(function () {
          Handlers.app.switchPanel(nextPanel);
          callback();
        });
    }

    onDiscard: {
      Handlers.conversational.reset();
      Handlers.app.switchPanel(nextPanel);
      callback();
    }

    onCancel: {
      Handlers.app.switchPanel(nextPanel);
    }

    onOpened: Handlers.app.switchPanel(Panels.ConversationalPanel)
  }

  NewFilePopup {
    id: newFilePopup
    property var callback
    property bool ignoreWarnings
    onAccepted: function (path) {
      Handlers.conversational.saveAs(path, false, newFilePopup.callback, newFilePopup.ignoreWarnings);
    }
  }

  OverwriteWarningPopup {
    id: overwriteWarningPopup
    property var callback
    property bool ignoreWarnings
    onAccepted: function (path) {
      Handlers.conversational.saveAs(path, true, overwriteWarningPopup.callback, overwriteWarningPopup.ignoreWarnings);
    }
  }

  Connections {
    target: Handlers.conversational

    function onSaveModifiedFileDialogRequested(callback: var, autoUpdated: bool, operation: string) {
      saveModifiedPopup.callback = callback;
      saveModifiedPopup.autoUpdated = autoUpdated;
      saveModifiedPopup.nextPanel = Handlers.app.activePanel;
      saveModifiedPopup.operation = operation;
      saveModifiedPopup.open();
    }

    function onNewFilePopupRequested(callback: var, ignoreWarnings: bool) {
      newFilePopup.callback = callback;
      newFilePopup.ignoreWarnings = ignoreWarnings;
      newFilePopup.open();
    }

    function onOverwriteWarningPopupRequested(callback: var, originalPath: string, ignoreWarnings: bool) {
      overwriteWarningPopup.originalPath = originalPath;
      overwriteWarningPopup.callback = callback;
      overwriteWarningPopup.ignoreWarnings = ignoreWarnings;
      overwriteWarningPopup.open();
    }
  }
}
