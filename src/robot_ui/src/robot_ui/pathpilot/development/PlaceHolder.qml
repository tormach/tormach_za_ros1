import QtQuick

Rectangle {
  id: root
  property alias text: label.text
  width: 100
  height: 100
  color: Qt.rgba(Math.random(), Math.random(), Math.random(), 1)

  Text {
    id: label
    anchors.centerIn: parent
    text: ""
  }
}
