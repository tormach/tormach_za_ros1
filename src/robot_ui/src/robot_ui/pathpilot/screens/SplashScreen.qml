import QtQuick
import pathpilot.core

Rectangle {
  id: root
  property double loadingProgress: 0.75
  readonly property int smallerSide: width < height ? width : height
  color: Colors.black1
  opacity: 1.0
  width: 1280
  height: 800

  Image {
    id: background
    source: Icons.general.background
    anchors.fill: parent
    fillMode: Image.PreserveAspectCrop
  }

  Image {
    id: logoImg
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.verticalCenter: parent.verticalCenter
    anchors.verticalCenterOffset: -parent.smallerSide * 0.05
    source: Icons.splashscreen.icon1
    smooth: true
    width: parent.smallerSide * 1.0
    height: width * 0.4
    sourceSize.width: width
    sourceSize.height: height
    fillMode: Image.PreserveAspectFit
  }

  Rectangle {
    id: barRect
    anchors.top: logoImg.bottom
    anchors.horizontalCenter: parent.horizontalCenter
    width: parent.smallerSide * 0.6
    height: parent.smallerSide * 0.015
    smooth: true
    border.color: Colors.white2
    border.width: 0
    radius: height / 2
    color: Colors.white2
    anchors.topMargin: 50
    Rectangle {
      id: progressRect
      anchors.verticalCenter: parent.verticalCenter
      anchors.left: parent.left
      anchors.leftMargin: parent.width * 0.01
      width: parent.width * 0.98 * root.loadingProgress
      height: parent.height * 0.7
      smooth: true
      radius: height / 2
      color: Colors.green1
    }
  }

  Behavior on opacity {
    enabled: opacity == 1.0
    PropertyAnimation {
      duration: 500
      properties: "opacity"
      easing.type: Easing.InCubic
    }
  }
}
