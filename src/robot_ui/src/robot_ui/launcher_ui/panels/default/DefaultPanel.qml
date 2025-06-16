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
  property bool attention: false

  readonly property QtObject _d: QtObject {
    id: d

    function selectImage(versionName) {
      Updater.setImage(versionName);
      root.stateMachine.submitEvent("image_selected");
    }

    function deleteVersions() {
      root.stateMachine.submitEvent("delete_images");
    }

    function displayDefault() {
      if (visible) {
        defaultImage.loadDefaultImage();
      }
    }

    function decorateChange() {
      displayDefault();
      attention = true;
    }
  }

  EventConnection {
    stateMachine: root.stateMachine
    events: ["pull_complete"]
    onOccurred: {
      d.decorateChange();
    }
  }

  onVisibleChanged: {
    if (visible) {
      d.displayDefault();
    }
  }

  DefaultImage {
    id: defaultImage

    onDefaultNotFound: {
      console.log("Default image not found");
      root.stateMachine.submitEvent("select_local");
    }
  }

  PathPilotButton {
    id: dummyButton

    visible: false
  }

  ColumnLayout {
    anchors.fill: parent
    spacing: Sizes.doubleSpacing

    VerticalFiller {
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("Version staged to run:")
    }

    RowLayout {
      Layout.maximumHeight: col.height + Sizes.singleMargin * 2

      HorizontalFiller {
      }

      Rectangle {
        Layout.fillHeight: true
        Layout.minimumWidth: 10
        color: root.attention ? Colors.orange1 : Colors.green2
      }

      Rectangle {
        id: rect
        Layout.fillHeight: true
        Layout.preferredWidth: col.width + 3 * Sizes.singleMargin
        anchors.rightMargin: Sizes.doubleMargin
        color: Colors.gray1

        Column {
          id: col
          x: Sizes.doubleMargin
          y: (parent.height - height) / 2
          anchors.leftMargin: Sizes.singleMargin
          anchors.rightMargin: Sizes.doubleMargin

          PathPilotLabel {
            font.family: Fonts.font2
            font.pixelSize: Fonts.launcher.size2
            text: qsTr("<b>Version:</b> %1 %2").arg(defaultImage.version).arg(defaultImage.codename)
          }
          PathPilotLabel {
            font.family: Fonts.font2
            font.pixelSize: Fonts.launcher.size2
            text: qsTr("<b>Description:</b> %1").arg(defaultImage.description)
          }
          PathPilotLabel {
            font.family: Fonts.font2
            font.pixelSize: Fonts.launcher.size2
            text: qsTr("<b>Created:</b> %1").arg(defaultImage.creationDate)
          }
        }
      }

      HorizontalFiller {
      }
    }

    VerticalFiller {
    }

    RowLayout {
      visible: root.visible
      parent: root.buttonContainer

      PathPilotButton {
        Layout.alignment: Qt.AlignHCenter
        horizontalAlignment: Text.AlignHCenter
        text: qsTr("Start")

        onClicked: d.selectImage(defaultImage.name)
      }

      PathPilotButton {
        Layout.preferredWidth: 300
        horizontalAlignment: Text.AlignHCenter
        text: qsTr("Select another version...")

        onClicked: root.stateMachine.submitEvent("select_local")
      }

      PathPilotButton {
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 150
        horizontalAlignment: Text.AlignHCenter
        text: qsTr("Delete...")

        onClicked: d.deleteVersions()
      }
    }
  }
}
