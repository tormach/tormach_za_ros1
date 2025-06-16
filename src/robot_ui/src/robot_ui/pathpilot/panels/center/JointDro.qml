import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

RowLayout {
  id: root
  property string jointName: "J1"
  property double jointPosition: 0.0
  property int decimals: 4

  QtObject {
    id: d
    readonly property double threshold: Math.pow(10, -root.decimals)
    readonly property string zeros: "0." + "0".repeat(root.decimals)

    // JS toFixed may return -0.0000, we always want 0.0000
    function toFixed(value: double) {
      if (Math.abs(value) < d.threshold) {
        return d.zeros;
      } else {
        return value.toFixed(root.decimals);
      }
    }
  }

  PathPilotLabel {
    id: nameLabel
    Layout.fillWidth: false
    Layout.fillHeight: true
    text: root.jointName
    font.pixelSize: Fonts.jointPositionControl.size1
  }

  TextInput {
    id: jointPositionLabel
    Layout.fillWidth: true
    Layout.fillHeight: true
    readOnly: true
    selectByMouse: true
    text: d.toFixed(root.jointPosition)
    font.family: Fonts.font2
    font.pixelSize: Fonts.jointPositionControl.size3
    color: Colors.blue2
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
  }
}
