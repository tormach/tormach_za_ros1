import QtQuick
import QtQuick.Window

Rectangle {
  id: main

  /*! This property holds the led's current value.

    The default value is \c{false}.
  */
  property bool value: false

  /*! This property inverts the polarity of the led.

    The default value is \c{false}.
  */
  property bool invert: false

  /*! This property holds the led's active color.

    The default value is \c{red}.
  */
  property color activeColor: "red"

  /*! This property holds the led's off color.

    The default value is \c{darkGrey}.
  */
  property color offColor: "black"

  /*! This property holds whether the led should blink or not.

    The default value is \c{false}.
  */
  property bool blink: false

  /*! This property holds the blink interval of the led in ms when \l blink is set to \c true.

    The default value is \c{false}.
  */
  property int blinkInterval: 500

  /*! This property holds whether the led should have a small "shine" or not.

    The default value is \c{true}.
  */
  property bool shine: true

  width: 30
  height: 30
  implicitWidth: 30
  implicitHeight: 30
  border.width: 2
  radius: width / 2
  border.color: "black"
  color: ((value ^ invert) && (helpItem.blinkHelper || !blink)) ? activeColor : offColor
  opacity: enabled ? 1.0 : 0.3

  Rectangle {
    x: parent.width * 0.15
    y: parent.width * 0.15
    width: parent.width * 0.4
    height: width
    radius: width / 2
    color: "white"
    opacity: 0.4
    visible: main.shine
  }

  Timer {
    id: blinkTimer
    running: blink
    repeat: true
    interval: blinkInterval
    onTriggered: helpItem.blinkHelper = !helpItem.blinkHelper
  }

  QtObject {
    id: helpItem
    property bool blinkHelper: true
  }
}
