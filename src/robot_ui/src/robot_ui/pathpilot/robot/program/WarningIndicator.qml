import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

Loader {
  id: root
  property var warnings
  active: warnings != null && warnings.length > 0
  sourceComponent: Component {
    Icon {
      icon: Icons.program.warning
      MouseArea {
        id: warningMouseArea
        anchors.fill: parent
        hoverEnabled: true
      }

      ToolTip {
        scale: Sizes.scale
        visible: warningMouseArea.containsMouse
        text: {
          var texts = [];
          for (var i = 0; i < root.warnings.length; ++i) {
            if (root.warnings[i] && root.warnings[i].message) {
              // Check if the warning and message are not null
              texts.push(root.warnings[i].message);
            } else {
              console.log("Warning at index " + i + " is null or undefined");
            }
          }
          return texts.join("\n");
        }
      }
    }
  }
}
