import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers

PathPilotButton {
  id: root
  implicitHeight: 35
  implicitWidth: 80
  labelMargin: 2
  font.pixelSize: Fonts.exitButton.size1
  text: qsTr("Exit")
  onClicked: {
    Handlers.conversational.commitChanges(exitPopup.open, qsTr("exiting PathPilot"));
  }

  PathPilotPopup {
    id: exitPopup

    PathPilotLabel {
      text: qsTr("E-stop the robot before proceeding.<br><br>Click OK to shut down the control computer.")
      horizontalAlignment: Text.AlignLeft
      font.family: Fonts.font2
      font.pixelSize: Fonts.exitButton.size2
      font.bold: true
    }

    RowLayout {
      HorizontalFiller {
      }

      PathPilotButton {
        id: cancelButton
        text: qsTr("Cancel")
        onClicked: exitPopup.close()
      }

      PathPilotButton {
        id: okButton
        text: qsTr("OK")
        labelColor: Colors.red1
        onClicked: Qt.exit(0)
      }
    }
  }

  PathPilotToolTip {
    itemId: "msg_exit"
    sidePosition: PathPilotToolTip.Side.Left
  }
}
