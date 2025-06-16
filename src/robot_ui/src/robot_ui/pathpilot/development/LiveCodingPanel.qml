import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtCore
import pathpilot.file
import pathpilot.core
import pathpilot.development

Item {
  id: root
  property alias hideToolBar: hideToolBarCheck.checked
  property int flags: Qt.Window
  property int visibility: Window.AutomaticVisibility
  property alias rootItem: loader.item

  readonly property QtObject _d: QtObject {
    id: d

    function reload() {
      loader.source = "";
      ApplicationHelpers.clearQmlComponentCache();
      // delay setting the source to run event loop
      // for cleanups to happen before reloading
      Qt.callLater(function () {
          loader.source = fileDialog.file;
        });
    }

    function reloadOnce() {
      if (reloadProtectionTimer.running) {
        return;
      }
      d.reload();
      reloadProtectionTimer.start();
    }

    function openWithSystemEditor() {
      ApplicationHelpers.openUrlWithDefaultApplication(fileDialog.file);
    }

    function unload() {
      loader.source = "";
      fileDialog.selected = false;
      browser.update();
    }

    function restart() {
      PythonReloader.restart();
    }
  }

  Settings {
    id: windowSettings
    category: "window"
    property alias width: root.width
    property alias height: root.height
    property alias x: root.x
    property alias y: root.y
    property alias visibility: root.visibility
    property alias hideToolBar: hideToolBarCheck.checked
  }

  CpuMonitor {
    id: cpuMonitor
  }

  MouseArea {
    id: smallArea
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    height: 10
    width: height
    z: 10
    visible: contentItem.loaded && !fullArea.delayedVisible
    hoverEnabled: true
    propagateComposedEvents: true

    onClicked: function (mouse) {
      mouse.accepted = false;
    }
    onEntered: fullArea.visible = true
  }

  MouseArea {
    id: fullArea
    property bool delayedVisible: false
    anchors.top: parent.top
    anchors.right: parent.right
    anchors.left: parent.left
    height: 40
    z: 9
    hoverEnabled: true
    propagateComposedEvents: true
    visible: false

    onClicked: function (mouse) {
      mouse.accepted = false;
    }
    onPressed: function (mouse) {
      mouse.accepted = false;
    }
    onReleased: function (mouse) {
      mouse.accepted = false;
    }
    onExited: visible = false
    onVisibleChanged: delayTimer.start()

    Timer {
      id: delayTimer
      interval: 10
      onTriggered: fullArea.delayedVisible = fullArea.visible // break binding loop
    }
  }

  ColumnLayout {
    anchors.fill: parent
    anchors.topMargin: menuBar.visible ? 5 : 0

    RowLayout {
      id: menuBar
      visible: !hideToolBarCheck.checked || (smallArea.containsMouse || fullArea.containsMouse || !contentItem.loaded)

      Button {
        Layout.preferredHeight: 30
        enabled: fileDialog.selected
        text: qsTr("Edit")
        onClicked: d.openWithSystemEditor()
      }

      Button {
        Layout.preferredHeight: 30
        enabled: fileDialog.selected
        text: qsTr("Reload")
        onClicked: d.reloadOnce()
      }

      Button {
        Layout.preferredHeight: 30
        text: qsTr("Unload")
        onClicked: d.unload()
      }

      Button {
        Layout.preferredHeight: 30
        text: qsTr("Restart")
        onClicked: d.restart()
      }

      Label {
        Layout.alignment: Qt.AlignVCenter
        text: qsTr("CPU: %1%").arg(cpuMonitor.usage.toFixed(1))
      }

      Item {
        Layout.fillWidth: true
      }

      Button {
        text: qsTr("Inspect Item")
        checkable: true
        checked: clickAndFindArea.visible
        onClicked: clickAndFindArea.visible = true
      }

      CheckBox {
        id: hideToolBarCheck
        text: qsTr("Hide Tool Bar")
        checked: false
      }

      CheckBox {
        text: qsTr("Fullscreen")
        checked: root.visibility === Window.FullScreen

        onClicked: {
          if (checked) {
            root.visibility = Window.FullScreen;
          } else {
            root.visibility = Window.AutomaticVisibility;
          }
        }
      }

      CheckBox {
        text: qsTr("On Top")
        checked: root.flags & Qt.WindowStaysOnTopHint

        onClicked: {
          if (checked) {
            root.flags = root.flags | Qt.WindowStaysOnTopHint;
          } else {
            root.flags = root.flags & ~Qt.WindowStaysOnTopHint;
          }
        }
      }
    }

    Item {
      id: contentItem
      Layout.fillWidth: true
      Layout.fillHeight: true
      property bool loaded: loader.status !== Loader.Null

      Loader {
        id: loader
        anchors.fill: parent

        onStatusChanged: {
          if (status !== Loader.Error) {
            return;
          }
          var msg = loader.sourceComponent.errorString();
          errorLabel.text = qsTr("QML Error: Loading QML file failed:\n") + msg;
        }
      }

      MouseArea {
        id: clickAndFindArea
        visible: false
        anchors.fill: loader
        cursorShape: Qt.CrossCursor
        onClicked: function (mouse) {
          clickAndFindArea.visible = false;
          var topItem = QmlInspector.findTopItem(loader, mouse.x, mouse.y);
          var item = QmlInspector.findProjectItem(topItem);
          if (item) {
            var text = QmlInspector.inspectProjectItems(item);
            text += "\n\n" + QmlInspector.inspectItem(item);
            inspectorTextArea.text = text;
            inspectorDialog.visible = true;
          }
        }
      }

      Window {
        id: inspectorDialog
        property QtObject parent: root.Window.window
        width: parent.width * 0.7
        height: parent.height * 0.7
        x: parent.x + (parent.width - width) / 2
        y: parent.y + (parent.height - height) / 2
        flags: root.flags
        modality: Qt.ApplicationModal
        visible: false
        screen: parent?.screen ?? null

        ColumnLayout {
          anchors.fill: parent
          anchors.margins: 5

          ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            TextArea {
              id: inspectorTextArea
            }
          }

          Button {
            Layout.alignment: Qt.AlignRight
            text: qsTr("Close")
            onClicked: inspectorDialog.visible = false
          }
        }
      }

      Label {
        id: errorLabel
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.Wrap
        visible: loader.status === Loader.Error
      }

      FileSelectionDialog {
        id: fileDialog
        anchors.fill: parent
        model: browser.qmlFiles
        visible: !contentItem.loaded

        onSelectedChanged: {
          if (selected) {
            d.reloadOnce();
          }
        }
      }
    }
  }

  ProjectBrowser {
    id: browser
    projectPath: userProjectPath
    extensions: ['qml', 'ui.qml']
  }

  FileWatcher {
    id: fileWatcher
    fileUrl: browser.projectPath
    recursive: true
    enabled: fileDialog.selected
    onFileChanged: d.reloadOnce()
    nameFilters: ["*.qmlc", "*.jsc", "*.pyc", ".#*", ".*", "__pycache__", "*___jb_tmp___" // PyCharm safe write
      , "*___jb_old___"]
  }

  Timer {
    // timer prevents multiple reloads in a short time
    id: reloadProtectionTimer
    interval: 100
    running: false
  }

  // add additional components that should only be loaded once here.
}
