import QtQuick
import QtQuick.Layouts
import pathpilot.controls

GridLayout {
  id: root
  property bool editBlockMode: false
  property var blockData: {
    "valid": false
  }
  property bool addUpdateEnabled: true
  property int minimumLevel: 1

  property alias addButton: addButton
  property alias finishEditingButton: finishEditingButton
  property alias cancelButton: cancelButton

  property alias addButtonTooltipId: addButtonTooltip.itemId
  property alias finishEditingButtonTooltipId: addButtonTooltip.itemId
  property alias cancelButtonTooltipId: addButtonTooltip.itemId

  signal addClicked(string uuid)
  signal updateClicked
  signal cancelClicked
  Layout.fillWidth: false
  rows: 1

  PathPilotButton {
    id: addButton
    Layout.fillWidth: true
    Layout.preferredWidth: 180
    visible: !d.editBlockMode
    enabled: root.addUpdateEnabled
    text: qsTr("Add to program")
    onClicked: root.addClicked((blockData.valid && (blockData.level > root.minimumLevel)) ? blockData.uuid : "")

    PathPilotToolTip {
      id: addButtonTooltip
      itemId: "msg_add_to_program"
      sidePosition: PathPilotToolTip.Side.Left
    }
  }

  PathPilotButton {
    id: finishEditingButton
    Layout.fillWidth: true
    Layout.preferredWidth: 150
    visible: d.editBlockMode
    enabled: root.addUpdateEnabled
    text: qsTr("Finish Editing")
    onClicked: root.updateClicked()

    PathPilotToolTip {
      id: finishEditingButtonTooltip
      sidePosition: PathPilotToolTip.Side.Left
    }
  }

  PathPilotButton {
    id: cancelButton
    Layout.fillWidth: true
    Layout.preferredWidth: 100
    visible: d.editBlockMode
    text: qsTr("Cancel")
    onClicked: root.cancelClicked()

    PathPilotToolTip {
      id: cancelButtonTooltip
      sidePosition: PathPilotToolTip.Side.Left
    }
  }
}
