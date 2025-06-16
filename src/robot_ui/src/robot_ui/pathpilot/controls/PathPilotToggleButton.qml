import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core

PathPilotButton {
  id: root
  readonly property color ledColor: Colors.green1
  property bool ledActive: true
  property bool ledSynced: true
  property bool bigLed: false
  property string propertyText1: "OPT1"
  property string propertyText2: "OPT2"
  property alias propertyFont: text1.font
  property alias propertyHorizontalAlignment: text1.horizontalAlignment
  checkable: true

  ColumnLayout {
    anchors.right: parent.right
    anchors.left: parent.left
    anchors.leftMargin: root.labelMargin
    anchors.rightMargin: anchors.leftMargin
    anchors.verticalCenter: parent.verticalCenter

    Text {
      id: text1
      Layout.fillWidth: true
      horizontalAlignment: Text.AlignRight
      text: root.propertyText1
      font.pixelSize: Fonts.controls.toggleButton1
      font.family: Fonts.font1
      color: !root.enabled ? root.disabledColor : root.labelColor
      style: Text.Outline
      styleColor: root.shadowColor
      rightPadding: text1.horizontalAlignment == Text.AlignRight ? led1.width + Sizes.singleSpacing : 0

      Led {
        id: led1
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        height: root.bigLed ? 16 : 12
        width: height
        activeColor: root.ledSynced ? root.ledColor : Colors.yellow1
        value: !root.checked || !root.ledSynced
        enabled: root.ledActive
      }
    }

    Text {
      id: text2
      Layout.fillWidth: true
      horizontalAlignment: text1.horizontalAlignment
      text: root.propertyText2
      font: text1.font
      color: !root.enabled ? root.disabledColor : root.labelColor
      style: Text.Outline
      styleColor: root.shadowColor
      rightPadding: text1.rightPadding

      Led {
        id: led2
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        height: led1.height
        width: height
        activeColor: root.ledSynced ? root.ledColor : Colors.yellow1
        value: root.checked || !root.ledSynced
        enabled: root.ledActive
      }
    }
  }
}
