import QtQuick
import QtQuick.Controls
import QtQuick.Controls as C1
import QtQuick.Layouts
import QtQuick.Window
import QtQml.Models
import pathpilot.core
import pathpilot.panels.main
import pathpilot.robot.program
import pathpilot.development

UnscaledTestBase {
  id: root

  QtObject {
    id: d
    readonly property string programPath: DevelopmentPaths.programPath + "/example_program6.py"
  }

  ProgramReader {
    id: reader
    path: d.programPath
  }

  ProgramCodeTreeModel {
    id: programModel
    program: reader.program
  }

  ItemSelectionModel {
    // Note: without the selection model, we get crashes on remove
    id: itemSelectionModel
    model: programModel
  }

  ProgramCodeTreeView {
    anchors.fill: parent
    anchors.margins: Sizes.doubleMargin
    model: programModel
    selection: itemSelectionModel
  }
}
