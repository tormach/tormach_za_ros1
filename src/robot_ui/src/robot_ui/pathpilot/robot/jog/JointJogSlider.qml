import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Shapes
import pathpilot.core
import pathpilot.controls

RowLayout {
  id: root
  property alias from: slider.from
  property alias to: slider.to
  property alias value: slider.value
  readonly property bool incrementPressed: incrementButton.pressed || incrementActiveExternal
  readonly property bool decrementPressed: decrementButton.pressed || decrementActiveExternal
  readonly property bool incrementHovered: incrementButton.hovered || incrementActiveExternal
  readonly property bool decrementHovered: decrementButton.hovered || decrementActiveExternal
  property bool readOnly: true
  property bool incrementActiveExternal: false
  property bool decrementActiveExternal: false

  signal incrementClicked
  signal decrementClicked

  PathPilotButton {
    id: decrementButton
    implicitWidth: height
    hoverEnabled: true

    onClicked: root.decrementClicked()

    Text {
      anchors.centerIn: parent
      color: root.decrementPressed ? Colors.cyan1 : Colors.white1
      text: "◀"
      font.family: Fonts.font3
      font.pixelSize: Fonts.jogPanel.size3
      style: Text.Outline
      styleColor: parent.shadowColor
    }
  }

  Slider {
    id: slider
    Layout.fillWidth: true
    Layout.alignment: Qt.AlignVCenter
    from: -1.0
    to: 1.0
    implicitHeight: 40
    leftPadding: 0.0
    rightPadding: 0.0

    handle: Item {
      id: handle
      x: slider.leftPadding + slider.visualPosition * (slider.availableWidth - width)
      y: slider.topPadding + slider.availableHeight / 2 - height / 2
      implicitWidth: 20
      implicitHeight: 30
      height: slider.availableHeight

      Shape {
        id: arrowShape
        anchors.fill: parent
        vendorExtensionsEnabled: false

        ShapePath {
          strokeWidth: 1
          strokeColor: Colors.gray5
          fillColor: Colors.green2
          joinStyle: ShapePath.RoundJoin

          PathLine {
            x: arrowShape.width / 2
            y: arrowShape.height / 3
          }
          PathLine {
            x: arrowShape.width / 2
            y: arrowShape.height
          }
          PathLine {
            x: arrowShape.width / 2
            y: arrowShape.height / 3
          }
          PathLine {
            x: arrowShape.width
            y: 0
          }
          PathLine {
            x: 0
            y: 0
          }
        }
      }
    }

    background: Rectangle {
      x: slider.leftPadding + handle.width / 2
      y: slider.topPadding + handle.height / 3
      implicitWidth: 200
      implicitHeight: 20
      width: slider.availableWidth - handle.width
      height: handle.height * 2 / 3
      radius: 2
      color: Colors.white1
      border.width: 2
      border.color: Colors.gray5
    }

    MouseArea {
      anchors.fill: parent
      enabled: root.readOnly
    }
  }

  PathPilotButton {
    id: incrementButton
    implicitWidth: height
    hoverEnabled: true

    onClicked: root.incrementClicked()

    Text {
      anchors.centerIn: parent
      color: root.incrementPressed ? Colors.cyan1 : Colors.white1
      text: "▶"
      font.family: Fonts.font3
      font.pixelSize: Fonts.jogPanel.size3
      style: Text.Outline
      styleColor: parent.shadowColor
    }
  }
}
