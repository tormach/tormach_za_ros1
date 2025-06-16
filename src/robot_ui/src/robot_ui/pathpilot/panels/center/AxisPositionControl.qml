import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

RowLayout {
  id: root
  property int axis: 0
  property string axisName: "X"
  property double axisPosition: 0.0
  property int decimals: 4
  property bool readOnly: false

  readonly property bool buttonHovered: zeroButton.hovered

  signal touchOff(double position)
  signal reset

  PathPilotDelayButton {
    id: zeroButton
    Layout.fillHeight: true
    Layout.fillWidth: false
    Layout.preferredWidth: height * 1.2
    text: root.axisName
    horizontalAlignment: Text.AlignHCenter
    font.pixelSize: Fonts.jointPositionControl.size1
    enabled: !root.readOnly

    onActivated: {
      root.touchOff(0.0);
    }

    Text {
      id: textLabel
      anchors.left: parent.left
      anchors.top: parent.top
      anchors.bottom: parent.bottom
      anchors.margins: parent.height * 0.2
      verticalAlignment: Text.AlignVCenter
      font.family: Fonts.font1
      font.pixelSize: parent.height * 0.16
      font.weight: Font.Bold
      lineHeight: 0.88
      text: "Z\nE\nR\nO"
      color: !parent.enabled ? parent.disabledColor : (parent.blink && d.blinkHelper) ? parent.blinkColor : parent.labelColor
      style: Text.Outline
      styleColor: parent.shadowColor
    }

    MouseArea {
      id: rightClickArea
      anchors.fill: parent
      acceptedButtons: Qt.RightButton
      onClicked: root.reset()
    }
  }

  PathPilotDroField {
    id: textField
    Layout.fillWidth: true
    Layout.fillHeight: true
    decimals: root.decimals
    readOnly: root.readOnly
    font.pixelSize: Fonts.centerPanel.size3

    onValueUpdated: function (value) {
      root.touchOff(value);
    }

    Binding {
      textField.value: root.axisPosition
    }
  }
}
