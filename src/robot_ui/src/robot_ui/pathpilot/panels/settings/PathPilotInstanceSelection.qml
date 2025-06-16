import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.file

PathPilotPanel {
  id: root
  Layout.preferredHeight: 340
  Layout.preferredWidth: 300
  property alias model: listView.model

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleSpacing
    anchors.topMargin: Sizes.singleSpacing

    ListView {
      id: listView
      Layout.fillHeight: true
      Layout.fillWidth: true
      clip: true
      currentIndex: -1

      section.property: "selected"
      section.criteria: ViewSection.FullString
      section.delegate: Item {
        anchors.left: parent.left
        anchors.right: parent.right
        height: 35

        PathPilotLabel {
          anchors.fill: parent
          text: section == "true" ? qsTr("Selected Machines") : qsTr("Discovered Machines")
          elide: Text.ElideRight
          horizontalAlignment: Text.AlignLeft
        }

        Rectangle {
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.bottom: parent.bottom
          height: 1
          color: Colors.gray1
        }
      }

      delegate: Item {
        property string uuid: model.uuid
        property bool selected: model.selected
        property string name: model.name

        anchors.left: parent.left
        anchors.right: parent.right
        height: 35

        RowLayout {
          anchors.fill: parent
          anchors.margins: Sizes.singleMargin

          PathPilotLabel {
            Layout.fillWidth: true
            text: name
            elide: Text.ElideRight
            horizontalAlignment: Text.AlignLeft
            font.family: Fonts.font2
          }

          HorizontalFiller {
          }

          Led {
            Layout.preferredHeight: 25
            Layout.preferredWidth: height
            activeColor: Colors.green1
            visible: selected
            value: connected
          }
        }

        MouseArea {
          anchors.fill: parent
          onClicked: listView.currentIndex = index
        }
      }

      highlight: Rectangle {
        color: Colors.green2
      }
    }

    RowLayout {
      Layout.fillWidth: true

      PathPilotButton {
        Layout.fillWidth: true
        text: qsTr("Add")
        enabled: listView.currentItem && !listView.currentItem.selected
        onClicked: {
          fileNamePopup.text = listView.currentItem.name;
          fileNamePopup.uuid = listView.currentItem.uuid;
          fileNamePopup.open();
        }
        PathPilotToolTip {
          itemId: "msg_add_pp_cnc_instance"
        }
      }

      PathPilotButton {
        Layout.fillWidth: true
        text: qsTr("Remove")
        enabled: listView.currentItem && listView.currentItem.selected
        onClicked: root.model.removeNode(listView.currentItem.uuid)

        PathPilotToolTip {
          itemId: "msg_remove_pp_cnc_instance"
        }
      }
    }
  }

  FileNamePopup {
    id: fileNamePopup
    property string uuid: ""

    onAccepted: root.model.addNode(fileNamePopup.text, fileNamePopup.uuid)
  }
}
