import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.machinetalk
import pathpilot.file
import pathpilot.panels.settings

UnscaledTestBase {
  id: root

  MachinetalkInstanceListModel {
    id: instanceModel
  }

  PathPilotInstanceSelection {
    id: instanceSelection
    anchors.fill: parent
    anchors.margins: Sizes.doubleSpacing
    model: instanceModel
  }
}
