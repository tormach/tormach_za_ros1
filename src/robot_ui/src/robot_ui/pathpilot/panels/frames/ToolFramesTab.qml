import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.frame
import pathpilot.robot.frame.wizards
import pathpilot.handlers

FramesTabBase {
  id: root
  title: qsTr("Tool")

  readonly property QtObject _d: QtObject {
    id: d
    readonly property ToolFrames frames: Handlers.state.toolFrames

    function getSelectedFrameNames() {
      var names = [];
      for (var i = 0; i < tableView.selection.selectedIndexes.length; ++i) {
        var index = tableView.selection.selectedIndexes[i];
        names.push(tableView.model.data(index, FrameTableModel.NameRole));
      }
      return names;
    }

    function removeFrames() {
      var names = d.getSelectedFrameNames();
      tableView.clearSelection();
      for (var i = 0; i < names.length; ++i) {
        d.frames.deleteFrame(names[i]);
      }
    }

    function removeAllFrames() {
      d.frames.clearFrames();
    }

    function setFrame(name, frame, modelType) {
      d.frames.setFrame(name, frame, {
          "model_type": modelType
        });
    }

    function updateFrameUsingWizard() {
      Config.user.custom.frameName = d.getSelectedFrameNames()[0];
      Handlers.app.startWizardProgram(FrameWizards.toolFrameWizard, Panels.FramesPanel);
    }

    function updateFrameOrientation(a, b, c) {
      var name = d.getSelectedFrameNames()[0];
      var pose = d.frames.getFramePose(name);
      pose[3] = a;
      pose[4] = b;
      pose[5] = c;
      d.frames.setFrame(name, pose);
    }
  }

  NewFramePopup {
    id: newFramePopup
    frames: d.frames
    defaultPrefix: "tool_"

    onAccepted: function (name) {
      modelTypePopup.name = name;
      modelTypePopup.pose = [0, 0, 0, 0, 0, 0];
      modelTypePopup.applyFrame = true;
      modelTypePopup.modelType = "";
      modelTypePopup.open();
    }
  }

  RemoveFramePopup {
    id: removeFramePopup
    count: tableView.selectedRows.length
    onAccepted: d.removeFrames()
  }

  ModelTypePopup {
    id: modelTypePopup
    frames: d.frames.defaultFrames
    onAccepted: {
      d.setFrame(modelTypePopup.name, modelTypePopup.pose, modelTypePopup.modelType);
    }
  }

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin

    FrameTableView {
      id: tableView
      Layout.fillHeight: true
      Layout.fillWidth: true
      frames: d.frames
      modelTypeVisible: true

      onUpdateFrameModelTypeRequested: function (name, pose, modelType) {
        modelTypePopup.name = name;
        modelTypePopup.pose = pose;
        modelTypePopup.modelType = modelType;
        modelTypePopup.applyFrame = false;
        modelTypePopup.open();
      }
    }

    ColumnLayout {
      Layout.fillWidth: false
      Layout.preferredWidth: 200

      PathPilotButton {
        Layout.fillWidth: true
        text: qsTr("Add Frame")
        onClicked: {
          newFramePopup.open();
        }
      }

      PathPilotButton {
        Layout.fillWidth: true
        text: tableView.selectedRows.length > 1 ? qsTr("Remove Frames") : qsTr("Remove Frame")
        enabled: tableView.selectedRows.length > 0
        onClicked: removeFramePopup.open()
        PathPilotToolTip {
          itemId: "msg_remove_frame"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }

      VerticalFiller {
      }

      PathPilotButton {
        Layout.fillWidth: true
        Layout.preferredHeight: 100
        enabled: tableView.selectedRows.length == 1
        text: qsTr("Update frame\nusing\nWizard")
        horizontalAlignment: Text.AlignHCenter
        onClicked: d.updateFrameUsingWizard()
        PathPilotToolTip {
          itemId: "msg_update_frame_from_current_position"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }

      PathPilotButton {
        Layout.fillWidth: true
        Layout.preferredHeight: 100
        enabled: tableView.selectedRows.length == 1
        text: qsTr("Frame orientation\nWizard")
        horizontalAlignment: Text.AlignHCenter
        onClicked: markerOperationsPopup.open()
        PathPilotToolTip {
          itemId: "msg_update_frame_using_wizard"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }

      ToolFrameOrientationPopup {
        id: markerOperationsPopup
        onSetToolOrientation: function (a, b, c) {
          d.updateFrameOrientation(a, b, c);
        }
      }

      VerticalFiller {
      }
    }
  }
}
