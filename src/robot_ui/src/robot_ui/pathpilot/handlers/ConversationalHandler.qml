import QtQuick
import QtQml.Models
import pathpilot.base
import pathpilot.core
import pathpilot.file
import pathpilot.robot.program
import pathpilot.robot.program.blocks
import pathpilot.robot.validator 1.0

QtObject {
  id: root

  signal editingRequested(string type)
  signal editingStopped
  signal addWaypointPopupRequested(var globalMode)
  signal addWaypointRequested(string name, bool poseMode, bool globalMode, bool exactPoseMode)
  signal updateWaypointPopupRequested(string name, bool poseMode, bool globalMode, bool hasExactPose)
  signal updateWaypointRequested(string name, bool poseMode, bool globalMode, bool exactPoseMode)

  signal saveModifiedFileDialogRequested(var callback, bool autoUpdated, string operation)
  signal newFilePopupRequested(var callback, bool ignoreWarnings)
  signal overwriteWarningPopupRequested(var callback, string originalPath, bool ignoreWarnings)
  signal programWarningsPopupRequested(var callback)

  property ProgramHandler programHandler
  property QtObject stateHandler
  property string programName: programHandler.info.name
  property string programPath: programHandler.info.path
  readonly property string selectedBlockUuid: d.uuidData ? d.uuidData : ""
  property alias program: programManipulator.modifiedProgram
  property alias programWarnings: programValidator.warnings

  property alias globalWaypoints: globalWaypointsManipulator.modifiedWaypoints

  readonly property bool programModified: combinedHistory.undoPossible || d.unitsModified
  readonly property bool programAutoUpdated: programManipulator.modifiedProgram.headerAutoUpdated
  readonly property bool programWriting: programWriter.writing || d.templateWriting
  readonly property bool programHasWarnings: !programValidator.valid
  readonly property bool programUnsaved: programPath.startsWith(temporaryDirectory.path)
  property bool editingActive: false

  // expose copy paste operations
  property alias copyPasteCommand: programCopyPaste.currentCommand
  property alias copyPasteSourceUuid: programCopyPaste.sourceUuid

  // program modification controls
  readonly property bool moveBlockDownAllowed: blockData.valid && (blockData.level > 1) && (blockData.nextUuid !== "")
  readonly property bool moveBlockUpAllowed: blockData.valid && (blockData.level > 1) && (blockData.previousUuid !== "")
  readonly property bool deleteBlockAllowed: blockData.valid && (blockData.type !== "mainprogram")
  readonly property bool redoAllowed: combinedHistory.redoPossible
  readonly property bool undoAllowed: combinedHistory.undoPossible
  readonly property bool saveAllowed: programModified || programUnsaved
  readonly property bool saveAsAllowed: programHandler.unloadProgramAllowed
  readonly property bool newAllowed: programHandler.unloadProgramAllowed || programHandler.loadProgramAllowed
  readonly property bool copyAllowed: blockData.valid && (blockData.level > 1)
  readonly property bool cutAllowed: blockData.valid && (blockData.level > 1)
  readonly property bool pasteAllowed: copyAllowed && programCopyPaste.pastePossible
  readonly property bool toggleEnabledAllowed: blockData.valid && (blockData.level > 1)
  readonly property bool conversationalAllowed: !programHandler.programRunning

  property ProgramTreeModel programModel: ProgramTreeModel {
    program: root.program
    warnings: programValidator.warnings
  }

  property WaypointTableModel waypointsModel: WaypointTableModel {
    source: root.program
    warnings: programValidator.warnings
  }

  property ItemSelectionModel programSelectionModel: ItemSelectionModel {
    signal cleared
    model: programModel
    // clear operation doesn't trigger selectionChanged
    function clearFixed() {
      clearCurrentIndex();
      clearSelection();
      cleared();
    }
  }

  property ProgramManipulator manipulator: ProgramManipulator {
    id: programManipulator
    sourceProgram: programHandler.program
    modifiedProgram {
      linearUnit: Config.user.linearUnit
      angularUnit: Config.user.angularUnit
      timeUnit: Config.user.timeUnit
      linearUnitDecimals: Config.data.dro.decimals[Config.user.linearUnit]
      angularUnitDecimals: Config.data.dro.decimals[Config.user.angularUnit]
    }

    onUndoAdded: programValidator.analyzeProgram()
    onRedoAdded: programValidator.analyzeProgram()
    onUndoCleared: programValidator.analyzeProgram()
  }

  property ProgramValidator validator: ProgramValidator {
    id: programValidator
    program: programManipulator.modifiedProgram
    globalWaypoints: root.globalWaypoints
    digitalInputNames: root.stateHandler.digitalIOs.digitalInputNames
    digitalOutputNames: root.stateHandler.digitalIOs.digitalOutputNames
    userFrameNames: root.stateHandler.userFrames.frameNames
    toolFrameNames: root.stateHandler.toolFrames.frameNames
    mainLoopWarningEnabled: Config.user.conversational.mainLoopWarningEnabled

    onDigitalInputNamesChanged: programValidator.analyzeProgramDelayed()
    onDigitalOutputNamesChanged: programValidator.analyzeProgramDelayed()
    onUserFrameNamesChanged: programValidator.analyzeProgramDelayed()
    onToolFrameNamesChanged: programValidator.analyzeProgramDelayed()
    onMainLoopWarningEnabledChanged: programValidator.analyzeProgramDelayed()

    function analyzeProgramDelayed() {
      validationTimer.restart(); // program analyzing is delayed to collated multiple requests generated by signal
    }

    readonly property Connections connections: Connections {
      target: programValidator.globalWaypoints
      function onWaypointRemoved() {
        programValidator.analyzeProgramDelayed();
      }
      function onWaypointInserted() {
        programValidator.analyzeProgramDelayed();
      }
      function onWaypointUpdated() {
        programValidator.analyzeProgramDelayed();
      }
      function onReset() {
        programValidator.analyzeProgramDelayed();
      }
    }

    readonly property Timer validationTimer_: Timer {
      id: validationTimer
      interval: 100
      repeat: false
      onTriggered: programValidator.analyzeProgram()
    }
  }

  property ProgramCopyPaste copyPaste: ProgramCopyPaste {
    id: programCopyPaste
    manipulator: programManipulator
  }

  property WaypointTableModel globalWaypointsModel: WaypointTableModel {
    source: globalWaypointsManipulator.modifiedWaypoints
  }

  property GlobalWaypointsManipulator globalWaypointsManipulator: GlobalWaypointsManipulator {
    id: globalWaypointsManipulator
    sourceWaypoints: globalWaypointsInterface
    onUndoAdded: function () {
      // instantly write global waypoint changes to the store
      globalWaypointsManipulator.modifiedWaypoints.writeToStore();
      globalWaypointsManipulator.resetHistory();
      globalWaypointsManipulator.sourceWaypoints.readFromStore();
    }
  }

  property ProgramTemplates programTemplates: ProgramTemplates {
    id: programTemplates
    searchPaths: [ResourcePaths.programTemplatePath]

    Component.onCompleted: {
      programTemplates.update();
      defaultTimer.start();
    }
  }

  property QtObject _d: QtObject {
    id: d
    readonly property var uuidData: programModel.data(programSelectionModel.currentIndex, ProgramTreeModel.UuidRole)

    // workaround: for some reason QML doesn't care about unit changes when binding directly
    readonly property string sourceProgramLinearUnit: programManipulator?.sourceProgram?.linearUnit ?? "m"
    readonly property string modifiedProgramLinearUnit: programManipulator.modifiedProgram.linearUnit
    readonly property string sourceProgramAngularUnit: programManipulator?.sourceProgram?.angularUnit ?? "rad"
    readonly property string modifiedProgramAngularUnit: programManipulator.modifiedProgram.angularUnit
    readonly property string sourceProgramTimeUnit: programManipulator?.sourceProgram?.timeUnit ?? "s"
    readonly property string modifiedProgramTimeUnit: programManipulator.modifiedProgram.timeUnit
    // we delay the update of unitsModified to prevent a binding loop
    readonly property bool unitsModified_: (d.sourceProgramLinearUnit != d.modifiedProgramLinearUnit) || (d.sourceProgramAngularUnit != d.modifiedProgramAngularUnit) || (d.sourceProgramTimeUnit != d.modifiedProgramTimeUnit)
    property bool unitsModified: false
    onUnitsModified_Changed: {
      unitsModifiedTimer.stop();
      unitsModifiedTimer.start();
    }
    property Timer unitsModifiedTimer: Timer {
      repeat: false
      interval: 10
      onTriggered: d.unitsModified = d.unitsModified_
    }

    // disable file watching when generating template program
    property bool templateWriting: false

    property Connections programConnections: Connections {
      target: root.programHandler
      function onLoadedProgramFileChanged() {
        root.commitChanges(programHandler.reloadProgram, qsTr("auto-reloading externally modified program"));
      }
    }
  }

  property CombinedHistory _combinedHistory: CombinedHistory {
    id: combinedHistory
    manipulators: [programManipulator] // not using globalWaypointsManipulators history
  }

  property ProgramWriter _writer: ProgramWriter {
    id: programWriter
    program: root.program
    path: root.programPath
  }

  property GlobalWaypoints _globalWaypointsInterface: GlobalWaypoints {
    id: globalWaypointsInterface

    Component.onCompleted: globalWaypointsInterface.readFromStore()
  }

  property BlockData _blockData: BlockData {
    id: blockData
    uuid: root.selectedBlockUuid
    program: root.program
  }

  property TemporaryDirectory _temporaryDirectory: TemporaryDirectory {
    id: temporaryDirectory

    Component.onDestruction: {
      if (root.programUnsaved) {
        programHandler.unloadProgram();
      }
    }
  }

  property Timer _defaultTimer: Timer {
    id: defaultTimer
    interval: 1000
    repeat: false
    onTriggered: {
      if (programHandler.info.valid == "" || !programHandler.info.valid) {
        root.createDefaultProgram();
      }
    }
  }

  property FileInfo _fileInfo: FileInfo {
    id: fileInfo
  }

  property PoseWaypointValidator waypointValidator: PoseWaypointValidator {
  }

  /**
  Ask the user to commit outstanding program modifications
  and then continue with the task.
  */
  function commitChanges(callback: var, operation: string) {
    if (!(root.programModified || root.programAutoUpdated)) {
      callback();
    } else {
      var autoUpdated = root.programAutoUpdated && !root.programModified;
      root.saveModifiedFileDialogRequested(callback, autoUpdated, operation);
    }
  }

  function save(callback: var, ignoreWarnings: bool) {
    if (ignoreWarnings == undefined) {
      ignoreWarnings = false;
    }
    if (root.programUnsaved) {
      saveAs(undefined, undefined, callback, ignoreWarnings);
      return;
    }
    if (root.programHasWarnings && !ignoreWarnings) {
      root.programWarningsPopupRequested(function () {
          root.save(callback, true);
        });
      return;
    }
    programWriter.write();
    root.globalWaypoints.writeToStore();
    programHandler.reloadProgram();
    if (callback) {
      callback();
    }
  }

  function saveAs(path: string, overwrite: bool, callback: var, ignoreWarnings: bool) {
    if (ignoreWarnings == undefined) {
      ignoreWarnings = false;
    }
    if (root.programHasWarnings && !ignoreWarnings) {
      root.programWarningsPopupRequested(function () {
          root.saveAs(path, overwrite, callback, true);
        });
      return;
    }
    if (path == undefined) {
      root.newFilePopupRequested(callback, ignoreWarnings);
      return;
    }
    if (overwrite == undefined) {
      overwrite = false;
    }
    fileInfo.path = path;
    if (fileInfo.exists && !overwrite) {
      root.overwriteWarningPopupRequested(callback, fileInfo.absolutePath, ignoreWarnings);
    } else {
      programWriter.writeToPath(path);
      root.globalWaypoints.writeToStore();
      programHandler.loadProgram(path);
      if (callback) {
        callback();
      }
    }
  }

  function new_() {
    if (programTemplates.templates.length == 1) {
      // auto select template if only one is available
      root.createProgramFromTemplate(programTemplates.templates[0]);
    } else {
      // unload program shows the template selection panel
      programHandler.unloadProgram();
    }
  }

  function reset() {
    combinedHistory.resetHistory();
  }

  function clearSelection() {
    programSelectionModel.clearFixed();
  }

  function selectBlock(uuid: string) {
    var index = programModel.indexForUuid(uuid);
    // clear before to ensure update of selection
    programSelectionModel.clearCurrentIndex();
    programSelectionModel.clearSelection();
    programSelectionModel.setCurrentIndex(index, ItemSelectionModel.ClearAndSelect);
  }

  function moveBlockUp() {
    programManipulator.moveBlock(blockData.previousUuid, blockData.uuid);
    selectBlock(blockData.uuid);
  }

  function moveBlockDown() {
    programManipulator.moveBlock(blockData.uuid, blockData.nextUuid);
    selectBlock(blockData.uuid);
  }

  function deleteBlock() {
    var next = blockData.nextUuid;
    programManipulator.removeBlock(blockData.uuid);
    selectBlock(next);
  }

  function toggleBlockEnabled() {
    programManipulator.updateBlock(blockData.uuid, {
        "disabled": !blockData.disabled
      });
  }

  function redo() {
    combinedHistory.redo();
    programSelectionModel.clearFixed();
  }

  function undo() {
    combinedHistory.undo();
    programSelectionModel.clearFixed();
  }

  function copy(uuid: string) {
    programCopyPaste.copy(uuid);
  }

  function cut(uuid: string) {
    programCopyPaste.cut(uuid);
  }

  function paste(uuid: string) {
    var newUuid = programCopyPaste.paste(uuid);
    selectBlock(newUuid);
  }

  function requestEditing() {
    root.editingRequested(blockData.type);
  }

  function startEditing() {
    if (root.editingActive) {
      return;
    }
    root.editingActive = true;
  }

  function endEditing() {
    if (!root.editingActive) {
      return;
    }
    root.editingActive = false;
    root.editingStopped();
  }

  function requestAddWaypoint(globalMode) {
    // abort if conversational is not open
    if (!root.newAllowed) {
      return;
    }
    root.addWaypointPopupRequested(globalMode);
  }

  function requestUpdateWaypoint(name: string, poseMode: bool, globalMode: bool, hasExactPose: bool) {
    root.updateWaypointPopupRequested(name, poseMode, globalMode, hasExactPose);
  }

  function createProgramFromTemplate(template: ProgramTemplateItem) {
    d.templateWriting = true;
    temporaryDirectory.cleanup();
    var path = temporaryDirectory.createFilePath(qsTr("unsaved%1").arg(".py"));
    template.apply(path);
    d.templateWriting = false;
    programHandler.loadProgram(path);
  }

  function createDefaultProgram() {
    var templates = programTemplates.templates;
    for (var i = 0; i < templates.length; ++i) {
      if (templates[i].name == Config.data.conversational.defaultProgramTemplate) {
        createProgramFromTemplate(templates[i]);
      }
    }
  }
}
