import QtQuick
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.robot.preview
import pathpilot.robot.preview_waypoints
import pathpilot.handlers

WindowController {
  id: root
  property bool previewEnabled: Config.user.preview.enabled
  property string rvizConfig: Config.user.preview.rvizConfig !== "" ? Config.user.preview.rvizConfig : Config.data.preview.rvizConfig
  property bool showGlobalWaypoints: Config.user.preview.showGlobalWaypoints
  property bool showProgramWaypoints: Config.user.preview.showProgramWaypoints
  property string activeWaypointName: ""
  active: true
  winId: windowIdSubscriber.winId

  function reload() {
    if (rvizProcess.active) {
      rvizProcess.stop();
      rvizProcess.start();
    }
  }

  function viewMode() {
    if (!d.active) {
      return;
    }
    planningDisplay.setPropertyValue("Scene Robot/Show Robot Visual", true);
    planningDisplay.setPropertyValue("Scene Robot/Robot Alpha", 1.0);
    planningDisplay.setPropertyValue("Planning Request/Query Goal State", false);
    planningDisplay.apply();
    tools.currentTool = "Move Camera";
  }

  function interactiveMode() {
    if (!d.active) {
      return;
    }
    planningDisplay.setPropertyValue("Scene Robot/Show Robot Visual", true);
    planningDisplay.setPropertyValue("Scene Robot/Robot Alpha", 1.0);
    planningDisplay.setPropertyValue("Planning Request/Goal State Alpha", 0.5);
    planningDisplay.setPropertyValue("Planning Request/Query Goal State", true);
    planningDisplay.apply();
    tools.currentTool = "Interact";
  }

  function updateUserFrameAxesFrame(frame) {
    if (!d.active) {
      return;
    }
    userFrameAxesDisplay.activeFrame = frame;
    userFrameAxesDisplay.setPropertyValue("Reference Frame", frame);
    userFrameAxesDisplay.apply();
    waypointMarkers._update();
  }

  function updateToolFrameAxesFrame(frame) {
    if (!d.active) {
      return;
    }
    toolFrameAxesDisplay.activeFrame = frame;
    toolFrameAxesDisplay.setPropertyValue("Reference Frame", frame);
    toolFrameAxesDisplay.apply();
  }

  function updateInteractiveMarkerOffset(offset) {
    if (!d.active) {
      return;
    }
    planningDisplay.interactiveMarkerOffset = offset;
    planningDisplay.setPropertyValue("Planning Request/Interactive Marker Offset/Position/X", offset.position.x);
    planningDisplay.setPropertyValue("Planning Request/Interactive Marker Offset/Position/Y", offset.position.y);
    planningDisplay.setPropertyValue("Planning Request/Interactive Marker Offset/Position/Z", offset.position.z);
    planningDisplay.setPropertyValue("Planning Request/Interactive Marker Offset/Orientation/X", offset.orientation.x);
    planningDisplay.setPropertyValue("Planning Request/Interactive Marker Offset/Orientation/Y", offset.orientation.y);
    planningDisplay.setPropertyValue("Planning Request/Interactive Marker Offset/Orientation/Z", offset.orientation.z);
    planningDisplay.setPropertyValue("Planning Request/Interactive Marker Offset/Orientation/W", offset.orientation.scalar);
    planningDisplay.apply();
  }

  readonly property QtObject _d: QtObject {
    id: d
    property bool fullyLoaded: false
    readonly property bool activationCondition: root.previewEnabled && globalPositionObject.active && d.fullyLoaded
    readonly property bool deactivationCondition: !root.previewEnabled
    readonly property bool active: (activeDelayed || activationCondition) && !deactivationCondition
    property bool activeDelayed: false // removes the binding loop
    property bool showGlobalWaypoints: root.showGlobalWaypoints
    property bool showProgramWaypoints: root.showProgramWaypoints
    property string activeWaypointName: root.activeWaypointName
    onActiveChanged: {
      delayTimer.restart();
    }
    property Timer _delayTimer: Timer {
      id: delayTimer
      interval: 100
      repeat: false
      onTriggered: {
        d.activeDelayed = d.active;
      }
    }
  }

  Component.onCompleted: {
    d.fullyLoaded = true;
  }

  readonly property GlobalPositionObject globalPositionObject: GlobalPositionObject {
    id: globalPositionObject
    target: root
  }

  readonly property WindowIdSubscriber _windowIdSubscriber: WindowIdSubscriber {
    id: windowIdSubscriber
    topic: "/rviz/window_id"
  }

  readonly property KeyEventSubscriber _keyEventSubscriber: KeyEventSubscriber {
    id: keyEventSubscriber
    topic: "/rviz/key_event"
    globalShortcuts: GlobalShortcuts
  }
  // needs to be placed after the window controller for proper cleanup
  readonly property SystemProcess _rvizProcess: SystemProcess {
    id: rvizProcess
    active: d.activeDelayed
    command: "rosrun rviz rviz -s \"\" -d " + root.rvizConfig + " -e __name:=rviz"
  }

  readonly property RvizTools tools: RvizTools {
    id: tools
  }

  readonly property RvizDisplay planningDisplay: RvizDisplay {
    id: planningDisplay
    property var interactiveMarkerOffset: null
    name: "MotionPlanning"
  }

  readonly property RvizDisplay userFrameAxesDisplay: RvizDisplay {
    id: userFrameAxesDisplay
    property string activeFrame: "world"
    name: "UserFrameAxes"
  }

  readonly property RvizDisplay toolFrameAxesDisplay: RvizDisplay {
    id: toolFrameAxesDisplay
    property string activeFrame: "tool0"
    name: "ToolFrameAxes"
  }

  readonly property WaypointMarkers waypointMarkers: WaypointMarkers {
    showGlobalWaypoints: d.showGlobalWaypoints
    globalWaypoints: Handlers.conversational ? Handlers.conversational.globalWaypoints : null

    showProgramWaypoints: d.showProgramWaypoints
    programWaypoints: Handlers.conversational ? Handlers.conversational.program : null

    activeWaypointName: d.activeWaypointName
  }

  readonly property RvizOptions options: RvizOptions {
    id: options
  }

  readonly property RvizView view: RvizView {
    id: view
  }
}
