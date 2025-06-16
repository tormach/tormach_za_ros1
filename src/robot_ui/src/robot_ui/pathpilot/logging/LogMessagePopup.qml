import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

PathPilotPopup {
  id: root
  property string severityString: "Warning"
  property string message: ""
  property string extendedInfo: ""
  property string title: severityString
  width: 1000
  height: 600

  QtObject {
    id: d
    readonly property TextInput clipboardHelper: TextInput {
      visible: false
    }

    function copyToClipboard(text) {
      clipboardHelper.text = text;
      clipboardHelper.selectAll();
      clipboardHelper.copy();
    }
  }

  PathPilotLabel {
    text: root.title
    font.family: Fonts.font2
    font.bold: true
  }

  Rectangle {
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.preferredHeight: root.height - buttonRow.height
    Layout.preferredWidth: root.width
    border.width: Sizes.halfMargin
    border.color: Colors.gray1

    ScrollView {
      id: view
      anchors.fill: parent

      TextArea {
        font.family: Fonts.font2
        font.pixelSize: Fonts.statusPanel.size1
        wrapMode: Text.WordWrap
        readOnly: true
        selectByMouse: true
        selectByKeyboard: true
        selectionColor: Colors.green2
        text: root.message + "\n\n" + root.extendedInfo
      }
    }
  }

  RowLayout {
    id: buttonRow
    HorizontalFiller {
    }

    PathPilotIconButton {
      id: copyButton
      implicitWidth: 220
      text: qsTr("Copy to Clipboard")
      icon_: Icons.filepanel.copy
      onClicked: {
        d.copyToClipboard(root.extendedInfo);
      }
    }

    PathPilotButton {
      id: closeButton
      implicitWidth: 120
      text: qsTr("Close")
      onClicked: root.close()
    }
  }
}
