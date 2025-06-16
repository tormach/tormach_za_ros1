import QtQuick
import QtQuick.Window
import pathpilot.core
import pathpilot.controls

PathPilotIconButton {
  id: root
  text: qsTr("Home")

  icon_: Icons.filepanel.home

  PathPilotToolTip {
    itemId: "msg_home"
  }
}
