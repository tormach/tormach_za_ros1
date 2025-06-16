import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.conversational
import pathpilot.robot
import pathpilot.robot.program
import pathpilot.robot.program.blocks
import pathpilot.handlers

ConversationalItem {
  id: root

  onVisibleChanged: {
    if (root.visible) {
      waypointView.selectLastRow();
    }
  }

  QtObject {
    id: d
    readonly property bool editBlockMode: Handlers.conversational.editingActive
    property bool globalWaypointMode: false
    property alias linearMove: linearMoveRadio.checked
    property alias jointMove: jointMoveRadio.checked
    property alias velocityScale: velocityScaleSlider.value
    property double velocity: 0.0
    property alias accelerationScale: accelerationScaleSlider.value
    readonly property var waypointManipulator: globalWaypointMode ? Handlers.conversational.globalWaypointsManipulator : Handlers.conversational.manipulator
    readonly property WaypointTableModel waypointListModel: d.globalWaypointMode ? Handlers.conversational.globalWaypointsModel : Handlers.conversational.waypointsModel
    readonly property var waypointsSource: d.globalWaypointMode ? Handlers.conversational.globalWaypoints : Handlers.conversational.program

    readonly property double jointDefaultVelocityScale: 1.0
    readonly property double linearMaxVelocity: Units.fromRos(ROS.getParam("/robot_description_planning/cartesian_limits/max_trans_vel"), Config.user.linearUnit + "/" + Config.user.timeUnit)
    readonly property double linearDefaultVelocity: Math.floor(d.linearMaxVelocity / 2.0)
    readonly property double linearDefaultAccelerationScale: 0.5

    function prepareWaypointData(name, target, poseMode, frame, arm_config = WaypointData.AnyType, rev_count = null) {
      return {
        "name": name,
        "target": target,
        "target_type": poseMode ? WaypointData.Pose : WaypointData.Joints,
        "arm_config": arm_config,
        "rev_count": rev_count,
        "frame": frame
      };
    }

    function convertFromRos(target, poseMode) {
      var newTarget;
      if (poseMode) {
        var linear = Units.fromRos(target.slice(0, 3), Config.user.linearUnit);
        var angular = Units.fromRos(target.slice(3, 6), Config.user.angularUnit);
        newTarget = linear.concat(angular);
      } else {
        newTarget = Units.fromRos(target, Config.user.angularUnit);
      }
      return newTarget;
    }

    function convertToRos(target, poseMode) {
      var newTarget;
      if (poseMode) {
        var linear = Units.toRos(target.slice(0, 3), Config.user.linearUnit);
        var angular = Units.toRos(target.slice(3, 6), Config.user.angularUnit);
        newTarget = linear.concat(angular);
      } else {
        newTarget = Units.toRos(target, Config.user.angularUnit);
      }
      return newTarget;
    }

    function addWaypointFromCurrent(name, poseMode, update, exactPoseMode) {
      if (poseMode) {
        if (exactPoseMode) {
          var isValid = Handlers.conversational.waypointValidator.valid;
          var armConfig = Handlers.conversational.waypointValidator.armConfig;
          var revCount = Handlers.conversational.waypointValidator.revCount;
        }
        var axisPositions = Handlers.state.cartesianState.pose.axisPositions;
        var target = getValues(axisPositions, Config.data.axisNames);
        var frame = Handlers.state.userFrames.activeFrame;
      } else {
        var jointPositions = Handlers.state.jointState.jointPositions;
        var target = getValues(jointPositions, Config.data.jointNames);
        var frame = "";
      }
      if (!d.globalWaypointMode) {
        target = convertFromRos(target, poseMode);
      }
      if (update) {
        d.waypointManipulator.updateWaypoint(waypointData.uuid, prepareWaypointData(name, target, poseMode, frame));
      } else {
        if (poseMode && exactPoseMode) {
          d.waypointManipulator.addWaypoint(prepareWaypointData(name, target, poseMode, frame, armConfig, revCount));
        } else {
          d.waypointManipulator.addWaypoint(prepareWaypointData(name, target, poseMode, frame));
        }
      }
    }

    function getValues(position, names) {
      var pos = [];
      for (var i = 0; i < names.length; ++i) {
        pos.push(position[names[i].toLowerCase()]);
      }
      return pos;
    }

    function editWaypoint() {
      d.waypointManipulator.updateWaypoint(waypointData.uuid, prepareWaypointData());
    }

    function removeWaypoints() {
      var uuids = [];
      for (var i = 0; i < waypointView.selectedRows.length; ++i) {
        var row = waypointView.selectedRows[i];
        var index = waypointView.model.index(row, 0);
        var uuid = waypointView.model.data(index, WaypointTableModel.UuidRole);
        uuids.push(uuid);
      }
      waypointView.clearSelection();
      for (var i = 0; i < uuids.length; ++i) {
        d.waypointManipulator.removeWaypoint(uuids[i]);
      }
    }

    function goToWaypoint() {
      var poseMode = waypointData.targetType == WaypointData.Pose;
      var target = waypointData.target;
      if (!d.globalWaypointMode) {
        target = convertToRos(target, poseMode);
      }
      addWaypointPanel.target = target;
      addWaypointPanel.frame = Handlers.state.userFrames.activeFrame;
      addWaypointPanel.poseMode = poseMode;
      addWaypointPanel.name = waypointData.name;
      addWaypointPanel.show();
    }

    function selectCurrentWaypoint() {
      var name = blockData.waypoint;
      waypointView.clearSelection();
      if (name == "") {
        return;
      }
      if (name.indexOf("\"") === 0) {
        d.globalWaypointMode = true;
        name = name.replace(/\"/g, "");
      } else {
        d.globalWaypointMode = false;
      }
      var result = waypointView.selectWaypointByName(name);
    }

    function prepareMoveBlockData() {
      return {
        "waypoint": (d.globalWaypointMode ? "\"%1\"" : "%1").arg(waypointData.name),
        "type": d.linearMove ? "movel" : (d.jointMove ? "movej" : "movef"),
        "velocity_scale": (d.jointMove && d.velocityScale < 1.0) ? d.velocityScale.toFixed(2) : null,
        "velocity": (d.linearMove && d.velocity !== d.linearDefaultVelocity) ? d.velocity : null,
        "acceleration_scale": (d.linearMove && d.accelerationScale !== 0.5) ? d.accelerationScale.toFixed(2) : null
      };
    }

    function prepareFrameBlockData(frame) {
      return {
        "name": frame,
        "frame_type": FrameBlockData.ChangeUserFrame
      };
    }

    function addMoveBlock(blockUuid) {
      Handlers.conversational.manipulator.beginGroup();
      if (waypointData.targetType == WaypointData.Pose && frameBlockData.lastFrame !== waypointData.frame) {
        blockUuid = Handlers.conversational.manipulator.createBlock(blockUuid, "frame");
        Handlers.conversational.manipulator.updateBlock(blockUuid, prepareFrameBlockData(waypointData.frame));
      }
      var uuid = Handlers.conversational.manipulator.createBlock(blockUuid, "movel");
      Handlers.conversational.manipulator.updateBlock(uuid, prepareMoveBlockData());
      Handlers.conversational.manipulator.endGroup();
      Handlers.conversational.selectBlock(uuid);
    }

    function addFrameBlock(blockUuid) {
      Handlers.conversational.manipulator.beginGroup();
      var uuid = Handlers.conversational.manipulator.createBlock(blockUuid, "frame");
      Handlers.conversational.manipulator.updateBlock(uuid, prepareFrameBlockData(Handlers.state.userFrames.activeFrame));
      Handlers.conversational.manipulator.endGroup();
      Handlers.conversational.selectBlock(uuid);
    }

    function updateMoveBlock() {
      Handlers.conversational.manipulator.updateBlock(blockData.uuid, prepareMoveBlockData());
      Handlers.conversational.endEditing();
    }

    function cancelEditing() {
      Handlers.conversational.endEditing();
    }

    function startEditing() {
      Handlers.conversational.startEditing();
      if (blockData.type == "movel") {
        linearMoveRadio.checked = true;
      } else if (blockData.type == "movej") {
        jointMoveRadio.checked = true;
      } else {
        freeMoveRadio.checked = true;
      }
      d.velocityScale = blockData.velocityScale;
      d.accelerationScale = blockData.accelerationScale;
      d.velocity = blockData.velocity;
    }
  }

  Connections {
    target: Handlers.conversational

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onEditingRequested(type) {
      if ((type == "movel") || (type == "movej") || (type == "movef")) {
        d.startEditing();
        root.forceFocus();
        d.selectCurrentWaypoint();
      }
    }

    function onEditingStopped() {
      if (root.focused) {
        root.releaseFocus();
      }
    }

    function onAddWaypointRequested(name, poseMode, globalMode, exactPoseMode) {
      d.globalWaypointMode = globalMode;
      d.addWaypointFromCurrent(name, poseMode, false, exactPoseMode);
    }

    function onUpdateWaypointRequested(name, poseMode, globalMode, exactPoseMode) {
      d.globalWaypointMode = globalMode;
      d.addWaypointFromCurrent(name, poseMode, true, exactPoseMode);
    }
  }

  WaypointData {
    id: waypointData
    uuid: waypointView.currentUuid
    source: d.waypointsSource
  }

  MoveBlockData {
    id: blockData
    uuid: Handlers.conversational.selectedBlockUuid
    program: Handlers.conversational.program
  }

  FrameBlockData {
    id: frameBlockData
    uuid: Handlers.conversational.selectedBlockUuid
    program: Handlers.conversational.program
  }

  AddWaypointPanel {
    id: addWaypointPanel
    parent: root.popupSpace
    anchors.fill: parent
    visible: false
  }

  GridLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
    anchors.leftMargin: Sizes.doubleMargin
    rowSpacing: Sizes.singleSpacing
    columnSpacing: Sizes.singleSpacing
    columns: 2

    RowLayout {
      PathPilotRadioButton {
        text: qsTr("Program Waypoints")
        checked: !d.globalWaypointMode
        onClicked: {
          d.globalWaypointMode = false;
        }
        PathPilotToolTip {
          itemId: "conv_move_program_waypoints_radio"
        }
      }
      PathPilotRadioButton {
        text: qsTr("Global Waypoints")
        checked: d.globalWaypointMode
        onClicked: {
          d.globalWaypointMode = true;
        }
        PathPilotToolTip {
          itemId: "conv_move_global_waypoints_radio"
        }
      }
    }

    ColumnLayout {
      Layout.fillWidth: false
      Layout.preferredWidth: 200
      Layout.rowSpan: 2

      PathPilotButton {
        Layout.fillWidth: true
        Layout.preferredHeight: 100
        text: qsTr("New waypoint\nfrom current\nPosition")
        horizontalAlignment: Text.AlignHCenter
        onClicked: {
          Handlers.conversational.requestAddWaypoint(d.globalWaypointMode);
        }
        PathPilotToolTip {
          itemId: "add_new_waypoint_from_current_position"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }

      PathPilotButton {
        Layout.fillWidth: true
        Layout.preferredHeight: 100
        text: qsTr("Update waypoint\nfrom current\nPosition")
        horizontalAlignment: Text.AlignHCenter
        enabled: waypointView.selectedRows.length == 1
        onClicked: {
          var hasExactPose = waypointData.armConfig != null;
          Handlers.conversational.requestUpdateWaypoint(waypointData.name, waypointData.targetType == WaypointData.Pose, d.globalWaypointMode, hasExactPose);
        }

        PathPilotToolTip {
          itemId: "msg_update_waypoint_from_current_position"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }
      RemoveWaypointPopup {
        id: removeWaypointPopup
        onAccepted: d.removeWaypoints()
      }
      PathPilotButton {
        Layout.fillWidth: true
        text: qsTr("Remove Waypoint")
        horizontalAlignment: Text.AlignHCenter
        enabled: waypointView.selectedRows.length > 0
        onClicked: {
          if (d.globalWaypointMode) {
            removeWaypointPopup.open();
          } else {
            d.removeWaypoints();
          }
        }

        PathPilotToolTip {
          itemId: "msg_remove_waypoint"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }

      PathPilotButton {
        Layout.fillWidth: true
        text: qsTr("Go To Waypoint")
        horizontalAlignment: Text.AlignHCenter
        enabled: waypointView.selectedRows.length == 1
        onClicked: d.goToWaypoint()

        PathPilotToolTip {
          itemId: "msg_go_to_waypoint"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }

      VerticalFiller {
      }

      PathPilotButton {
        Layout.fillWidth: true
        Layout.preferredHeight: 100
        visible: !d.editBlockMode
        text: qsTr("Add change frame\nto active frame\nto program")
        horizontalAlignment: Text.AlignHCenter
        onClicked: d.addFrameBlock((blockData.valid && (blockData.level > buttons.minimumLevel)) ? blockData.uuid : "")

        PathPilotToolTip {
          itemId: "msg_add_change_frame_to_active_frame_to_program"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }

      ConversationalButtons {
        id: buttons
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignRight
        rows: 2
        columns: 1
        editBlockMode: d.editBlockMode
        blockData: blockData
        addUpdateEnabled: waypointView.selectedRows.length == 1
        addButton.text: qsTr("add move to\nselected waypoint\nto program")
        addButton.implicitHeight: 100
        addButton.horizontalAlignment: Text.AlignHCenter
        addButtonTooltipId: "conv_move_add_to_program"

        onAddClicked: function (uuid) {
          d.addMoveBlock(uuid);
        }
        onUpdateClicked: d.updateMoveBlock()
        onCancelClicked: d.cancelEditing()

        PathPilotToolTip {
          itemId: "msg_add_move_to_selected_waypoint_to_program"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }
    }

    ColumnLayout {
      WaypointTableView {
        id: waypointView
        Layout.fillWidth: true
        Layout.fillHeight: true
        waypointsModel: d.waypointListModel
        linearUnit: d.globalWaypointMode ? Units.rosLinearUnit : Config.user.linearUnit
        angularUnit: d.globalWaypointMode ? Units.rosAngularUnit : Config.user.angularUnit

        onRowCountChanged: waypointView.selectLastRow()

        Connections {
          target: d
          function onGlobalWaypointModeChanged() {
            waypointView.selectLastRow();
          }
        }
        Connections {
          target: d.waypointListModel
          function onModelReset() {
            waypointView.selectLastRow();
          }
        }
      }

      RowLayout {
        Layout.preferredHeight: velocityScaleSlider.height
        Layout.fillHeight: false

        PathPilotRadioButton {
          id: linearMoveRadio
          text: qsTr("Linear")

          onClicked: d.velocity = d.linearDefaultVelocity

          PathPilotToolTip {
            itemId: "conv_move_type_radio"
          }
        }

        PathPilotRadioButton {
          id: jointMoveRadio
          text: qsTr("Joint")
          checked: true

          onClicked: d.velocityScale = d.jointDefaultVelocityScale

          PathPilotToolTip {
            itemId: "conv_move_type_radio"
          }
        }

        PathPilotRadioButton {
          id: freeMoveRadio
          text: qsTr("Free")
          checked: false

          PathPilotToolTip {
            itemId: "conv_move_type_radio"
          }
        }

        RowLayout {
          visible: d.linearMove

          Spacer {
            vertical: true
          }

          PathPilotLabel {
            text: qsTr("Velocity:")
          }

          PathPilotTextField {
            id: velocityTextField
            validator: DoubleValidator {
              bottom: 0
              top: d.linearMaxVelocity
            }

            text: d.velocity

            Binding {
              target: d
              property: "velocity"
              value: velocityTextField.acceptableInput ? velocityTextField.text : 0.0
            }
          }

          PathPilotLabel {
            text: Config.user.linearUnit + " / " + Config.user.timeUnit
          }

          Spacer {
            vertical: true
          }

          PathPilotLabel {
            enabled: d.linearMove
            text: qsTr("Acceleration:")
          }

          PathPilotSlider {
            id: accelerationScaleSlider
            enabled: d.linearMove
            from: 0.0
            to: 1.0
            value: d.linearDefaultAccelerationScale
            stepSize: 0.01
          }
        }

        RowLayout {
          visible: d.jointMove

          Spacer {
            vertical: true
          }

          PathPilotLabel {
            text: qsTr("Velocity:")
          }

          PathPilotSlider {
            id: velocityScaleSlider
            from: 0.0
            to: 1.0
            value: d.jointDefaultVelocityScale
            stepSize: 0.01
          }

          HorizontalFiller {
            implicitWidth: velocityScaleSlider.implicitWidth
          }
        }

        HorizontalFiller {
        }
      }
    }
  }
}
