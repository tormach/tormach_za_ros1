import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.robot.validator
import pathpilot.handlers
import pathpilot.robot.program.blocks

PathPilotPopup {
  id: root
  property bool globalMode: false
  property bool poseMode: true
  property alias exactPoseMode: checkBox.checked
  property bool updateMode: false
  property string name: ""

  readonly property QtObject _d: QtObject {
    id: d
    readonly property var waypointManipulator: root.globalMode ? Handlers.conversational.globalWaypointsManipulator : Handlers.conversational.manipulator

    function setDefaultName() {
      waypointNameValidator.waypoints = root.globalMode ? Handlers.conversational.globalWaypoints : Handlers.conversational.program;
      waypointNameValidator.defaultPrefix = globalRadioButton.checked ? Config.data.conversational.defaultGlobalWaypointPrefix : Config.data.conversational.defaultWaypointPrefix;
      nameInput.text = waypointNameValidator.generateDefaultName();
    }

    function addWaypoint() {
      Handlers.conversational.addWaypointRequested(nameInput.text, root.poseMode, root.globalMode, root.exactPoseMode);
    }

    function updateWaypoint() {
      Handlers.conversational.updateWaypointRequested(nameInput.text, root.poseMode, root.globalMode, root.exactPoseMode);
    }
  }

  onOpened: {
    Handlers.conversational.waypointValidator.updateValid();
    if (!root.updateMode) {
      d.setDefaultName();
      waypointNameValidator.ignoredName = "";
    } else {
      waypointNameValidator.ignoredName = root.name;
      nameInput.text = root.name;
    }
    nameInput.forceActiveFocus();
  }

  onGlobalModeChanged: d.setDefaultName()

  WaypointNameValidator {
    id: waypointNameValidator
  }

  SyntaxValidator {
    id: syntaxValidator
  }

  RowLayout {
    PathPilotLabel {
      text: root.updateMode ? qsTr("Update Waypoint from Current Position") : qsTr("Add Waypoint from Current Position")
    }
  }

  GridLayout {
    columns: 4

    ButtonGroup {
      id: typeGroup
    }

    ButtonGroup {
      id: locationGroup
    }

    PathPilotLabel {
      id: captureLabel
      font.family: Fonts.font2
      font.pixelSize: Fonts.conversationalPopups.size1
      font.bold: true
      text: qsTr("Capture:")
      Layout.alignment: Qt.AlignVCenter
    }

    RowLayout {
      // Use RowLayout to align them horizontally
      Layout.columnSpan: 1
      Layout.alignment: Qt.AlignTop
      PathPilotRadioButton {
        id: poseRadioButton
        text: qsTr("Pose")
        checked: root.poseMode
        ButtonGroup.group: typeGroup
        onClicked: root.poseMode = true
        PathPilotToolTip {
          itemId: "conv_move_pose_waypoints_radio"
        }
        Layout.alignment: Qt.AlignTop
      }

      WarningIndicator {
        id: warningIndicator
        Layout.alignment: Qt.AlignVCenter
        warnings: [programWarning]

        ProgramWarning {
          id: programWarning
          type: ProgramWarning.Types.EmptyProgram
          message: qsTr("Waypoint too close to singularity.")
        }

        visible: !Handlers.conversational.waypointValidator.valid && root.poseMode
        active: !Handlers.conversational.waypointValidator.valid && root.poseMode
      }
    }

    PathPilotRadioButton {
      id: jointsRadioButton
      text: qsTr("Joints")
      checked: !root.poseMode
      ButtonGroup.group: typeGroup
      onClicked: root.poseMode = false
      PathPilotToolTip {
        itemId: "conv_move_joint_waypoints_radio"
      }
    }

    HorizontalFiller {
    }

    PathPilotLabel {
      visible: !root.updateMode
      font.family: Fonts.font2
      font.pixelSize: Fonts.conversationalPopups.size1
      font.bold: true
      text: qsTr("Location:")
    }

    PathPilotRadioButton {
      id: localRadioButton
      visible: !root.updateMode
      text: qsTr("Program")
      checked: !root.globalMode
      ButtonGroup.group: locationGroup
      onClicked: root.globalMode = false
      PathPilotToolTip {
        itemId: "conv_move_program_waypoints_radio"
      }
    }

    PathPilotRadioButton {
      id: globalRadioButton
      visible: !root.updateMode
      text: qsTr("Global")
      checked: root.globalMode
      ButtonGroup.group: locationGroup
      onClicked: root.globalMode = true
      PathPilotToolTip {
        itemId: "conv_move_global_waypoints_radio"
      }
    }

    HorizontalFiller {
      visible: !root.updateMode
    }

    PathPilotCheckBox {
      id: checkBox
      Layout.columnSpan: 4 // Span all 3 columns
      Layout.alignment: Qt.AlignLeft // Align the checkbox to the left
      enabled: root.poseMode
      text: "Exact arm configuration"
    }

    PathPilotLabel {
      font.family: Fonts.font2
      font.pixelSize: Fonts.conversationalPopups.size1
      font.bold: true
      text: qsTr("Name:")
    }

    PathPilotTextField {
      id: nameInput
      Layout.fillWidth: true
      Layout.columnSpan: 3
      implicitWidth: 300

      validator: RegularExpressionValidator {
        regularExpression: /[A-Za-z_][0-9A-Za-z_ ]*/
      }

      function validate() {
        error = !waypointNameValidator.validate(text, 0);
        if (!error) {
          error |= !syntaxValidator.validate(text, 0);
        }
      }

      onTextEdited: {
        text = text.replace(/\s/g, '_');
        validate();
      }

      Keys.onReturnPressed: okButton.forceActiveFocus()
      Keys.onEnterPressed: okButton.forceActiveFocus()
    }
  }

  RowLayout {
    HorizontalFiller {
    }

    PathPilotButton {
      id: cancelButton
      text: qsTr("Cancel")
      onClicked: root.close()
    }

    PathPilotButton {
      id: okButton
      enabled: !nameInput.error
      text: qsTr("OK")
      onClicked: {
        root.close();
        if (root.updateMode) {
          d.updateWaypoint();
        } else {
          d.addWaypoint();
        }
      }
    }
  }
}
