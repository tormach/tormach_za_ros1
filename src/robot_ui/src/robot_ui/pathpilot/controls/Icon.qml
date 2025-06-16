import QtQuick
import pathpilot.core

Item {
  id: root
  property var icon: IconObject {
  }
  property alias image: image
  implicitWidth: image.width
  implicitHeight: image.height

  Image {
    id: image
    source: icon.source
    sourceSize: icon.size
    width: icon.width
    height: icon.height
  }
}
