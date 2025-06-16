import QtQuick
import QtQuick.Window
import pathpilot.core
import pathpilot.controls

PathPilotIconButton {
  id: root
  implicitWidth: 100
  text: qsTr("Back")
  icon_: Icons.filepanel.back

  PathPilotToolTip {
    itemId: "msg_back"
  }
}
