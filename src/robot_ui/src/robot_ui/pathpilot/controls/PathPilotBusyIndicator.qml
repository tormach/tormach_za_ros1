import QtQuick
import QtQuick.Controls
import pathpilot.core

BusyIndicator {
  id: control
  implicitHeight: implicitWidth

  readonly property QtObject d: QtObject {
    property int current: 8
    property int count: 10
    function increment() {
      if (current < (count - 1)) {
        current += 1;
      } else {
        current = 0;
      }
    }
  }

  Timer {
    id: timer
    interval: 150
    running: control.running && control.visible
    repeat: true
    onTriggered: d.increment()
  }

  contentItem: Item {
    id: rectangle
    implicitWidth: 64
    implicitHeight: 64

    Repeater {
      id: repeater
      model: d.count

      Rectangle {
        property bool selected: index === d.current
        property bool ticked: true

        width: rectangle.width * (selected ? 0.22 : 0.15)
        height: width
        radius: width / 2
        color: ticked ? "transparent" : Colors.green2
        border.width: ticked ? 1 : 0
        border.color: Colors.green2
        x: (rectangle.width - height) / 2 + rectangle.width / 2.5 * Math.cos((index / d.count) * 2 * Math.PI)
        y: (rectangle.height - width) / 2 + rectangle.height / 2.5 * Math.sin((index / d.count) * 2 * Math.PI)

        onSelectedChanged: if (selected) {
          ticked = !ticked;
        }
      }
    }
  }
}
