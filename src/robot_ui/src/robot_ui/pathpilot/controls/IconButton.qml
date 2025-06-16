import QtQuick

Item {
  id: root
  property var normalIcon: Icons.button.normal
  property var checkedIcon: normalIcon
  property var inactiveIcon: normalIcon
  property bool checked: false
  property bool checkable: false
  property alias pressed: mouseArea.pressed

  property int mouseMargin: 0 // margin if icon has shadow

  signal clicked
  implicitWidth: icon.width
  implicitHeight: icon.height
  opacity: enabled ? 1.0 : (!d.hasInactive ? Colors.disabledOpacity : 1.0)

  QtObject {
    id: d
    readonly property bool hasInactive: (normalIcon.source !== inactiveIcon.source)
  }

  Icon {
    id: icon
    icon: (enabled || !d.hasInactive) ? (checked || pressed) ? checkedIcon : normalIcon : inactiveIcon
  }

  MouseArea {
    id: mouseArea
    anchors.fill: icon
    anchors.margins: root.mouseMargin
    cursorShape: Qt.PointingHandCursor
    onClicked: {
      root.clicked();
      if (root.checkable) {
        root.checked = !root.checked;
      }
    }
  }
}
