import QtQuick
import QtQuick.Window
import QtQuick.Controls
import pathpilot.core

TextArea {
  id: root
  objectName: "textArea"
  text: ""
  font.pixelSize: Fonts.controls.textField1
  font.family: Fonts.font2
  horizontalAlignment: Text.AlignLeft
  verticalAlignment: Text.AlignTop
  color: Colors.black1
  selectByMouse: true
  wrapMode: TextArea.Wrap

  background: Rectangle {
    implicitWidth: implicitHeight * 3
    implicitHeight: Sizes.controlHeight * 3
    radius: Sizes.smallRadius
    border.color: Colors.gray3
    border.width: Sizes.thinBorder
    color: enabled ? (root.activeFocus ? Colors.cyan1 : Colors.white1) : Colors.gray1
  }

  onActiveFocusChanged: {
    if (!focus) {
      deselect();
    }
  }

  onEditingFinished: {
    root.focus = false;
  }
}
