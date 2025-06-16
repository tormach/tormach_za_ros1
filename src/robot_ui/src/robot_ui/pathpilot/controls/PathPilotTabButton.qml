import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core

TabButton {
  id: root

  property int alignment: Qt.AlignBottom
  property bool highlighted: false
  property color highlightedColor: Colors.red1
  property var iconObject: IconObject {
  }
  implicitWidth: implicitHeight * 5.8
  implicitHeight: d.spd * 5
  font.pixelSize: Fonts.controls.tabButton1
  font.family: Fonts.font2

  QtObject {
    id: d
    readonly property real spd: 5
  }

  background: Item {
    Rectangle {
      anchors.fill: parent
      anchors.topMargin: (root.alignment == Qt.AlignBottom) ? (root.checked ? 0 : d.spd * 0.5) : (root.checked ? 0 : d.spd * 0.75)
      anchors.bottomMargin: (root.alignment == Qt.AlignBottom) ? (root.checked ? -d.spd : -d.spd * 0.25) : (root.checked ? -d.spd : -d.spd * 0.5)
      radius: d.spd * 0.75
      color: root.highlighted ? root.highlightedColor : (root.checked ? Colors.white3 : Colors.gray4)

      Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: (root.alignment == Qt.AlignBottom) ? parent.top : undefined
        anchors.bottom: (root.alignment == Qt.AlignBottom) ? undefined : parent.bottom
        height: parent.radius
        color: parent.color
      }
    }
  }

  contentItem: Item {
    RowLayout {
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.verticalCenter: parent.verticalCenter
      anchors.verticalCenterOffset: d.spd * (0.5 + (root.checked ? 0 : (root.alignment == Qt.AlignBottom) ? -0.25 : 0.25))

      Icon {
        id: tabIcon
        icon: root.iconObject
      }

      Text {
        id: textLabel
        horizontalAlignment: Text.AlignHCenter
        Layout.fillWidth: true

        elide: Text.ElideRight
        font: root.font
        text: root.text
        color: root.enabled ? Colors.black1 : Colors.gray1
      }

      Item {
        implicitWidth: tabIcon.implicitWidth
        height: 1
      }
    }
  }
}
