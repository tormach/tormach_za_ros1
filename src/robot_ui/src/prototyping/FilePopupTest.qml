import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.file
import pathpilot.development

ScaledTestBase {
  id: root

  DeleteFilePopup {
    id: deleteFilePopup
  }

  FileNamePopup {
    id: fileNamePopup
  }

  NewFilePopup {
    id: newFilePopup
    extension: ".py"
    onAccepted: function (path, name) {
      console.log(path);
    }
  }

  OpenFilePopup {
    id: openFilePopup
    fileFilter: ".*\\.py"
    onAccepted: function (path, name) {
      console.log(path);
    }
  }

  OverwriteWarningPopup {
    id: overwriteWarningPopup
    originalPath: "/foo/bar/program.py"
    onAccepted: function (path, name) {
      console.log(path);
    }
  }

  SaveModifiedWarningPopup {
    id: saveModifiedWarningPopup
  }

  Grid {
    anchors.centerIn: parent
    columns: 3
    spacing: Sizes.singleSpacing

    PathPilotButton {
      implicitWidth: 140
      text: "Set File Name"
      onClicked: fileNamePopup.open()
    }

    PathPilotButton {
      implicitWidth: 140
      text: "New File"
      onClicked: newFilePopup.open()
    }

    PathPilotButton {
      implicitWidth: 140
      text: "Open File"
      onClicked: openFilePopup.open()
    }

    PathPilotButton {
      implicitWidth: 140
      text: "Show Warning"
      onClicked: overwriteWarningPopup.open()
    }

    PathPilotButton {
      implicitWidth: 200
      text: "Delete File Warning"
      onClicked: deleteFilePopup.open()
    }

    PathPilotButton {
      implicitWidth: 220
      text: "Save Modified Warning"
      onClicked: saveModifiedWarningPopup.open()
    }
  }
}
