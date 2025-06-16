import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import launcher_ui.logic 1.0
import QtScxml

Item {
  id: root
  property StateMachine stateMachine
  property Item buttonContainer

  readonly property QtObject d: QtObject {

    property alias channelPanelVisible: localChannelsModel.multiple
    property alias changelogPanelVisible: localImagesModel.startPossible
    property alias deletionPossible: localImagesModel.deletionPossible

    function selectImage() {
      if (localImagesModel.startPossible) {
        Updater.setImage(localImagesModel.stagedImageName);
      }
    }

    function selectFromUsb() {
      stateMachine.submitEvent("select_usb");
    }

    function displayImages() {
      if (visible) {
        localImagesModel.channelFilter = channelsComboBox.channel;
        localImagesModel.loadImages();
      }
    }

    function deleteVersions() {
      root.stateMachine.submitEvent("delete_versions");
    }

    function loadChannels() {
      if (visible) {
        localChannelsModel.loadChannels();
      }
    }

    function requestDelete() {
      root.stateMachine.submitEvent('confirm_delete');
    }

    function requestBack() {
      root.stateMachine.submitEvent('delete_finished');
    }

    function deleteImages() {
      if (deletionPossible) {
        localImagesModel.deleteImages();
      }
    }
  }

  Connections {
    target: Updater
    function onImageSelected() {
      stateMachine.submitEvent("image_selected");
    }
  }

  EventConnection {
    stateMachine: root.stateMachine
    events: ["pull_complete"]
    onOccurred: {
      d.displayImages();
    }
  }

  EventConnection {
    stateMachine: root.stateMachine
    events: ["delete_versions"]
    onOccurred: {
      d.deleteImages();
    }
  }

  onVisibleChanged: {
    if (visible) {
      d.loadChannels();
    }
  }

  LocalImages {
    id: localImagesModel
    onLoadingStarted: {
      imagesLoading.visible = true;
    }
    onLoadingCompleted: {
      imagesLoading.visible = false;
    }
    onDeletingCompleted: {
      stateMachine.submitEvent("delete_finished");
    }
  }

  LocalChannels {
    id: localChannelsModel

    onLoadingCompleted: {
      channelsComboBox.currentIndex = 0;
      d.displayImages();
    }
  }

  ColumnLayout {
    anchors.fill: parent
    RowLayout {
      visible: root.stateMachine?.versionSelection ?? false
      ColumnLayout {
        RowLayout {
          id: channelPanel
          visible: localChannelsModel.multiple

          PathPilotLabel {
            text: qsTr("Release channel:")
          }

          PathPilotComboBox {
            id: channelsComboBox
            // Will generate an exception when no available channels are actually
            // present in the Docker daemon on the machine controller (in production
            // use, this should never happen)
            property string channel: currentIndex != -1 ? delegateModel.items.get(currentIndex).model.name : ""
            textRole: "label"
            model: localChannelsModel
            onActivated: {
              d.displayImages();
            }
          }

          PathPilotBusyIndicator {
            id: imagesLoading
            visible: false
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredHeight: 45
            Layout.preferredWidth: 45
          }
        }

        PathPilotLabel {
          text: qsTr("Versions available locally:")
        }

        LocalImagesListView {
          id: localImagesListView
          Layout.fillWidth: true
          Layout.fillHeight: true
          Layout.preferredWidth: 500
          model: localImagesModel
        }
      }

      ColumnLayout {
        visible: d.changelogPanelVisible
        PathPilotLabel {
          text: qsTr("Changelog:")
        }

        Rectangle {
          Layout.fillHeight: true
          Layout.fillWidth: true
          Layout.preferredWidth: 300
          border.width: Sizes.halfMargin
          border.color: Colors.gray1

          ScrollView {
            id: view
            anchors.fill: parent

            TextArea {
              wrapMode: Text.WordWrap
              font.pixelSize: Fonts.launcher.size1
              font.family: Fonts.font2
              readOnly: true
              selectByMouse: true
              selectByKeyboard: true
              selectionColor: Colors.green2
              textFormat: Text.StyledText
              text: localImagesModel.startPossible ? localImagesModel.changelogData : qsTr(qsTr("No image selected"))
            }
          }
        }
      }
    }
  }

  ColumnLayout {
    id: deletingPanel
    anchors.fill: parent
    spacing: Sizes.doubleSpacing
    visible: root.stateMachine?.deletingImages ?? false

    VerticalFiller {
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("Deleting selected images...")
    }

    PathPilotBusyIndicator {
      Layout.alignment: Qt.AlignHCenter
    }

    VerticalFiller {
    }
  }

  RowLayout {
    visible: root.visible
    parent: root.buttonContainer

    PathPilotButton {
      horizontalAlignment: Text.AlignHCenter
      text: qsTr("Start")
      enabled: localImagesModel.startPossible

      onClicked: d.selectImage()
    }

    PathPilotButton {
      Layout.preferredWidth: 200
      horizontalAlignment: Text.AlignHCenter
      text: qsTr("Load  from  USB...")

      onClicked: d.selectFromUsb()
    }

    PathPilotButton {
      Layout.alignment: Qt.AlignHCenter
      Layout.preferredWidth: 150
      horizontalAlignment: Text.AlignHCenter
      text: qsTr("Delete")

      enabled: d.deletionPossible
      onClicked: d.deleteVersions()
    }
  }
}
