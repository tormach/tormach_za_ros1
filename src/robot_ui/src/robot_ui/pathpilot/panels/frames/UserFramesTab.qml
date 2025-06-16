import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.frame
import pathpilot.robot.frame.wizards
import pathpilot.handlers

FramesTabBase {
  id: root
  title: qsTr("User")

  readonly property QtObject _d: QtObject {
    id: d
    readonly property UserFrames frames: Handlers.state.userFrames
    property bool addFromCurrent: false

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

    function updateFrameFromCurrent() {
      var name = d.getSelectedFrameNames()[0];
      d.frames.setFrameFromCurrent(name);
    }

    function updateFrameUsingWizard() {
      Config.user.custom.frameName = d.getSelectedFrameNames()[0];
      Handlers.app.startWizardProgram(FrameWizards.userFrameWizard, Panels.FramesPanel);
    }
  }

  NewFramePopup {
    id: newFramePopup
    frames: d.frames

    onAccepted: function (name) {
      if (d.addFromCurrent)
        d.frames.setFrameFromCurrent(name);
      else
        d.frames.setFrame(name, [0, 0, 0, 0, 0, 0]);
    }
  }

  RemoveFramePopup {
    id: removeFramePopup
    count: tableView.selectedRows.length
    onAccepted: d.removeFrames()
  }

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin

    FrameTableView {
      id: tableView
      Layout.fillHeight: true
      Layout.fillWidth: true
      frames: d.frames
    }

    ColumnLayout {
      Layout.fillWidth: false
      Layout.preferredWidth: 200

      PathPilotButton {
        Layout.fillWidth: true
        text: qsTr("Add Frame")
        onClicked: {
          d.addFromCurrent = false;
          newFramePopup.open();
        }

        PathPilotToolTip {
          itemId: "add_user_frame"
          sidePosition: PathPilotToolTip.Side.Left
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
        text: qsTr("Update frame\nfrom current\nPosition")
        horizontalAlignment: Text.AlignHCenter
        onClicked: d.updateFrameFromCurrent()

        PathPilotToolTip {
          itemId: "msg_update_frame_from_current_position"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }

      PathPilotButton {
        Layout.fillWidth: true
        Layout.preferredHeight: 100
        enabled: tableView.selectedRows.length == 1
        text: qsTr("Update frame\nusing\nWizard")
        horizontalAlignment: Text.AlignHCenter
        onClicked: d.updateFrameUsingWizard()
        PathPilotToolTip {
          itemId: "msg_update_frame_using_wizard"
          sidePosition: PathPilotToolTip.Side.Left
        }
      }

      VerticalFiller {
      }
    }
  }
}
