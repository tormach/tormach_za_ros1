import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers
import pathpilot.file
import pathpilot.hub

ColumnLayout {
  id: root
  property alias selection: filePanel.selection
  property alias fileOperations: filePanel.fileOperations

  RowLayout {
    visible: filePanel.visible

    BackButton {
      onClicked: filePanel.navigation.navigateBack()
    }

    PathPilotIconButton {
      implicitWidth: 140
      text: qsTr("USB Home")
      icon_: Icons.filepanel.usb
      onClicked: filePanel.navigation.navigateHome()
    }

    PathPilotIconButton {
      implicitWidth: 120
      text: qsTr("Eject")
      icon_: Icons.filepanel.eject
      onClicked: usbMediaWatcher.unmountMedia()
    }

    PathPilotLabel {
      text: qsTr("Drive: %1").arg(usbMediaWatcher.mediaName)
    }

    HorizontalFiller {
    }
  }

  LocalFilePanel {
    id: filePanel
    navigation.homePath: usbMediaWatcher.usbPath
    visible: usbMediaWatcher.usbMounted
  }

  PathPilotLabel {
    Layout.fillWidth: true
    Layout.fillHeight: true
    horizontalAlignment: Qt.AlignHCenter
    verticalAlignment: Qt.AlignVCenter
    font.family: Fonts.font2
    text: qsTr("No USB flash drive connected.")
    visible: !filePanel.visible
  }

  UsbMediaWatcher {
    id: usbMediaWatcher
    path: FileUtils.userMediaMountPath
  }
}
