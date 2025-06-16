import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

Rectangle {
  id: root
  signal doubleClicked(int row)
  signal rightClicked(int row)

  property bool readOnly: false
  property alias model: listView.model
  color: Colors.white1
  clip: true

  readonly property QtObject _d: QtObject {
    id: d
    property double lineNrColumnWidth: ~~(Math.log(root.model.lineCount) / Math.LN10 + 1) * fontMetrics.averageCharacterWidth
  }

  function selectRow(row: int) {
    listView.currentIndex = row;
    listView.positionViewAtIndex(row, ListView.Center);
  }

  function selectLine(line: int) {
    root.selectRow(line - 1);
  }

  FontMetrics {
    id: fontMetrics
    font.family: Fonts.font2
    font.pixelSize: Fonts.programTreeView.size1
  }

  ListView {
    id: listView
    anchors.fill: parent
    currentIndex: -1

    delegate: Rectangle {
      id: item
      required property int index
      required property var display
      property ListView view: ListView.view
      implicitWidth: ListView.view.width
      implicitHeight: 25
      color: item.index == ListView.view.currentIndex ? Colors.green2 : Colors.white1

      RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Sizes.singleMargin
        anchors.rightMargin: Sizes.singleMargin
        spacing: Sizes.doubleSpacing

        Text {
          id: lineNrText
          Layout.preferredWidth: d.lineNrColumnWidth
          text: item.index + 1
          verticalAlignment: Text.AlignVCenter
          elide: Text.ElideRight
          font.pixelSize: Fonts.programTreeView.size1
          font.family: Fonts.font2
          color: Colors.black1
        }

        Text {
          Layout.fillWidth: true
          text: item.display
          verticalAlignment: Text.AlignVCenter
          elide: Text.ElideRight
          font.pixelSize: Fonts.programTreeView.size1
          font.family: Fonts.font2
          color: Colors.black1
        }
      }

      MouseArea {
        anchors.fill: parent

        onClicked: function (mouse) {
          item.forceActiveFocus();
          if (mouse.button == Qt.LeftButton) {
            root.selectRow(item.index, mouse.modifiers);
          } else {
            root.rightClicked(item.index);
          }
        }

        onDoubleClicked: root.doubleClicked(item.index)
      }
    }

    ScrollBar.horizontal: ScrollBar {
      policy: ScrollBar.AlwaysOff
    }

    ScrollBar.vertical: ScrollBar {
      snapMode: ScrollBar.SnapAlways
      policy: ScrollBar.AlwaysOn
    }
  }

  MouseArea {
    anchors.fill: parent
    enabled: root.readOnly
  }
}
