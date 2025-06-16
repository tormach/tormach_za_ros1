pragma Singleton
import QtQuick

QtObject {
  id: root

  readonly property int halfMargin: 3
  readonly property int singleMargin: 5
  readonly property int doubleMargin: 10

  readonly property int singleSpacing: 5
  readonly property int doubleSpacing: 10

  readonly property int thinBorder: 1
  readonly property int thickBorder: 2

  readonly property int controlHeight: 45

  readonly property int smallRadius: 2
  readonly property int bigRadius: 5

  property real scale: 1.0 // this value is updated by our ScaleContainer
}
