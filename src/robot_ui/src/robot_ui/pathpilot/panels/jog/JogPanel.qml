import QtQuick
import QtQuick.Window
import pathpilot.core
import pathpilot.handlers

JogPanelBase {
  id: root
  title: qsTr("Jog")
  enabled: Handlers.app.jogAllowed

  JogPanelControl {
    anchors.fill: parent
    anchors.margins: Sizes.doubleSpacing
  }
}
