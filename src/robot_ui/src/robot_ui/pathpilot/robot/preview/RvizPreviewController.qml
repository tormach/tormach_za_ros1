import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers
import pathpilot.robot.preview

Rectangle {
  id: root
  property int mode: PreviewMode.Interactive
  color: Colors.black1
  readonly property QtObject _d: QtObject {
    id: d
    function updateMode() {
      if (!Handlers.preview) {
        return;
      }
      switch (root.mode) {
      case PreviewMode.Interactive:
        Handlers.preview.interactiveMode();
        break;
      case PreviewMode.View:
        Handlers.preview.viewMode();
        break;
      }
    }
  }

  ColumnLayout {
    anchors.centerIn: parent
    Layout.preferredWidth: 300
    spacing: Sizes.doubleSpacing

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      visible: !Handlers.preview.windowCaptured
      text: Handlers.preview.previewEnabled ? qsTr("Robot Preview loading...") : qsTr("Robot Preview disabled")
    }
  }

  onVisibleChanged: {
    if (visible) {
      d.updateMode();
    }
  }
  onModeChanged: d.updateMode()

  GlobalPositionController {
    id: positionController
    source: root
    target: Handlers.preview ? Handlers.preview.globalPositionObject : null
    active: root.visible
  }

  RvizPreviewVisualizationControls {
    id: rvizcontrols
    visible: root.visible && Handlers.preview.previewEnabled && positionController.active
    x: root.Window.window.x + Handlers.preview.globalPositionObject.target.x + Handlers.preview.globalPositionObject.target.width - rvizcontrols.width - Sizes.singleMargin
    y: root.Window.window.y + Handlers.preview.globalPositionObject.target.y + Sizes.singleMargin
    onVisibleChanged: {
      if (visible)
        root.Window.window.requestActivate();
    }
  }
}
