import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

Loader {
  id: root
  property bool isCopySource: false
  property bool isCutSource: false
  active: isCopySource || isCutSource
  sourceComponent: Component {
    Icon {
      icon: root.isCopySource ? Icons.program.blockCopy : Icons.program.blockCut

      MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
      }

      ToolTip {
        scale: Sizes.scale
        visible: mouseArea.containsMouse
        text: root.isCopySource ? qsTr("Copy source") : qsTr("Cut source")
      }
    }
  }
}
