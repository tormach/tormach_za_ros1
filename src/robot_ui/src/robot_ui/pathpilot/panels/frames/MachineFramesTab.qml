import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers

FramesTabBase {
  id: root
  title: qsTr("Machine")

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin

    MachineFramesTableView {
      Layout.fillHeight: true
      Layout.fillWidth: true
      nodeModel: Handlers.state.machinetalk.nodeModel
    }
  }
}
