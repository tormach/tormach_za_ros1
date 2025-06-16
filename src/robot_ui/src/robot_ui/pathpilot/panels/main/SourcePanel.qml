import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.handlers

Item {
  id: root
  property bool folded: true
  property bool recentFilesVisible: false
  property bool mdiVisible: false
  Layout.preferredWidth: folded ? 300 : 600

  ColumnLayout {
    anchors.fill: parent

    PathPilotComboBox {
      id: recentFilesComboBox
      Layout.fillWidth: true
      visible: root.recentFilesVisible
      enabled: Handlers.program.loadProgramAllowed
      model: Handlers.program.info.recentFiles
      displayText: Handlers.program.programLoaded ? (Handlers.conversational.programUnsaved ? qsTr("*unsaved program*") : Handlers.program.info.name) : ""

      onActivated: function (index) {
        var loadProgram = function () {
          Handlers.program.loadProgram(Handlers.program.info.recentPaths[index]);
        };
        if (Handlers.program.programLoaded) {
          Handlers.conversational.commitChanges(loadProgram, qsTr("loading program"));
        } else {
          loadProgram();
        }
      }

      Connections {
        target: Handlers.conversational
        function onProgramUnsavedChanged() {
          if (Handlers.conversational.programUnsaved) {
            // temporary unsaved program has been loaded
            deselectDelayTimer.start();
          }
        }
      }

      Connections {
        target: Handlers.program
        function onProgramLoadedChanged() {
          if (!Handlers.program.programLoaded) {
            // delay unloading since call might come while "onActivated" is running
            deselectDelayTimer.start();
          }
        }
      }

      Timer {
        id: deselectDelayTimer
        interval: 10
        repeat: false
        onTriggered: {
          recentFilesComboBox.currentIndex = -1;
        }
      }
    }

    ProgramCodeListView {
      id: programView
      Layout.fillWidth: true
      Layout.fillHeight: true

      model: ProgramCodeListModel {
        id: programCodeModel
        program: Handlers.program.program
      }

      Connections {
        target: Handlers.program.info.positionSync
        function onLineNumberChanged() {
          programView.selectLine(Handlers.program.info.positionSync.lineNumber);
        }
      }

      Text {
        id: emptyLabel
        text: qsTr("No program loaded")
        anchors.centerIn: parent
        visible: !Handlers.program.programLoaded
        font.family: Fonts.font2
        font.pixelSize: Fonts.programTreeView.size1
        color: Colors.black1
      }
    }

    RowLayout {
      id: mdiRow
      visible: root.mdiVisible

      MdiInputField {
        Layout.fillWidth: true
        implicitHeight: foldButton.height
      }

      FoldUnfoldButton {
        id: foldButton
        checked: true
        onClicked: {
          root.folded = !root.folded;
          checked = !root.folded;
        }
      }
    }
  }
}
