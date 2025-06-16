import QtQuick
import QtQuick.Window
import QtQuick.Controls
import pathpilot.core

TextField {
  id: root
  property bool error: !root.acceptableInput
  objectName: "textField"

  implicitWidth: implicitHeight * 5
  implicitHeight: Sizes.controlHeight
  rightPadding: 5
  leftPadding: 5
  padding: 1
  text: ""
  font.pixelSize: Fonts.controls.textField1
  font.family: Fonts.font2
  horizontalAlignment: Text.AlignHCenter
  verticalAlignment: Text.AlignVCenter
  color: error ? Colors.yellow1 : Colors.black1
  selectByMouse: true

  background: Rectangle {
    radius: Sizes.smallRadius
    border.color: Colors.gray3
    border.width: Sizes.thinBorder
    color: enabled ? (error ? Colors.red1 : (root.activeFocus ? Colors.cyan1 : Colors.white1)) : Colors.gray1
  }

  onActiveFocusChanged: {
    if (focus) {
      selectAll();
    } else {
      deselect();
    }
  }
}
