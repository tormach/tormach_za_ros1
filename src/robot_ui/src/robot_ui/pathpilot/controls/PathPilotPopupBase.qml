import QtQuick
import QtQuick.Controls
import QtQuick.Templates as T
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers

T.Popup {
  id: root
  default property alias data_: container.data
  parent: Overlay.overlay
  implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset, contentWidth + leftPadding + rightPadding)
  implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset, contentHeight + topPadding + bottomPadding)
  padding: Sizes.doubleMargin
  x: Math.round((parent.width - width) / 2)
  y: Math.round((parent.height - height) / 2)
  modal: true
  focus: true
  scale: Sizes.scale
  closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

  contentItem: ColumnLayout {
    id: container
    spacing: Sizes.doubleSpacing
  }

  background: Rectangle {
    color: Colors.black1

    PathPilotBackgroundImage {
      anchors.fill: parent
      anchors.margins: Sizes.halfMargin
    }
  }

  T.Overlay.modal: Rectangle {
    color: "#7F000000"
  }

  T.Overlay.modeless: T.Overlay.modal
}
