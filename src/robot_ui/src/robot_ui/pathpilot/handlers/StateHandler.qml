import QtQuick
import pathpilot.core
import pathpilot.robot
import pathpilot.robot.machinetalk
import pathpilot.robot.hal
import pathpilot.robot.frame
import pathpilot.hub
import pathpilot.logging
import pathpilot.robot.preview

QtObject {
  id: root

  property RvizPreviewObject previewHandler

  readonly property QtObject _d: QtObject {
    property bool windowCaptured: root.previewHandler?.windowCaptured ?? false

    onWindowCapturedChanged: {
      if (windowCaptured) {
        userFrames.updateAxesFrame();
        toolFrames.updateAxesFrame();
        toolFrames.updateInteractiveMarker();
      }
    }
  }

  readonly property JointState jointState: JointState {
    baseLink: Config.data.robotArmBaseLink
    jointNamePrefix: "joint_"
    positionTolerance: ROS.getParam('moveit/goal_joint_tolerance') / 2
  }

  readonly property CartesianState cartesianState: CartesianState {
    positionTolerance: ROS.getParam('moveit/goal_position_tolerance') / 2
    orientationTolerance: ROS.getParam('moveit/goal_orientation_tolerance') / 2
  }

  readonly property DigitalIOs digitalIOs: DigitalIOs {
    Component.onCompleted: update()
  }

  readonly property UserFrames userFrames: UserFrames {
    namespace: "user_frames"
    cartesianState: root.cartesianState
    positionTolerance: ROS.getParam('moveit/goal_position_tolerance') / 2
    orientationTolerance: ROS.getParam('moveit/goal_orientation_tolerance') / 2

    onActiveFrameFrameChanged: userFrames.updateAxesFrame()

    function updateAxesFrame() {
      if (root.previewHandler) {
        root.previewHandler.updateUserFrameAxesFrame(userFrames.activeFrameFrame);
      }
    }
  }

  readonly property ToolFrames toolFrames: ToolFrames {
    namespace: "tool_frames"
    positionTolerance: ROS.getParam('moveit/goal_position_tolerance') / 2
    orientationTolerance: ROS.getParam('moveit/goal_orientation_tolerance') / 2

    readonly property Frames defaultFrames: Frames {
      namespace: "default_tool_frames"
    }

    onInteractiveMarkerOffsetChanged: toolFrames.updateInteractiveMarker()
    onActiveFrameFrameChanged: toolFrames.updateAxesFrame()

    function updateInteractiveMarker() {
      if (root.previewHandler) {
        root.previewHandler.updateInteractiveMarkerOffset(toolFrames.interactiveMarkerOffset);
      }
    }

    function updateAxesFrame() {
      if (root.previewHandler) {
        root.previewHandler.updateToolFrameAxesFrame(toolFrames.activeFrameFrame);
      }
    }
  }

  property QtObject machinetalk: QtObject {
    property MachinetalkInstanceListModel instanceModel: MachinetalkInstanceListModel {
    }
    property MachinetalkNodeTableModel nodeModel: MachinetalkNodeTableModel {
    }
  }

  readonly property QtObject driveControl: QtObject {
    // From hal_402_device_mgr.hal_402_mgr.Hal402Mgr.cmd_name_to_int_map
    readonly property int initCmdInt: 0
    readonly property int stopCmdInt: 1
    readonly property int startCmdInt: 2
    readonly property int homeCmdInt: 3
    readonly property int faultCmdInt: 4

    readonly property bool stopInEffect: cmdPin.value == stopCmdInt
    readonly property bool startInEffect: cmdPin.value == startCmdInt
    readonly property bool homeInEffect: cmdPin.value == homeCmdInt
    readonly property bool faultInEffect: cmdPin.value == faultCmdInt
    readonly property bool valid: cmdPin.synced

    readonly property HalPin cmdPin: HalPin {
      id: cmdPin
      topic: "hal_io/state_cmd"
      type: Hal.U32
      direction: Hal.IO
    }
  }

  readonly property QtObject driveStop: QtObject {
    readonly property bool inEffect: driveControl.stopInEffect && driveControl.valid
    readonly property bool canEffect: !inEffect

    function effectCmd() {
      driveControl.cmdPin.value = driveControl.stopCmdInt;
    }
  }

  readonly property QtObject driveStart: QtObject {
    readonly property bool inEffect: driveControl.startInEffect && driveControl.valid
    readonly property bool canEffect: !inEffect

    function effectCmd() {
      driveControl.cmdPin.value = driveControl.startCmdInt;
    }
  }

  readonly property QtObject driveHome: QtObject {
    readonly property bool inEffect: driveControl.homeInEffect && driveControl.valid
    readonly property bool canEffect: driveStop.inEffect

    function effectCmd() {
      driveControl.cmdPin.value = driveControl.homeCmdInt;
    }
  }

  readonly property QtObject probePolarity: QtObject {
    readonly property HalPin probePolarityPin: HalPin {
      id: probePolarityPin
      topic: "hal_io/probe_active_low"
      type: Hal.Bit
      direction: Hal.Out
    }

    readonly property bool allowed: probePolarityPin.synced

    function setProbePolarity(polarity) {
      probePolarityPin.value = polarity;
    }
  }

  readonly property HubConnector hubConnector: HubConnector {
    id: hubConnector
    property int previousStatus: HubConnector.IdleStatus
    ppHubUrl: Config.data.ppHubUrl
    email: ApplicationHelpers.getEnvVar("PPHUB_EMAIL", "")
    token: ApplicationHelpers.getEnvVar("PPHUB_TOKEN", "")

    onStatusChanged: {
      if (hubConnector.status == HubConnector.IdleStatus && hubConnector.previousStatus == HubConnector.UploadMachineLogdataStatus) {
        Logging.log(qsTr("Log data uploaded to PathPilot HUB for technical support"), LogLevel.Info);
      }
      hubConnector.previousStatus = hubConnector.status;
    }
  }
}
