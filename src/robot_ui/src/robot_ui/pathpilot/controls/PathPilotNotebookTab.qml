import QtQuick
import pathpilot.core

Rectangle {
  id: root
  property string title: ""
  property var icon: IconObject {
  }
  property bool highlighted: false // set when a tab is highlighted
  property color highlightedColor: Colors.red1 // the highlight color
  property bool focused: false // set when a tab has focus

  signal forceFocus
  signal releaseFocus

  color: Colors.white3
}
