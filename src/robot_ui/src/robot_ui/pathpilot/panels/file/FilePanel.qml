import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import QtCore
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers
import pathpilot.file

FilePanelBase {
  id: root
  property string mainSelectionPath: mainFilePanel.navigation.currentPath
  property string externalSelectionPath: ""
  property string homePath: Config.data.programHomePath
  title: qsTr("File")
  enabled: Handlers.app.browseFilesAllowed

  QtObject {
    id: d

    function loadProgram(path) {
      Handlers.conversational.commitChanges(function () {
          Handlers.program.loadProgram(path);
          Handlers.app.switchPanel(Panels.MainPanel);
        }, qsTr("loading program"));
    }

    function conversationalEdit(path) {
      Handlers.conversational.commitChanges(function () {
          Handlers.program.loadProgram(path);
          Handlers.app.switchPanel(Panels.ConversationalPanel);
        }, qsTr("loading program for conversational editing"));
    }
  }

  onVisibleChanged: {
    if (visible) {
      mainFilePanel.fileBrowser.selectFile(Handlers.conversational.programPath);
      mainFilePanel.fileBrowser.moveToSelected();
    }
  }

  Settings {
    id: settings
    category: "file"
    property alias hubSelected: usbHubToggleButton.checked
  }

  Shortcut {
    sequence: StandardKey.Find
    onActivated: {
      mainFilePanel.focusFilter();
    }
  }

  ProgramFilePopups {
  }

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleMargin
    spacing: Sizes.doubleSpacing

    ColumnLayout {
      Layout.fillWidth: true

      RowLayout {
        BackButton {
          onClicked: mainFilePanel.navigation.navigateBack()
        }

        HomeButton {
          implicitWidth: 100
          text: qsTr("Home")
          onClicked: mainFilePanel.navigation.navigateHome()
        }

        PathPilotIconButton {
          id: loadProgramButton
          implicitWidth: 180
          text: qsTr("Load Program")
          icon_: Icons.filepanel.open
          enabled: mainFilePanel.selection.programSelected
          onClicked: d.loadProgram(mainFilePanel.selection.programPath)

          PathPilotToolTip {
            itemId: "msg_load_program"
          }
        }

        HorizontalFiller {
        }
      }

      LocalFilePanel {
        id: mainFilePanel
        programLoadingEnabled: true
        navigation.homePath: root.homePath
      }
    }

    ColumnLayout {
      Layout.fillWidth: false
      visible: true
      spacing: Sizes.doubleSpacing

      PathPilotToggleButton {
        id: usbHubToggleButton
        implicitWidth: 60
        implicitHeight: 50
        Layout.alignment: Qt.AlignHCenter
        propertyText1: qsTr("USB")
        propertyText2: qsTr("Hub")
        propertyFont.pixelSize: Fonts.filePanel.size3

        PathPilotToolTip {
          itemId: "msg_usb_or_hub"
        }
      }

      VerticalFiller {
      }

      CopyFromToOperationsButtonGroup {
        id: copyFromToGroup
        leftSelection: mainFilePanel.selection
        rightSelection: usbHubToggleButton.checked ? hubFilePanel.hubConnector : usbFilePanel.selection

        onCopyLeftToRight: {
          if (usbHubToggleButton.checked) {
            hubFilePanel.hubConnector.upload(copyFromToGroup.leftSelection);
          } else {
            mainFilePanel.fileOperations.copyTo(rightSelection.path);
          }
        }

        onCopyRightToLeft: {
          if (usbHubToggleButton.checked) {
            hubFilePanel.hubConnector.download(copyFromToGroup.leftSelection.path);
          } else {
            usbFilePanel.fileOperations.copyTo(leftSelection.path);
          }
        }
      }

      VerticalFiller {
      }
    }

    UsbFilePanel {
      id: usbFilePanel
      Layout.fillWidth: true
      visible: !usbHubToggleButton.checked
    }

    HubFilePanel {
      id: hubFilePanel
      Layout.fillWidth: true
      visible: usbHubToggleButton.checked
    }

    ColumnLayout {
      Layout.fillWidth: true

      PathPilotLabel {
        Layout.alignment: Qt.AlignHCenter
        text: qsTr("File Preview")
        font.pixelSize: Fonts.filePanel.size2
        Layout.preferredHeight: loadProgramButton.height
      }

      FilePreview {
        Layout.fillHeight: true
        Layout.fillWidth: true
        mainFileSelection: mainFilePanel.selection
        secondaryFileSelection: usbFilePanel.selection
        hubConnector: hubFilePanel.hubConnector
      }

      RowLayout {
        Layout.fillWidth: true

        HorizontalFiller {
        }

        PathPilotButton {
          enabled: mainFilePanel.selection.programSelected
          implicitWidth: 160
          text: qsTr("Conv. Edit")
          onClicked: d.conversationalEdit(mainFilePanel.selection.programPath)

          PathPilotToolTip {
            itemId: "msg_conv_edit"
            sidePosition: PathPilotToolTip.Side.Left
          }
        }

        PathPilotButton {
          enabled: mainFilePanel.selection.programSelected
          implicitWidth: 160
          text: qsTr("Edit Program")
          onClicked: ApplicationHelpers.runSystemCommand(Config.user.codeEditor + " \"" + mainFilePanel.selection.programPath + "\"")

          PathPilotToolTip {
            itemId: "msg_edit_program"
            sidePosition: PathPilotToolTip.Side.Left
          }
        }
      }
    }
  }
}
