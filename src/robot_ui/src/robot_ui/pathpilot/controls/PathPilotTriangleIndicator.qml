import QtQuick
import QtQuick.Shapes
import pathpilot.core

Shape {
  id: root
  property color color: enabled ? Colors.black1 : Colors.gray5
  width: 12
  height: 8

  ShapePath {
    strokeWidth: 1
    strokeColor: root.color
    strokeStyle: ShapePath.SolidLine
    fillColor: root.color
    joinStyle: ShapePath.MiterJoin
    fillRule: ShapePath.WindingFill

    PathLine {
      x: root.width
    }
    PathLine {
      x: root.width / 2
      y: root.height
    }
    PathLine {
      x: 0
      y: 0
    }
  }
}
