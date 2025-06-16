import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.panels.left
import pathpilot.panels.center
import pathpilot.panels.right

Item {
  id: root

  PathPilotBackgroundImage {
    anchors.fill: parent
  }

  MainNotebook {
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: rowLayout1.top
    anchors.margins: Sizes.singleMargin
  }

  RowLayout {
    id: rowLayout1
    height: parent.height * 0.38
    anchors.right: parent.right
    anchors.left: parent.left
    anchors.bottom: parent.bottom
    anchors.margins: Sizes.singleMargin

    LeftPanel {
      id: leftPanel
      Layout.fillHeight: true
      Layout.fillWidth: true
      Layout.minimumWidth: root.width * 0.3
    }

    CenterPanel {
      id: centerPanel
      Layout.fillHeight: true
      Layout.fillWidth: true
      Layout.minimumWidth: root.width * 0.3
    }

    RightPanel {
      id: rightPanel
      Layout.fillHeight: true
      Layout.fillWidth: true
      Layout.minimumWidth: root.width * 0.3
    }
  }
}
