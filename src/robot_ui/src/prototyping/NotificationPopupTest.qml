import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program.notification
import pathpilot.robot.program

ScaledTestBase {
  id: root

  NotificationPopup {
    id: notificationPopup
    message: "Hello World!"

    //Component.onCompleted: open()
    onAccepted: close()
  }

  NotificationPopup {
    id: warningPopup
    message: "Honk honk, something is weird."
    notifyType: NotificationMessage.Warning

    onAborted: close()
  }

  NotificationPopup {
    id: errorPopup
    message: "Puff Zack Kaboom!??!"
    notifyType: NotificationMessage.Error

    onAborted: close()
  }

  NotificationPopup {
    id: userInputPopup
    message: "Please enter a number"
    notifyType: NotificationMessage.UserInput

    onAccepted: {
      console.log(userInput);
      close();
    }
    onAborted: close()
  }

  Row {
    anchors.centerIn: parent
    spacing: Sizes.singleSpacing

    PathPilotButton {
      implicitWidth: 180
      text: "Show Notification"
      onClicked: notificationPopup.open()
    }

    PathPilotButton {
      implicitWidth: 180
      text: "Show Warning"
      onClicked: warningPopup.open()
    }

    PathPilotButton {
      implicitWidth: 180
      text: "Show Error"
      onClicked: errorPopup.open()
    }

    PathPilotButton {
      implicitWidth: 180
      text: "User Input"
      onClicked: {
        userInputPopup.userInput = "23";
        userInputPopup.open();
      }
    }
  }
}
