import QtQuick
import pathpilot.core

Rectangle {
  id: root
  property bool vertical: false
  height: vertical ? 50 : 1
  width: vertical ? 1 : 200
  color: Colors.gray1
}
