import QtQuick
import QtQuick.Controls
import pathpilot.controls

UnscaledTestBase {
  id: root

  Rectangle {
    id: greenRect
    color: "green"
    width: 200
    height: 200

    Rectangle {
      id: blueRect
      color: "blue"
      width: 100
      height: 100
    }
  }

  Rectangle {
    id: yellowRect
    color: "yellow"
    anchors.fill: parent
    anchors.margins: 20

    Button {
      anchors.centerIn: parent
      text: "Button"
      onClicked: orangeRect.visible = true
    }

    TextInput {
      text: "foo"
    }

    Rectangle {
      id: orangeRect
      color: "#77FF5500"
      parent: invisibleRect
      anchors.fill: parent
      anchors.margins: 10
      visible: false

      MouseArea {
        anchors.fill: parent
      }
    }
  }

  Item {
    id: invisibleRect
    anchors.fill: parent
  }
}
