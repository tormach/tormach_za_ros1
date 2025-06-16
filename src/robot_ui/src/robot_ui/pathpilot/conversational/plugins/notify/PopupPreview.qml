import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

Item {
  id: root
  default property alias containerData: container.data

  Rectangle {
    implicitWidth: outerContainer.implicitWidth + Sizes.doubleMargin * 2
    implicitHeight: outerContainer.implicitHeight + Sizes.doubleMargin * 2
    anchors.centerIn: parent
    color: Colors.black1

    PathPilotBackgroundImage {
      anchors.fill: parent
      anchors.margins: Sizes.halfMargin
    }

    ColumnLayout {
      id: outerContainer
      anchors.fill: parent
      anchors.margins: Sizes.doubleMargin
      spacing: Sizes.singleSpacing

      VerticalFiller {
      }

      ColumnLayout {
        id: container
        Layout.fillWidth: true
        Layout.fillHeight: true
        spacing: Sizes.doubleSpacing
      }
    }
  }
}
