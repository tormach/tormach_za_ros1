import QtQuick
import QtQuick.Shapes
import pathpilot.core

PathPilotTriangleIndicator {
  id: root
  property bool expanded: false
  rotation: expanded ? 0 : -90
}
