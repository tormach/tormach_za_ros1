import QtQuick

Item {
  id: root
  readonly property bool modified: model && model.modified
  readonly property string type: model ? model.type : ""

  //color:
  Text {
    anchors.fill: parent
    color: root.modified ? "green" : styleData.textColor
    elide: styleData.elideMode
    text: root.type
  }
}
