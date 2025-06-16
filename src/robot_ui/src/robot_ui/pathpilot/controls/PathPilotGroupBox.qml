import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls

PathPilotPanel {
  default property alias data_: container.data
  property alias title: titleLabel.text

  implicitWidth: container.implicitWidth + Sizes.singleMargin * 2
  implicitHeight: container.implicitHeight + Sizes.singleMargin * 2

  ColumnLayout {
    id: container
    anchors.centerIn: parent
    spacing: Sizes.singleSpacing

    PathPilotLabel {
      id: titleLabel
      Layout.fillWidth: true
    }
  }
}
