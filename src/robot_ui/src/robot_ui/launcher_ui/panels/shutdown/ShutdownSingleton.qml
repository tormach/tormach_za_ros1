pragma Singleton
import QtQuick
import QtQuick.Controls
import pathpilot.core
import pathpilot.controls
import launcher_ui.logic 1.0

Item {
  id: root
  signal shutdownRequested
  signal requestShutdown

  LauncherControl {
    id: launcherControl
  }

  onRequestShutdown: {
    d.shutdown();
  }

  readonly property QtObject d: QtObject {
    function shutdown() {
      root.shutdownRequested();
      launcherControl.shutdown("UI 'shutdown' requested");
    }
  }
}
