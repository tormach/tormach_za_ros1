import QtQuick
import QtQuick.Controls
import pathpilot.controls
import pathpilot.logging

PathPilotComboBox {
  id: root
  readonly property int level: model.get(currentIndex).level
  implicitWidth: 160
  textRole: "text"
  currentIndex: 2
  model: ListModel {
    ListElement {
      text: qsTr("Debug")
      level: LogLevel.Debug
    }
    ListElement {
      text: qsTr("Info")
      level: LogLevel.Info
    }
    ListElement {
      text: qsTr("Warning")
      level: LogLevel.Warn
    }
    ListElement {
      text: qsTr("Error")
      level: LogLevel.Error
    }
    ListElement {
      text: qsTr("Fatal")
      level: LogLevel.Fatal
    }
  }
}
