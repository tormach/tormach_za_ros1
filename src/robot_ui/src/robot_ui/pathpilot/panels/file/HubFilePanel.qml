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
  readonly property bool online: root.hubConnector.loggedIn
  readonly property bool taskRunning: root.hubConnector.taskRunning
  readonly property HubConnector hubConnector: Handlers.state.hubConnector

  onVisibleChanged: {
    if (root.online && root.hubConnector.status == HubConnector.IdleStatus) {
      root.hubConnector.reloadFiles();
    }
  }

  Connections {
    target: root.hubConnector
    function onFilesUpdated() {
      fileSystemBrowser.reload();
    }
    function onLoggedInChanged() {
      if (root.hubConnector.loggedIn) {
        root.hubConnector.reloadFiles();
      }
    }
  }

  RowLayout {
    BackButton {
      enabled: root.online
      onClicked: fileSystemBrowser.navigation.navigateBack()
    }

    PathPilotIconButton {
      id: hubHomeBUtton
      enabled: root.online
      implicitWidth: 140
      text: qsTr("Hub Home")
      icon_: Icons.filepanel.hub
      onClicked: fileSystemBrowser.navigation.navigateHome()

      PathPilotToolTip {
        itemId: "msg_hub_home"
      }
    }

    PathPilotIconButton {
      id: reloadButton
      enabled: root.online
      icon_: Icons.filepanel.refresh
      text: qsTr("Reload")
      onClicked: root.hubConnector.reloadFiles()
      PathPilotToolTip {
        itemId: "msg_reload"
      }
    }

    PathPilotIconButton {
      id: loginLogoutButton
      text: root.online ? qsTr("Log out") : qsTr("Sign In")
      icon_: root.online ? Icons.filepanel.online : Icons.filepanel.offline
      onClicked: {
        if (root.online) {
          root.hubConnector.logout();
        } else {
          hubLoginPopup.open();
        }
      }
      PathPilotToolTip {
        itemId: "msg_log_out"
      }
    }

    HorizontalFiller {
    }
  }

  HubFileSystemBrowser {
    id: fileSystemBrowser
    Layout.fillHeight: true
    Layout.fillWidth: true
    hubConnector: root.hubConnector
    fileFilter: ".*" + fileOperations.filterString + ".*"
    filterDirs: true

    onFileSelected: function (path) {
      console.log("download " + path);
    }
    onFolderSelected: function (path) {
      fileSystemBrowser.clearSelection();
      fileSystemBrowser.navigation.currentPath = path;
    }

    MouseArea {
      id: readonlyMouseArea
      anchors.fill: parent
      visible: root.taskRunning

      PathPilotBusyIndicator {
        anchors.centerIn: parent
      }
    }
  }

  RowLayout {
    Layout.fillWidth: true

    Icon {
      icon: Icons.filepanel.warning
      visible: root.hubConnector.status == HubConnector.ErrorStatus || !root.online
    }

    PathPilotLabel {
      id: infoLabel
      Layout.fillWidth: true
      Layout.alignment: Qt.AlignVCenter
      horizontalAlignment: Text.AlignLeft
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size3
      elide: Text.ElideRight
      text: {
        if (root.hubConnector.status === HubConnector.ErrorStatus) {
          return root.hubConnector.errorString;
        } else {
          if (root.online) {
            return qsTr("Free space: %1 Used: %2").arg(FileUtils.humanReadableBytes(root.hubConnector.availableBytes)).arg(FileUtils.humanReadableBytes(root.hubConnector.usedBytes));
          } else {
            return qsTr("HUB session timeout; sign in required.");
          }
        }
      }
    }
  }

  HubFileOperationsButtonGroup {
    id: fileOperations
    Layout.fillWidth: true
    selection: fileSystemBrowser.fileSelection
  }

  HubLoginPopup {
    id: hubLoginPopup
    email: root.hubConnector.email
    onAccepted: function (email, password) {
      root.hubConnector.email = email;
      root.hubConnector.password = password;
      root.hubConnector.login();
    }
  }
}
