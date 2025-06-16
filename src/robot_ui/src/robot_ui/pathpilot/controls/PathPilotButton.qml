import QtQuick
import QtQuick.Window
import QtQuick.Controls
import pathpilot.core
import pathpilot.controls

Button {
  id: root
  property bool blinkEnabled: highlighted
  property bool blink: false
  property int blinkInterval: 500

  property alias horizontalAlignment: textLabel.horizontalAlignment
  property int labelMargin: Sizes.singleMargin

  property color blinkColor: Colors.red1
  property color shadowColor: Colors.gray2
  property color labelColor: Colors.white2
  property color disabledColor: Colors.gray1
  font.family: Fonts.font1
  font.pixelSize: Fonts.controls.button1
  opacity: enabled ? 1.0 : 0.7

  QtObject {
    id: d
    property bool blinkHelper: true
    property bool keyPressed: false
    property bool buttonReleased: true

    readonly property Timer releaseTimer: Timer {
      repeat: false
      onTriggered: root.onReleased()
      interval: 1
    }
  }

  contentItem: Item {
    Text {
      id: textLabel
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.verticalCenter: parent.verticalCenter
      anchors.verticalCenterOffset: -1 // small optimization
      anchors.leftMargin: root.labelMargin
      anchors.rightMargin: anchors.leftMargin
      horizontalAlignment: Text.AlignLeft
      font: root.font
      text: root.text
      color: !root.enabled ? root.disabledColor : (root.blink && d.blinkHelper) ? root.blinkColor : root.labelColor
      style: Text.Outline
      styleColor: root.shadowColor
    }
  }

  background: Item {
    implicitWidth: implicitHeight * 3
    implicitHeight: Sizes.controlHeight

    BorderImage {
      id: borderImage
      anchors.fill: parent
      source: (root.pressed || d.keyPressed) ? Icons.buttons.pressed : Icons.buttons.normal
      border.left: 9
      border.right: 9
      border.top: 9
      border.bottom: 9
    }
  }

  Keys.enabled: root.focus
  Keys.onPressed: function (event) {
    if ([Qt.Key_Return, Qt.Key_Enter].includes(event.key)) {
      if (!event.isAutoRepeat) {
        d.keyPressed = true;
      }
      root.onPressed();
    }
  }
  Keys.onReleased: function (event) {
    if ([Qt.Key_Return, Qt.Key_Enter].includes(event.key)) {
      if (!event.isAutoRepeat) {
        d.keyPressed = false;
      }
      if (root.checkable) {
        root.checked = !root.checked;
      }
      root.onReleased();
      root.onClicked();
    }
  }

  onReleased: {
    d.releaseTimer.stop();
  }

  onPressedChanged: {
    if (!pressed) {
      d.releaseTimer.start(); // workaround for cases where onReleased is not triggered (moving cursor out of button area)
    }
  }

  Timer {
    running: root.blink
    repeat: true
    interval: root.blinkInterval
    onTriggered: d.blinkHelper = !d.blinkHelper
  }
}
