import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers
import pathpilot.robot.program
import pathpilot.robot.program.blocks

RowLayout {
  QtObject {
    id: d
    readonly property var subProgramNames: blockData.quickcallableSubProgramNames
    property var activeSubProgram: subProgramNames.length > 0 ? subProgramNames[0] : ""
  }

  SubProgramBlockData {
    id: blockData
    program: Handlers.conversational.program
  }

  PathPilotComboBox {
    id: runSubProgramComboBox
    Layout.fillWidth: true
    enabled: d.subProgramNames.length > 0
    model: d.subProgramNames
    editable: false
    onActivated: function (index) {
      d.activeSubProgram = d.subProgramNames[index];
    }
  }

  PathPilotButton {
    id: runSubProgramBtn
    enabled: d.subProgramNames.length > 0
    implicitWidth: 200
    text: qsTr("Run Subprogram")
    onClicked: function () {
      Handlers.program.startSubprogram(d.activeSubProgram);
    }
    PathPilotToolTip {
      itemId: "run_subprogram"
      sidePosition: PathPilotToolTip.Side.Left
    }
  }
}
