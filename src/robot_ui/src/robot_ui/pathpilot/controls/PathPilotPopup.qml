import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers

Item {
  id: root
  signal closed
  signal opened
  default property alias data_: popup.data_
  property alias background: popup.background
  property alias modal: popup.modal
  property alias scale: popup.scale
  property alias closePolicy: popup.closePolicy
  property alias dim: popup.dim
  property alias spacing: popup.spacing
  property alias padding: popup.padding
  property alias popupVisible: popup.visible
  property alias contentItem: popup.contentItem
  property alias implicitWidth: popup.implicitWidth
  property alias implicitHeight: popup.implicitHeight

  visible: false
  onVisibleChanged: {
    console.warn("PathPilotPopup: use popupVisible instead of visible property");
  }

  function open() {
    popup.open();
  }

  function close() {
    popup.close();
  }

  Window {
    id: popupWindow
    property QtObject parent: root.Window.window

    width: parent?.width ?? 0
    height: parent?.height ?? 0
    x: parent?.x ?? 0
    y: parent?.y ?? 0
    visibility: visible ? (Handlers.app?.applicationWindowVisibility ?? Window.AutomaticVisibility) : Window.Hidden
    flags: Qt.FramelessWindowHint | (Handlers.app?.applicationWindowFlags ?? Qt.Window)
    modality: Qt.ApplicationModal
    screen: parent?.screen ?? null
    color: "transparent"

    PathPilotPopupBase {
      id: popup
      focus: root.focus

      onOpened: {
        popupWindow.show();
        root.opened();
      }

      onClosed: {
        popupWindow.close();
        root.closed();
      }
    }
  }
}
