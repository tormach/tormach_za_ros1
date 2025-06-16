import QtQuick
import QtQuick.Controls
import QtQuick.Window
import pathpilot.core

ComboBox {
  id: control
  property alias error: textField.error
  property bool readOnly: false
  property int maximumPopupHeight: control.height * 8
  flat: true
  font.pixelSize: Fonts.controls.textField1
  font.family: Fonts.font2

  delegate: ItemDelegate {
    id: item
    readonly property bool isCurrent: control.currentIndex === index

    width: control.width
    contentItem: Text {
      text: control.textRole ? (Array.isArray(control.model) ? modelData[control.textRole] : model[control.textRole]) : modelData
      color: Colors.black1
      font.family: control.font.family
      font.pixelSize: control.font.pixelSize
      font.bold: item.isCurrent
      elide: Text.ElideRight
      verticalAlignment: Text.AlignVCenter
    }
    background: Item {
      Rectangle {
        anchors.fill: parent
        anchors.margins: Sizes.thickBorder
        color: item.highlighted ? Colors.cyan1 : "transparent"
        radius: 2
      }
    }
    highlighted: control.highlightedIndex === item.index
  }

  indicator: PathPilotTriangleIndicator {
    id: canvas
    x: control.width - width - control.rightPadding
    y: control.topPadding + (control.availableHeight - height) / 2
    z: 10
    color: control.pressed ? Colors.cyan1 : (control.enabled ? Colors.black1 : Colors.gray5)
    rotation: control.popup.visible ? 180 : 0
  }

  contentItem: PathPilotTextField {
    id: textField
    anchors.fill: parent
    horizontalAlignment: Text.AlignLeft
    text: control.editable ? control.editText : metrics.elidedText
    leftPadding: Sizes.singleMargin * 2
    readOnly: !control.editable
    validator: control.validator

    TextMetrics {
      id: metrics
      font: textField.font
      text: control.displayText
      elide: Qt.ElideRight
      elideWidth: textField.width - 25
    }

    MouseArea {
      anchors.fill: !control.editable ? parent : null
      anchors.right: !control.editable ? undefined : parent.right
      anchors.top: !control.editable ? undefined : parent.top
      anchors.bottom: !control.editable ? undefined : parent.bottom
      width: (control.indicator.width + control.spacing) * 3
      onClicked: {
        if (!control.readOnly) {
          control.popup.visible = !control.popup.visible;
        }
      }
    }
  }

  background: Item {
    implicitWidth: implicitHeight * 5
    implicitHeight: Sizes.controlHeight
  }

  popup: Popup {
    id: popup
    property real idealHeight: Math.min(control.maximumPopupHeight, listView.contentHeight)
    property real idealWidth: control.width
    y: control.height - 1
    implicitWidth: popup.idealWidth * Sizes.scale
    implicitHeight: popup.idealHeight * Sizes.scale
    padding: 0
    transformOrigin: Item.TopLeft

    ListView {
      id: listView
      scale: Sizes.scale
      transformOrigin: Item.TopLeft
      height: popup.idealHeight
      width: popup.idealWidth - Sizes.thickBorder * 2
      x: Sizes.thickBorder
      clip: true
      model: control.popup.visible ? control.delegateModel : null
      currentIndex: control.highlightedIndex
      interactive: true

      ScrollBar.vertical: ScrollBar {
        snapMode: ScrollBar.SnapAlways
        policy: listView.height < listView.contentHeight ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
      }
    }

    background: Rectangle {
      scale: Sizes.scale
      transformOrigin: Item.TopLeft
      height: popup.idealHeight
      width: popup.idealWidth
      color: Colors.white1
      border.color: Colors.gray3
      border.width: Sizes.thickBorder
      radius: Sizes.smallRadius
    }
  }

  function selectByText(text) {
    for (var i = 0; i < model.length; ++i) {
      if (model[i] == text) {
        control.currentIndex = i;
        return;
      }
    }
    control.currentIndex = 0;
  }
}
