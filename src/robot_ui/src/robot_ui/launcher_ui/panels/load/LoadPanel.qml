import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import launcher_ui.logic 1.0
import pathpilot.file
import pathpilot.development
import QtScxml

Item {
  id: root
  property StateMachine stateMachine
  property Item buttonContainer
  property string mainSelectionPath: "/media"

  readonly property QtObject _d: QtObject {
    id: d

    function selectLocalImage() {
      root.stateMachine.submitEvent("select_local");
    }

    function loadCompleted() {
      root.stateMachine.submitEvent("usb_load_completed");
    }

    function loadStarted() {
      root.stateMachine.submitEvent("usb_load_started");
    }
  }

  LoadImage {
    id: loadImage
    onLoadCompleted: d.loadCompleted()
    onLoadStarted: d.loadStarted()
  }

  ColumnLayout {
    id: selectPanel
    anchors.fill: parent
    spacing: Sizes.doubleSpacing
    visible: root.stateMachine?.usbFileSelect ?? false

    onVisibleChanged: {
      if (visible) {
        mainFileSystemBrowser.open();
      }
    }

    OpenFilePopup {
      id: mainFileSystemBrowser
      implicitWidth: root.width * 0.9
      implicitHeight: root.height * 0.9
      closePolicy: Popup.NoAutoClose
      homePath: root.mainSelectionPath
      fileFilter: ".*\\.tar"

      onAccepted: {
        loadImage.startLoading(mainFileSystemBrowser.path);
      }

      onCancelled: {
        d.selectLocalImage();
      }
    }

    VerticalFiller {
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("Waiting for file selection...")
    }

    PathPilotBusyIndicator {
      Layout.alignment: Qt.AlignHCenter
    }

    VerticalFiller {
    }
  }

  ColumnLayout {
    id: loadingPanel
    anchors.fill: parent
    spacing: Sizes.doubleSpacing
    visible: root.stateMachine?.usbLoading ?? false

    VerticalFiller {
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("Loading from file %1").arg(mainFileSystemBrowser.path)
    }

    PathPilotBusyIndicator {
      Layout.alignment: Qt.AlignHCenter
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      font.family: Fonts.font2
      text: qsTr("Progress %1%").arg(loadImage.layerLoadingProgress)
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      font.family: Fonts.font2
      text: qsTr("Processing Layer %1").arg(loadImage.layerLoadingNumber + 1)
    }

    VerticalFiller {
    }
  }

  ColumnLayout {
    id: outputPanel
    anchors.fill: parent
    spacing: Sizes.doubleSpacing
    visible: root.stateMachine?.usbLoaded ?? false

    VerticalFiller {
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("File %1 imported.").arg(mainFileSystemBrowser.path)
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      font.family: Fonts.font2
      visible: loadImage.validImagesExist
      text: qsTr("Successfully loaded images:")
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      font.family: Fonts.font2
      visible: loadImage.validImagesExist
      text: loadImage.validImages
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      font.family: Fonts.font2
      visible: loadImage.invalidImagesExist
      text: qsTr("Invalid images:")
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      font.family: Fonts.font2
      visible: loadImage.invalidImagesExist
      text: loadImage.invalidImages
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      font.family: Fonts.font2
      visible: loadImage.outputErrorExists
      text: qsTr("Error message:")
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      font.family: Fonts.font2
      visible: loadImage.outputErrorExists
      text: loadImage.outputError
    }

    VerticalFiller {
    }
  }

  RowLayout {
    visible: outputPanel.visible
    parent: root.buttonContainer

    PathPilotButton {
      id: continueButton
      Layout.alignment: Qt.AlignHCenter
      horizontalAlignment: Text.AlignHCenter
      text: qsTr("Continue")

      onClicked: d.selectLocalImage()
    }
  }
}
