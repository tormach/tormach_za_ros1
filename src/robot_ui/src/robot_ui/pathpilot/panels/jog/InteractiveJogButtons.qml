import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.robot.jog
import pathpilot.handlers

ColumnLayout {
  id: root
  property alias markerOpsChecked: markerOpsButton.checked

  readonly property QtObject _d: QtObject {
    id: d
    readonly property InteractiveMarker interactiveMarker: Handlers.jog.interactiveMarker
    readonly property InteractiveMove interactiveMove: Handlers.jog.interactiveMove
    readonly property CartesianState cartesianState: Handlers.state.cartesianState
  }

  onVisibleChanged: {
    if (root.visible && !d.interactiveMarker.valid) {
      var pose = d.cartesianState.worldPose.copy(root);
      d.interactiveMarker.pose.orientation = pose.orientation;
      d.interactiveMarker.pose.position = pose.position;
    }
  }

  PathPilotButton {
    Layout.fillHeight: true
    Layout.preferredWidth: 200
    text: qsTr("Hold To\nMove To Marker")
    horizontalAlignment: Text.AlignHCenter
    enabled: d.interactiveMarker.valid && d.interactiveMove.isReachable

    onPressed: {
      Handlers.app.lockPanel(true);
      d.interactiveMove.moveToPose(d.interactiveMarker.pose.toEulerAngles());
    }
    onReleased: {
      d.interactiveMove.stop();
      Handlers.app.lockPanel(false);
    }

    PathPilotToolTip {
      itemId: "msg_hold_to_move_to_marker"
    }
  }

  PathPilotToggleButton {
    id: markerOpsButton
    Layout.fillHeight: true
    Layout.preferredWidth: 200
    checked: false
    propertyText2: qsTr("Marker Ops")
    propertyText1: qsTr("Cartesian Jog")
    propertyHorizontalAlignment: Text.AlignHCenter
    labelMargin: Sizes.doubleMargin
    propertyFont.pixelSize: Fonts.jogPanel.size3

    PathPilotToolTip {
      itemId: "msg_cartesian_jog_marke"
    }
  }
}
