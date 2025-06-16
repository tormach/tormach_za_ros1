import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core

RowLayout {
  id: root
  property alias from: slider.from
  property alias to: slider.to
  property alias value: slider.value
  property alias stepSize: slider.stepSize
  property alias pressed: slider.pressed
  property double defaultValue: (root.to - root.from) / 2
  property alias labelColor: label.color
  property alias live: slider.live

  readonly property bool hovered: sliderMouseArea.containsMouse || labelMouseArea.containsMouse
  spacing: 0
  opacity: enabled ? 1.0 : 0.7

  function increase() {
    slider.increase();
  }

  function decrease() {
    slider.decrease();
  }

  Slider {
    id: slider
    Layout.fillWidth: true
    Layout.alignment: Qt.AlignVCenter
    from: 0.0
    to: 1.0
    implicitHeight: Sizes.controlHeight

    // live: true
    handle: Rectangle {
      x: slider.leftPadding + slider.visualPosition * (slider.availableWidth - width)
      y: slider.topPadding + (slider.availableHeight - height) / 2
      implicitWidth: 60
      implicitHeight: slider.height
      radius: 4
      border.width: Sizes.thinBorder
      border.color: Colors.gray3
      gradient: Gradient {
        GradientStop {
          position: 0.0
          color: Colors.gray7
        }
        GradientStop {
          position: 1.0
          color: Colors.gray5
        }
      }

      Rectangle {
        id: centerStripe
        anchors.centerIn: parent
        width: 2
        height: parent.height * 0.8
        radius: height / 2
        color: Colors.gray3
      }

      Rectangle {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: centerStripe.right
        anchors.leftMargin: 5
        width: 2
        height: parent.height * 0.8
        radius: height / 2
        color: Colors.gray3
      }

      Rectangle {
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: centerStripe.left
        anchors.rightMargin: 5
        width: 2
        height: parent.height * 0.8
        radius: height / 2
        color: Colors.gray3
      }
    }

    background: Rectangle {
      x: slider.leftPadding
      y: slider.topPadding + (slider.availableHeight - height) / 2
      implicitWidth: slider.implicitHeight * 5
      implicitHeight: 10
      width: slider.availableWidth
      height: implicitHeight
      radius: height / 2
      color: Colors.gray1

      Rectangle {
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: 2
        width: slider.visualPosition * parent.width
        color: Colors.green2
        radius: parent.radius
      }
    }

    MouseArea {
      id: sliderMouseArea
      anchors.fill: parent
      acceptedButtons: Qt.RightButton
      hoverEnabled: true
      onClicked: {
        root.value = root.defaultValue;
      }
    }
  }

  Text {
    id: label
    Layout.fillWidth: false
    Layout.fillHeight: true
    Layout.preferredWidth: 60
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
    font.family: Fonts.font2
    font.pixelSize: Fonts.controls.slider1
    color: Colors.blue2
    text: ~~(slider.value * 100) + "%"

    MouseArea {
      id: labelMouseArea
      anchors.fill: parent
      hoverEnabled: true
    }
  }
}
