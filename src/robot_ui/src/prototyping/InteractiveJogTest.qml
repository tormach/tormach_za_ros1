import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.preview
import pathpilot.panels.center
import pathpilot.robot
import pathpilot.robot.jog
import pathpilot.panels.jog

ScaleContainer {
  id: root

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin

    RvizPreviewController {
      id: controller
      Layout.fillWidth: true
      Layout.fillHeight: true
      mode: PreviewMode.View
    }

    MarkerOperations {
      id: markerOperations
    }
  }
}
