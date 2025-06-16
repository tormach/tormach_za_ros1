import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers

PathPilotPanel {
  id: root

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleSpacing
    spacing: Sizes.doubleSpacing

    PathPilotLabel {
      text: qsTr("Interpreter")
    }

    Spacer {
      Layout.fillWidth: true
    }

    PathPilotButton {
      Layout.fillWidth: true
      text: qsTr("Reload")
      enabled: Handlers.program.reloadInterpreterAllowed

      onClicked: Handlers.program.reloadInterpreter()

      PathPilotToolTip {
        itemId: "msg_reload"
        sidePosition: PathPilotToolTip.Side.Left
      }
    }

    VerticalFiller {
    }
  }
}
