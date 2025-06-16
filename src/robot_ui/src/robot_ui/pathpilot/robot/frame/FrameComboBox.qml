import QtQuick
import pathpilot.controls
import pathpilot.robot.frame

PathPilotComboBox {
  id: root
  property QtObject frames: null // Frames type, prevent type conflict
  property string defaultFrameName: "world"
  property var frameModel: [defaultFrameName].concat(frames.frameNames)

  readonly property QtObject _d: QtObject {
    id: d
    property bool remoteUpdate: false

    function activateFrame(name) {
      if (d.remoteUpdate) {
        return;
      }
      if (name == defaultFrameName) {
        name = "";
      }
      root.frames.activeFrame = name;
    }
  }

  onFrameModelChanged: {
    d.remoteUpdate = true;
    root.model = root.frameModel;
    d.remoteUpdate = false;
  }

  onModelChanged: root.selectByText(root.frames.activeFrame)
  onCurrentIndexChanged: d.activateFrame(model[currentIndex])

  Connections {
    target: root.frames

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onActiveFrameChanged() {
      root.selectByText(root.frames.activeFrame);
    }
  }
}
