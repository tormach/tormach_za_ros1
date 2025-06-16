import QtQuick
import QtCore
import pathpilot.handlers
import pathpilot.robot

QtObject {
  id: root

  readonly property int activePanel: panelSwitcher.activePanel
  readonly property bool panelLocked: panelSwitcher.panelLocked

  property int applicationWindowVisibility: Window.AutomaticVisibility
  property int applicationWindowFlags: Qt.Window

  property ProgramHandler programHandler
  property QtObject jogHandler
  property QtObject stateHandler

  readonly property bool jogAllowed: (stateHandler.driveStart.inEffect && (!programHandler.programRunning || programHandler.programPausedActive))
  readonly property bool browseFilesAllowed: !programHandler.programRunning
  readonly property bool modifyFramesAllowed: !programHandler.programRunning
  readonly property bool changeFramesAllowed: !programHandler.programRunning || programHandler.programPausedActive
  readonly property bool modifyIosAllowed: !programHandler.programRunning
  readonly property bool modifySettingsAllowed: !programHandler.programRunning
  readonly property bool exitAllowed: !programHandler.programRunning
  readonly property bool dryRunSwitchAllowed: !programHandler.programRunning

  /** Locks/unlocks panel switching **/
  function lockPanel(lock) {
    panelSwitcher.lockPanel(lock);
  }

  /** Tries to switch the panel with next item**/
  function switchPanel(panel) {
    panelSwitcher.trySwitchPanelWithNextItem(panel);
  }

  /** Tries to switch the panel **/
  function trySwitchPanel(panel) {
    return panelSwitcher.trySwitchPanel(panel);
  }

  /** Starts a program in wizard mode (hiding the program path
                      and switching back to the previous program after completion. **/
  function startWizardProgram(path, panel) {
    var switchPanelBack = function () {
      Handlers.app.switchPanel(panel);
    };
    var loadAndStartProgram = function () {
      Handlers.program.loadAndStartInternalProgram(path, switchPanelBack);
    };
    Handlers.conversational.commitChanges(loadAndStartProgram, qsTr("starting wizard program"));
    Handlers.app.switchPanel(Panels.MainPanel);
  }

  readonly property PanelSwitcher _panelSwitcher: PanelSwitcher {
    id: panelSwitcher

    // save notebook index during development
    readonly property Loader _settingsLoader: Loader {
      active: devMode
      sourceComponent: Settings {
        category: "development"
        property int mainNotebookIndex: panelSwitcher.activePanel
        Component.onCompleted: panelSwitcher.activePanel = mainNotebookIndex
      }
    }
  }
}
