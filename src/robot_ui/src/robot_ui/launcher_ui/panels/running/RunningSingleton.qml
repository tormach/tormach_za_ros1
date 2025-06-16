pragma Singleton
import QtQuick

Item {
  id: root

  property bool running: false

  function start() {
    d.change(true);
  }

  function stop() {
    d.change(false);
  }

  readonly property QtObject d: QtObject {
    function change(input) {
      root.running = input;
    }
  }
}
