import QtQuick
import QtQuick.Window
import pathpilot.panels.jog

NotebookTestBase {
  id: root

  JogPanel {
    id: jogPanel
    anchors.fill: parent
  }
}
