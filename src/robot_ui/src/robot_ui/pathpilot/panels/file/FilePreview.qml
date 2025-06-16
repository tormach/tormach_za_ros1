import QtQuick
import QtQuick.Controls
import QtQuick.Window
import pathpilot.core
import pathpilot.file
import pathpilot.hub

Rectangle {
  id: root
  property FileSelection mainFileSelection
  property FileSelection secondaryFileSelection
  property HubConnector hubConnector
  border.width: Sizes.halfMargin
  border.color: Colors.gray1

  readonly property QtObject _d: QtObject {
    id: d
    property bool localPreview: true
    property bool secondaryPreview: false
    property string remoteFile: ""
    onRemoteFileChanged: {
      root.hubConnector.downloadFilePreview(remoteFile);
    }
  }

  FilePreviewLoader {
    id: filePreview
    path: d.secondaryPreview ? root.secondaryFileSelection.programPath : root.mainFileSelection.programPath
  }

  // files are updated when the selection changes
  // whatever is last selected is shown
  Connections {
    target: root.mainFileSelection
    function onFilesChanged() {
      d.secondaryPreview = false;
      d.localPreview = true;
    }
  }

  Connections {
    target: root.secondaryFileSelection
    function onFilesChanged() {
      d.secondaryPreview = true;
      d.localPreview = true;
    }
  }

  Connections {
    target: root.hubConnector
    function onFilesChanged() {
      d.localPreview = false;
      if (root.hubConnector.files.length > 0) {
        d.remoteFile = root.hubConnector.files[0];
      } else {
        d.remoteFile = "";
      }
    }
  }

  ScrollView {
    anchors.fill: parent
    anchors.margins: root.border.width

    TextArea {
      id: previewTextArea
      visible: d.localPreview ? filePreview.previewable : root.hubConnector.filePreviewable
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size3
      readOnly: true
      selectByMouse: true
      selectByKeyboard: true
      selectionColor: Colors.green2
      text: d.localPreview ? filePreview.content : root.hubConnector.filePreviewContent

      Component.onCompleted: wrapMode = TextEdit.NoWrap // workaround
    }
  }
}
