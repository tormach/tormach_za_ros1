import QtQuick
import pathpilot.core
import pathpilot.controls
import pathpilot.logging

ScaledTestBase {
  id: root

  LogMessagePopup {
    id: logMessagePopup
    message: "This is a log message."
    extendedInfo: "This is an extended info message.
It can be used to provide more information about the log message.
It can also be used to provide a link to a help page.
There can be multiple lines of text.
And even more stuff.
"
  }

  Row {
    anchors.centerIn: parent
    spacing: Sizes.singleSpacing

    PathPilotButton {
      implicitWidth: 180
      text: "Log Message"
      onClicked: logMessagePopup.open()
    }
  }

  Component.onCompleted: {
    logMessagePopup.open();
  }
}
