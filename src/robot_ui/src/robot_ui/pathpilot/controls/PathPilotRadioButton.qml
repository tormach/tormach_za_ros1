import QtQuick
import QtQuick.Window
import QtQuick.Controls
import pathpilot.core

RadioButton {
  id: root
  font.family: Fonts.font1
  font.pixelSize: Fonts.controls.radioButton1
  implicitHeight: Sizes.controlHeight
  leftPadding: 0

  indicator: Rectangle {
    implicitWidth: 25
    implicitHeight: implicitWidth
    x: root.leftPadding
    y: parent.height / 2 - height / 2
    radius: width / 2
    color: enabled ? Colors.white1 : Colors.gray1
    border.color: root.down ? Colors.cyan1 : Colors.green2

    Rectangle {
      width: parent.width * 0.6
      height: width
      x: (parent.width - width) / 2
      y: x
      radius: width / 2
      color: root.down ? Colors.cyan1 : Colors.green2
      visible: root.checked
    }
  }

  contentItem: Text {
    verticalAlignment: Text.AlignVCenter
    text: root.text
    font: root.font
    color: enabled ? (root.down ? Colors.cyan1 : Colors.white2) : Colors.gray1
    leftPadding: root.indicator.width + root.spacing
  }
}
