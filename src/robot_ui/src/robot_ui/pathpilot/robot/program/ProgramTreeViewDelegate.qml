import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.robot.program.blocks
import "."

Rectangle {
  id: root

  implicitWidth: padding + container.x + container.implicitWidth + padding
  implicitHeight: 36
  color: d.selected ? Colors.green2 : "transparent"

  // Assigned to by TreeView:
  required property TreeView treeView
  required property bool isTreeNode
  required property bool expanded
  required property int hasChildren
  required property int depth
  required property var model
  required property var index
  required property int row

  // from model roles
  required property bool modified
  required property bool disabled
  required property var warning
  required property string type
  required property string uuid

  // by us
  property int copyPasteCommand: ProgramCopyPaste.NoCommand
  property string copyPasteSourceUuid: ""
  readonly property real indent: 20
  readonly property real padding: 5
  readonly property bool hasWarning: warning.length > 0
  readonly property color textColor: root.modified ? Colors.green3 : Colors.black1
  readonly property bool isDragSource: mouseArea.drag.active
  readonly property bool isCutSource: (copyPasteCommand === ProgramCopyPaste.CutCommand) && (copyPasteSourceUuid === uuid)
  readonly property bool isCopySource: (copyPasteCommand === ProgramCopyPaste.CopyCommand) && (copyPasteSourceUuid === uuid)
  readonly property PathPilotTreeView view: treeView.parent

  opacity: isDragSource ? 0.2 : 1.0
  z: isDragSource ? 100 : 0
  Drag.active: mouseArea.held
  Drag.source: mouseArea
  Drag.hotSpot.x: width / 2
  Drag.hotSpot.y: height / 2

  QtObject {
    id: d
    readonly property bool selected: root.view.selectedRows.includes(root.row)

    readonly property var icons: {
      "mainprogram": Icons.program.mainProgram,
      "subprogram": Icons.program.subProgram,
      "movel": Icons.program.move,
      "movej": Icons.program.moveDown,
      "movef": Icons.program.moveDown,
      "wait": Icons.program.wait,
      "set": Icons.program.faceMill,
      "pass": Icons.program.empty,
      "notify": Icons.program.notify,
      "if": Icons.program.ifElse,
      "else": Icons.program.ifElse,
      "elif": Icons.program.ifElse,
      "loop": Icons.program.loop,
      "pathpilot": Icons.program.endMill,
      "call": Icons.program.subroutine,
      "default": Icons.program.empty
    }
    readonly property var texts: {
      "mainprogram": qsTr("Program"),
      "subprogram": qsTr("Subprogram"),
      "movel": qsTr("Linear Move"),
      "movej": qsTr("Joint Move"),
      "movef": qsTr("Free Move"),
      "wait": qsTr("Wait"),
      "set": qsTr("Set"),
      "pass": qsTr("Empty"),
      "notify": qsTr("Notify"),
      "usercode": qsTr("User Code"),
      "waypoint": qsTr("Waypoint"),
      "if": qsTr("If"),
      "else": qsTr("Else"),
      "elif": qsTr("Else If"),
      "loop": qsTr("Loop"),
      "pathpilot": qsTr("PathPilot"),
      "call": qsTr("Call"),
      "assignment": qsTr("Assignment"),
      "frame": qsTr("Frame"),
      "comment": qsTr("Comment"),
      "actuate_gripper": qsTr("Actuate Gripper"),
      "": ""
    }
    readonly property var components: {
      "movel": moveComponent,
      "movej": moveComponent,
      "movef": moveComponent,
      "wait": waitComponent,
      "set": setComponent,
      "notify": notifyComponent,
      "mainprogram": programComponent,
      "subprogram": programComponent,
      "if": ifComponent,
      "elif": ifComponent,
      "loop": loopComponent,
      "pathpilot": pathpilotComponent,
      "call": callComponent,
      "assignment": assignmentComponent,
      "frame": frameComponent,
      "comment": commentComponent,
      "actuate_gripper": actuateGripperComponent
    }
  }

  component ItemText: Text {
    verticalAlignment: Text.AlignVCenter
    elide: Text.ElideRight
    font.pixelSize: Fonts.programTreeView.size1
    font.family: Fonts.font2
    color: Colors.black1
  }

  BlockData {
    id: blockData
    uuid: root.uuid
    program: root.treeView.model.program
  }

  Item {
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    anchors.left: parent.left
    width: root.padding + (root.depth + 1) * root.indent
    visible: root.isTreeNode && root.hasChildren

    PathPilotTreeViewIndicator {
      anchors.verticalCenter: parent.verticalCenter
      x: root.padding
      expanded: root.expanded
    }

    TapHandler {
      onTapped: root.treeView.toggleExpanded(root.row)
    }
  }

  Rectangle {
    id: dropIndicator
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    height: 3
    color: Colors.green2
    visible: dropArea.containsDrag
  }

  RowLayout {
    id: container
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    x: root.padding + (root.depth + 1) * root.indent
    width: root.width - root.padding * 2 - x
    spacing: 0

    Icon {
      Layout.alignment: Qt.AlignVCenter
      icon: d.icons[root.type] || d.icons["default"]
      opacity: (root.enabled && !root.disabled) ? 1.0 : 0.5
    }

    Loader {
      Layout.fillWidth: true
      Layout.fillHeight: true
      Layout.leftMargin: Sizes.singleSpacing
      Layout.rightMargin: Sizes.singleSpacing
      sourceComponent: d.components[root.type] || defaultComponent
    }

    CopyPasteIndicator {
      id: copyPasteIndicator
      Layout.alignment: Qt.AlignVCenter
      isCutSource: root.isCutSource
      isCopySource: root.isCopySource
    }

    WarningIndicator {
      id: warningIndicator
      Layout.alignment: Qt.AlignVCenter
      warnings: root.warning
    }
  }

  MouseArea {
    id: mouseArea
    property bool held: false
    property int posX: 0
    property int posY: 0
    property alias uuid: root.uuid // expose for drag and drop
    anchors.fill: container
    z: 1
    acceptedButtons: Qt.LeftButton | Qt.RightButton
    pressAndHoldInterval: 200
    drag {
      target: mouseArea.held ? root : undefined
      axis: Drag.YAxis
    }
    cursorShape: drag.active ? Qt.DragMoveCursor : Qt.ArrowCursor

    onReleased: function (mouse) {
      if (mouseArea.held) {
        parent.Drag.drop();
        mouseArea.held = false;
        root.x = mouseArea.posX;
        root.y = mouseArea.posY;
      }
    }

    onClicked: function (mouse) {
      root.treeView.forceActiveFocus();
      if (mouse.button == Qt.LeftButton) {
        root.view.selectRow(root.row, mouse.modifiers);
      } else {
        root.view.rightClicked(root.row);
      }
    }

    onDoubleClicked: root.view.doubleClicked(root.row)

    onPressAndHold: function (mouse) {
      if (mouse.button == Qt.LeftButton) {
        mouseArea.posX = root.x;
        mouseArea.posY = root.y;
        mouseArea.held = true;
      }
    }

    DropArea {
      id: dropArea
      anchors.fill: parent
      anchors.margins: Sizes.singleMargin
      onDropped: function (drop) {
        root.view.dragAndDropCompleted(drop.source.uuid, root.uuid);
      }
    }
  }

  Component {
    id: defaultComponent
    ItemText {
      color: root.textColor
      font.strikeout: root.disabled
      text: d.texts[blockData.type] || blockData.type
    }
  }

  Component {
    id: notifyComponent
    ItemText {
      id: item
      property int notifyType: 0
      property string message: ""

      color: root.textColor
      font.strikeout: root.disabled
      text: ((notifyType !== NotifyBlockData.Notification) ? ((notifyType === NotifyBlockData.Warning) ? qsTr("Warning \"%1\"") : qsTr("Error \"%1\"")) : qsTr("Notification \"%1\"")).arg(message.substring(0, 20))

      function setValues() {
        notifyType = Number(blockData.get("notify_type"));
        message = String(blockData.get("message"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: moveComponent
    ItemText {
      id: item
      readonly property var typeStrings: {
        "movel": qsTr("Linear"),
        "movej": qsTr("Joint"),
        "movef": qsTr("Free")
      }
      readonly property string type: String(typeStrings[blockData.type])
      property string waypoint: ""

      color: root.textColor
      font.strikeout: root.disabled
      text: qsTr("%1 Move [%2]").arg(type).arg(waypoint)

      function setValues() {
        waypoint = String(blockData.get("waypoint"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: ifComponent
    ItemText {
      id: item
      readonly property string type: blockData.type == "if" ? qsTr("If") : qsTr("Else If")
      property string condition: ""

      color: root.textColor
      font.strikeout: root.disabled
      text: qsTr("%1 [ %2 ]").arg(type).arg(condition)

      function setValues() {
        condition = String(blockData.get("condition"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: loopComponent
    ItemText {
      id: item
      property int loopType: 0
      property string condition: ""
      property string variable: ""
      property int count: 0

      color: root.textColor
      font.strikeout: root.disabled
      text: (loopType == LoopBlockData.WhileLoop) ? qsTr("While [ %1 ]").arg(condition) : qsTr("Loop %1 times [ %2 ]").arg(count).arg(variable)

      function setValues() {
        condition = String(blockData.get("condition"));
        variable = String(blockData.get("variable"));
        count = Number(blockData.get("count"));
        loopType = Number(blockData.get("loop_type"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: pathpilotComponent
    ItemText {
      id: item
      property int commandType: 0
      property string commandLine: ""
      property string state: ""

      color: root.textColor
      font.strikeout: root.disabled
      text: getText(item.commandType)

      function getText(type) {
        switch (type) {
        case PathPilotBlockData.CycleStartCommand:
          return qsTr("PP Cycle Start");
        case PathPilotBlockData.AbortCommand:
          return qsTr("PP Abort");
        case PathPilotBlockData.MdiCommand:
          return qsTr("PP MDI: \"%1\"".arg(commandLine));
        case PathPilotBlockData.WaitForState:
          return qsTr("Wait for PP State \"%1\"".arg(state));
        default:
          return qsTr("PP Command");
        }
      }

      function setValues() {
        commandLine = String(blockData.get("command_line"));
        commandType = Number(blockData.get("command_type"));
        state = String(blockData.get("state"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: waitComponent
    ItemText {
      id: item
      property int waitType: 0
      property double sleepTime: 0.0
      property int digitalInNr: 0
      property string digitalInName: ""
      property bool digitalInState: false
      property bool optional: false

      color: root.textColor
      font.strikeout: root.disabled
      text: (waitType == WaitBlockData.Sleep) ? qsTr("Sleep for %1s").arg(sleepTime) : getText(waitType)

      function getText(type) {
        if (type == WaitBlockData.Pause) {
          return optional ? qsTr("Optional Pause") : qsTr("Pause");
        } else if (type == WaitBlockData.Exit) {
          return qsTr("Exit");
        } else {
          var state = digitalInState ? qsTr("Hi") : qsTr("Lo");
          if (digitalInName !== "") {
            return qsTr("Wait For \"%1\" %2").arg(digitalInName).arg(state);
          } else {
            return qsTr("Wait For Digital In %1 %2").arg(digitalInNr).arg(state);
          }
        }
      }

      function setValues() {
        waitType = Number(blockData.get("wait_type"));
        sleepTime = Number(blockData.get("sleep_time"));
        digitalInNr = Number(blockData.get("digital_in_nr"));
        digitalInName = String(blockData.get("digital_in_name"));
        digitalInState = Boolean(blockData.get("digital_in_state"));
        optional = Boolean(blockData.get("optional"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: setComponent
    ItemText {
      id: item
      property int setType: 0
      property int digitalOutNr: 0
      property string digitalOutName: ""
      property bool digitalOutState: false

      color: root.textColor
      font.strikeout: root.disabled
      text: (setType === SetBlockData.SetDigitalOut) ? getDigitalOutText() : qsTr("Set")

      function getDigitalOutText() {
        var state = digitalOutState ? qsTr("High") : qsTr("Low");
        if (digitalOutName !== "") {
          return qsTr("Set \"%1\" %2").arg(digitalOutName).arg(state);
        } else {
          return qsTr("Set Digital Out %1 %2").arg(digitalOutNr).arg(state);
        }
      }

      function setValues() {
        setType = Number(blockData.get("set_type"));
        digitalOutNr = Number(blockData.get("digital_out_nr"));
        digitalOutName = String(blockData.get("digital_out_name"));
        digitalOutState = Boolean(blockData.get("digital_out_state"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: programComponent
    ItemText {
      id: item
      readonly property string type: blockData.type == "mainprogram" ? qsTr("Program") : qsTr("Subprogram")
      property string name: ""

      color: root.textColor
      font.strikeout: root.disabled
      text: qsTr("%1 - %2").arg(type).arg(name)

      function setValues() {
        name = String(blockData.get("name"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: callComponent
    ItemText {
      id: item
      property string name: ""

      color: root.textColor
      font.strikeout: root.disabled
      text: qsTr("Call %1()").arg(name)

      function setValues() {
        name = String(blockData.get("name"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: assignmentComponent
    ItemText {
      id: item
      property string name: ""
      property string operator: ""
      property string expression: ""

      color: root.textColor
      font.strikeout: root.disabled
      text: qsTr("Assign [ %1 %2 %3 ]").arg(name).arg(operator).arg(expression)

      function setValues() {
        name = String(blockData.get("name"));
        operator = String(blockData.get("operator"));
        expression = String(blockData.get("expression"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: frameComponent
    ItemText {
      id: item
      property int frameType: 0
      property string name: ""
      property string pose: ""
      property string position: ""
      property string orientation: ""
      readonly property string args: {
        var list = [];
        if (pose) {
          list.push(pose);
        }
        if (position) {
          list.push(qsTr("pos=%1").arg(position));
        }
        if (orientation) {
          list.push(qsTr("ori=%1").arg(orientation));
        }
        return list.join(", ");
      }

      color: root.textColor
      font.strikeout: root.disabled
      text: item.getText(item.frameType)

      function getText(frameType) {
        switch (frameType) {
        case FrameBlockData.ChangeUserFrame:
          return qsTr("Change user frame [%1]").arg(name);
        case FrameBlockData.ChangeToolFrame:
          return qsTr("Change tool frame [%1]").arg(name);
        default:
          return qsTr("Frame [ %1 ]").arg(args);
        }
      }

      function setValues() {
        frameType = Number(blockData.get("frame_type"));
        name = String(blockData.get("name"));
        pose = String(blockData.get("pose"));
        position = String(blockData.get("position"));
        orientation = String(blockData.get("orientation"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: commentComponent
    ItemText {
      id: item
      property string commentText: ""

      color: root.textColor
      font.strikeout: root.disabled
      font.italic: true
      text: commentText

      function setValues() {
        commentText = String(blockData.get("text"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }

  Component {
    id: actuateGripperComponent
    ItemText {
      id: item
      property double position: 0.0
      property double effort: 0.0
      property bool wait: false

      color: root.textColor
      font.strikeout: root.disabled
      text: {
        if (item.effort == 0) {
          return qsTr("Release gripper");
        } else if (item.position == 0) {
          return qsTr("Close gripper [%1% effort]").arg(item.effort);
        } else if (item.position == 100) {
          return qsTr("Open gripper [%1% effort]").arg(item.effort);
        } else {
          return qsTr("Actuate gripper [%1%, %2% effort]").arg(item.position).arg(item.effort);
        }
      }

      function setValues() {
        item.position = Number(blockData.get("position")) * 100;
        item.effort = Number(blockData.get("effort")) * 100;
        item.wait = Boolean(blockData.get("wait"));
      }

      Component.onCompleted: setValues()

      Connections {
        target: blockData
        function onDataChanged() {
          item.setValues();
        }
      }
    }
  }
}
