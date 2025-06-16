import QtQuick
import QtQml.Models
import pathpilot.core
import pathpilot.robot.program
import pathpilot.robot.program.notification
import pathpilot.file
import pathpilot.logging

QtObject {
  id: root

  signal loadedProgramFileChanged

  property bool programModified: false // set from conversational handler via binding
  property bool programWriting: false // set from conversational handler via binding
  property alias interpreterState: interpreter.interpreterState
  property alias program: programReader.program
  property alias programUiPath: programUiReader.uiMainPath
  property alias programUiTimestamp: programUiReader.uiTimestamp

  property alias programLoaded: programReader.valid
  readonly property bool programRunning: [ProgramInterpreter.RunningState, ProgramInterpreter.PausedState, ProgramInterpreter.PausedActiveState].includes(interpreter.interpreterState)
  readonly property bool programPausedActive: [ProgramInterpreter.PausedActiveState].includes(interpreter.interpreterState)
  readonly property bool programError: [ProgramInterpreter.RuntimeErrorState, ProgramInterpreter.LoadErrorState].includes(interpreter.interpreterState)

  // program interpreter controls
  readonly property bool loadProgramAllowed: [ProgramInterpreter.StoppedState, ProgramInterpreter.IdleState, ProgramInterpreter.LoadErrorState].includes(interpreter.interpreterState)
  readonly property bool unloadProgramAllowed: [ProgramInterpreter.StoppedState, ProgramInterpreter.LoadErrorState].includes(interpreter.interpreterState)
  readonly property bool startProgramAllowed: [ProgramInterpreter.StoppedState].includes(interpreter.interpreterState)
  readonly property bool stopProgramAllowed: [ProgramInterpreter.RunningState, ProgramInterpreter.PausedState].includes(interpreter.interpreterState)
  readonly property bool stepProgramAllowed: [ProgramInterpreter.PausedState, ProgramInterpreter.StoppedState].includes(interpreter.interpreterState)
  readonly property bool pauseProgramAllowed: [ProgramInterpreter.RunningState].includes(interpreter.interpreterState)
  readonly property bool continueProgramAllowed: [ProgramInterpreter.PausedState].includes(interpreter.interpreterState)
  readonly property bool executeMdiAllowed: [ProgramInterpreter.StoppedState, ProgramInterpreter.IdleState].includes(interpreter.interpreterState)
  readonly property bool reloadInterpreterAllowed: loadProgramAllowed
  readonly property string programStatus: {
    switch (interpreter.interpreterState) {
    case ProgramInterpreter.RunningState:
      return qsTr("Running");
    case ProgramInterpreter.PausedState:
      return qsTr("Paused");
    case ProgramInterpreter.PausedActiveState:
      return qsTr("Paused Active");
    default:
      return qsTr("Idle");
    }
  }

  property ProgramReader reader: ProgramReader {
    id: programReader
    path: info.path

    program.onReset: {
      if (program.linearUnit) {
        Config.user.linearUnit = program.linearUnit;
      } else {
        program.linearUnit = Config.user.linearUnit;
      }
      if (program.angularUnit) {
        Config.user.angularUnit = program.angularUnit;
      } else {
        program.angularUnit = Config.user.angularUnit;
      }
      if (program.timeUnit) {
        Config.user.timeUnit = program.timeUnit;
      } else {
        program.timeUnit = Config.user.timeUnit;
      }
    }
  }

  property ProgramUiReader uiReader: ProgramUiReader {
    id: programUiReader
    programPath: info.path
  }

  property QtObject info: QtObject {
    property alias path: programPositionSync.filename
    property alias name: programInfo.name
    property alias valid: programReader.valid

    property ProgramInfo _programInfo: ProgramInfo {
      id: programInfo
      program: root.program
    }

    property ProgramPositionSync positionSync: ProgramPositionSync {
      id: programPositionSync
    }

    readonly property var recentFiles: recentFilesObj.recentFiles.slice().reverse()
    readonly property var recentPaths: recentFilesObj.recentPaths.slice().reverse()

    property RecentFiles _recentFilesObj: RecentFiles {
      id: recentFilesObj
      currentPath: info.path
      maximumCount: Config.data.recentFiles.maximumCount
      homePath: Config.data.programHomePath

      property Binding writeBinding: Binding {
        target: Config.user
        property: "recentPaths"
        value: recentFilesObj.recentPaths
        when: false
      }

      property Binding readBinding: Binding {
        target: recentFilesObj
        property: "recentPaths"
        value: Config.user.recentPaths
      }
    }

    function refreshRecentFiles() {
      var save = recentFilesObj.recentPaths;
      recentFilesObj.recentPaths = [];
      recentFilesObj.recentPaths = save;
    }
  }

  property MdiHistory mdiHistory: MdiHistory {
    id: mdiHistory
    maximumCount: Config.data.mdiHistory.maximumCount

    property Binding writeBinding: Binding {
      target: Config.user
      property: "mdiHistory"
      value: mdiHistory.mdiHistory
      when: false
    }

    property Binding readBinding: Binding {
      target: mdiHistory
      property: "mdiHistory"
      value: Config.user.mdiHistory
    }

    function refreshMdiHistory() {
      var save = _mdiHistory.mdiHistory;
      _mdiHistory.mdiHistory = [];
      _mdiHistory.mdiHistory = save;
    }
  }

  property ProgramInterpreter interpreter: ProgramInterpreter {
    id: interpreter
    onCommandError: function (message) {
      console.log("Error: " + message);
    }
  }

  property ProgramNotifications notifications: ProgramNotifications {
    id: notifications
  }

  property FileWatcher fileWatcher: FileWatcher {
    id: fileWatcher
    fileUrl: FileUtils.localPathToUrl(info.path)
    enabled: root.programLoaded && !root.programWriting
    onFileChanged: root.loadedProgramFileChanged() // goes through conversationalHandler to ask user to save/discards changes
  }

  property FileWatcher uiFileWatcher: FileWatcher {
    id: uiFileWatcher
    fileUrl: programUiReader.uiImportPath !== "" ? FileUtils.localPathToUrl(programUiReader.uiImportPath) : FileUtils.localPathToUrl(programUiReader.uiMainPath)
    enabled: programUiReader.valid
    onFileChanged: function () {
      console.log("UI file changed");
      programUiReader.reload();
    }
  }

  readonly property Connections connections: Connections {
    target: root
    function onProgramRunningChanged() {
      if (!root.programRunning) {
        if (d.programStoppedHook) {
          d.programStoppedHook();
          d.programStoppedHook = undefined;
        }
      }
    }

    Component.onCompleted: {
      if (fileWatcher.hasError) {
        Logging.log(qsTr("Cannot watch files: %1\nCheck your systems inotify limits!").arg(fileWatcher.errorString), LogLevel.Warn);
      }
    }
  }

  readonly property QtObject d: QtObject {
    id: d
    property var programStoppedHook
  }

  /**
  These functions do not ask the user to save outstanding changes.
  Combine with the commitChanges in ConversationalHandler when using
  in the UI.
  */
  function loadProgram(path: string) {
    var previousPath = programReader.path;
    recentFilesObj.writeBinding.when = true;
    interpreter.loadProgram(path);
    if (previousPath === path) {
      programReader.update();
    }
  }

  function loadAndStartInternalProgram(path: string, successHook: var, errorHook: var) {
    recentFilesObj.writeBinding.when = false;
    var previousPath = programReader.path;
    d.programStoppedHook = function () {
      root.loadProgram(previousPath);
      if (root.programError && errorHook) {
        errorHook();
      }
      if (!root.programError && successHook) {
        successHook();
      }
    };
    interpreter.loadProgram(path);
    interpreter.startProgram();
  }

  function reloadProgram() {
    var path = programReader.path;
    interpreter.stopProgram();
    interpreter.loadProgram(path);
    programReader.update();
  }

  function unloadProgram() {
    interpreter.unloadProgram();
  }

  function startProgram() {
    interpreter.reload(true, true);
    interpreter.startProgram();
  }

  function startSubprogram(name, loop) {
    if (loop === undefined) {
      loop = false;
    }
    interpreter.startSubprogram(name, loop);
  }

  function stopProgram() {
    interpreter.stopProgram();
  }

  function stepProgram() {
    interpreter.stepProgram();
  }

  function pauseProgram() {
    interpreter.pauseProgram();
  }

  function continueProgram() {
    interpreter.continueProgram();
  }

  function executeMDI(command: string) {
    interpreter.executeMDI(command);
    mdiHistory.writeBinding.when = true;
    mdiHistory.appendCommand(command);
  }

  function reloadInterpreter() {
    interpreter.reload();
  }
}
