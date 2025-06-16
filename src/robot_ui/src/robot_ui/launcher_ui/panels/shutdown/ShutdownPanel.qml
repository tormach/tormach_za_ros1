import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import launcher_ui.logic 1.0

Item {
  id: root
  property RobotUILauncher robotLauncher

  ColumnLayout {
    id: statusPanel
    anchors.fill: parent
    spacing: Sizes.doubleSpacing

    VerticalFiller {
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("Shutting down...")
    }

    PathPilotBusyIndicator {
      Layout.alignment: Qt.AlignHCenter
    }

    VerticalFiller {
    }
  }
}
