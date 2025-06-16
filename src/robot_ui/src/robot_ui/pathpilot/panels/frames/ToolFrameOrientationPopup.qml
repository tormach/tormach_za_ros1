import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers
import pathpilot.panels.jog

PathPilotPopup {
  id: root
  signal setToolOrientation(double a, double b, double c)
  width: 450

  onVisibleChanged: {
    if (visible) {
      markerOperations.currentPose.orientation = Handlers.state.cartesianState.worldPose.orientation;
    }
  }

  MarkerOperations {
    id: markerOperations
    inverse: true
  }

  RowLayout {
    HorizontalFiller {
    }

    PathPilotButton {
      id: cancelButton
      text: qsTr("Cancel")
      onClicked: root.close()
    }

    PathPilotButton {
      id: okButton
      text: qsTr("OK")
      onClicked: {
        root.close();
        root.setToolOrientation(markerOperations.a, markerOperations.b, markerOperations.c);
      }
    }
  }
}
