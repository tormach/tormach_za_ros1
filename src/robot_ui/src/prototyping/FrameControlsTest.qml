import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.frame
import pathpilot.handlers

UnscaledTestBase {
  id: root

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin

    FrameComboBox {
      id: frameCombo
      Layout.fillWidth: true
      frames: Handlers.state.userFrames
    }

    RowLayout {

      FrameTableView {
        id: tableView
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.preferredWidth: 500
        frames: Handlers.state.userFrames
      }

      FrameTableView2 {
        id: tableView2
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.preferredWidth: 500
        frames: Handlers.state.userFrames
        modelTypeVisible: true
      }
    }
  }
}
