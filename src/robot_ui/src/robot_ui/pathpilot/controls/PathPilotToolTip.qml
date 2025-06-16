import QtQuick
import QtQuick.Controls
import QtQuick.Templates as T
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers

T.ToolTip {
  id: control
  scale: Sizes.scale
  delay: 1200
  visible: false
  enabled: visible
  transformOrigin: Item.TopLeft

  x: x_positioning()
  y: y_positioning()

  implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset, contentWidth + leftPadding + rightPadding)
  implicitHeight: initHeight()
  leftPadding: Sizes.doubleMargin
  rightPadding: Sizes.doubleMargin

  enum Side {
    Left,
    Top,
    Right,
    Bottom
  }

  property int test: PathPilotToolTip.Side.Right

  // Tooltip controls
  property int sidePosition: PathPilotToolTip.Side.Right
  property int xOffset: 0
  property int yOffset: 0

  // Tooltip notch controls
  property int notchPosX: 0
  property int notchPosY: 0
  property int notchMargin: 10

  property alias itemId: toolTipInfo.itemId
  text: toolTipInfo.shortTextId ? qsTrId(toolTipInfo.shortTextId) : ""
  property string bodyText: toolTipInfo.longTextId !== "" ? toolTipInfo.prepareBodyText(qsTrId(toolTipInfo.longTextId), shortTextText.text) : ""
  property bool activationActor: parent?.hovered ?? false
  readonly property bool _ready: text !== "" && (activationActor || contentItem.containsMouse)

  function x_positioning() {
    if (sidePosition === PathPilotToolTip.Side.Right) {
      return (parent.width + Sizes.singleSpacing + 5) + xOffset;
    } else if (sidePosition === PathPilotToolTip.Side.Left) {
      return (-implicitWidth - Sizes.singleSpacing - 5) + xOffset;
    } else {
      return (parent.width / 2) + xOffset;
    }
  }

  function y_positioning() {
    if (sidePosition === PathPilotToolTip.Side.Bottom) {
      return parent.height + notchMargin + yOffset;
    } else if (sidePosition === PathPilotToolTip.Side.ToolTip) {
      return -notchMargin + yOffset;
    } else if (!d.fullText || (control.bodyText === toolTipInfo.longTextId)) {
      // Only show header check
      return ((parent.height - implicitHeight) / 2) + yOffset;
    } else {
      return 0;
    }
  }

  function initHeight() {
    if (control.bodyText === toolTipInfo.longTextId) {
      // Only show header check
      return 25;
    }
    return Math.max(implicitBackgroundHeight + topInset + bottomInset, contentHeight + topPadding + bottomPadding);
  }

  readonly property QtObject d: QtObject {
    id: d
    property bool fullText: false

    function startTimer() {
      if (fullTextText.text !== "") {
        fullTextTimer.start();
      }
    }

    function stopTimer() {
      fullTextTimer.stop();
      d.fullText = false;
    }

    function openForumUrl() {
      var url = Config.data.ppHubUrl + "/api/v1/redir/pprobot/uiforum/" + control.itemId;
      if (Handlers.state.hubConnector.loggedIn) {
        url += "?hubauthtoken=" + Handlers.state.hubConnector.token;
      }
      ApplicationHelpers.openUrlWithDefaultApplication(url);
    }
  }

  on_ReadyChanged: {
    if (control._ready) {
      control.visible = control._ready;
      closeDelayTimer.stop();
    } else {
      closeDelayTimer.start();
    }
  }

  onVisibleChanged: {
    if (visible) {
      d.startTimer();
    } else {
      d.stopTimer();
    }
  }

  Timer {
    id: fullTextTimer
    interval: control.delay
    repeat: false
    onTriggered: {
      d.fullText = true;
      closeTimer.start();
    }
  }

  Timer {
    id: closeTimer
    interval: 30000
    repeat: false
    onTriggered: control.visible = false
  }

  Timer {
    id: closeDelayTimer
    interval: 500
    repeat: false
    onTriggered: {
      control.visible = false;
      closeTimer.stop();
    }
  }

  contentItem: MouseArea {
    id: contentMouseArea
    implicitWidth: container.width
    implicitHeight: container.height + (d.fullText ? control.parent.height / 2.0 : 0.0)
    hoverEnabled: true

    Column {
      id: container
      Text {
        id: shortTextText
        anchors.right: parent.right
        anchors.left: parent.left
        height: buttonRow.buttonsVisible ? buttonRow.height : implicitHeight
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        text: control.text
        font: toolTipInfo.headerFont
        color: toolTipInfo.headerColor

        Row {
          id: buttonRow
          readonly property bool buttonsVisible: forumButton.visible
          anchors.right: parent.right
          spacing: 0

          Button {
            id: forumButton
            width: height
            visible: d.fullText
            flat: true
            icon.source: Icons.tooltips.forum.source
            icon.color: "transparent"
            hoverEnabled: true

            onClicked: d.openForumUrl()

            ToolTip.toolTip.scale: Sizes.scale
            ToolTip.delay: 100
            ToolTip.timeout: closeTimer.interval
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Discuss online")
          }
        }
      }

      Text {
        id: fullTextText
        visible: d.fullText && (control.bodyText !== toolTipInfo.longTextId)
        width: toolTipInfo.itemId !== "" ? toolTipInfo.longWidth : 1
        wrapMode: Text.Wrap
        text: control.bodyText
        font: toolTipInfo.bodyFont
        color: toolTipInfo.bodyColor
      }

      Item {
        width: fullTextText.width
        height: 1
      }
    }

    onClicked: {
      if (control.parent.onClicked !== undefined) {
        control.parent.onClicked();
      }
    }
    onDoubleClicked: {
      if (control.parent.onDoubleClicked !== undefined) {
        control.parent.onDoubleClicked();
      }
    }
    onPressed: {
      if (control.parent.onPressed !== undefined) {
        control.parent.onPressed();
      }
    }
    onReleased: {
      if (control.parent.onReleased !== undefined) {
        control.parent.onReleased();
      }
    }
  }

  background: Item {
    property int widthDiff: d.fullText ? 0 : fullTextText.width - shortTextText.width
    height: control.height
    width: control.width - widthDiff
    x: widthDiff / 2
    Rectangle {
      anchors.fill: parent
      color: Colors.white1
      radius: 8
      border.color: Colors.gray1
    }

    Rectangle {
      id: rect1
      rotation: 45
      x: control.notchPosX
      y: control.notchPosY || (control.parent ? -control.y + (control.parent.height / 2) - 6 : 0)

      anchors.left: ([PathPilotToolTip.Side.Top, PathPilotToolTip.Side.Bottom].includes(control.sidePosition)) ? undefined : ((control.sidePosition == PathPilotToolTip.Side.Right) ? parent.left : undefined)
      anchors.right: ([PathPilotToolTip.Side.Top, PathPilotToolTip.Side.Bottom].includes(control.sidePosition)) ? undefined : ((control.sidePosition == PathPilotToolTip.Side.Left) ? parent.right : undefined)

      anchors.top: ([PathPilotToolTip.Side.Left, PathPilotToolTip.Side.Right].includes(control.sidePosition)) ? undefined : ((control.sidePosition == PathPilotToolTip.Side.Bottom) ? parent.top : undefined)
      anchors.bottom: ([PathPilotToolTip.Side.Left, PathPilotToolTip.Side.Right].includes(control.sidePosition)) ? undefined : ((control.sidePosition == PathPilotToolTip.Side.Top) ? parent.bottom : undefined)

      anchors.leftMargin: (control.sidePosition == PathPilotToolTip.Side.Right) ? -4 : undefined
      anchors.rightMargin: (control.sidePosition == PathPilotToolTip.Side.Left) ? -4 : undefined
      anchors.topMargin: (control.sidePosition == PathPilotToolTip.Side.Bottom) ? -4 : undefined
      anchors.bottomMargin: (control.sidePosition == PathPilotToolTip.Side.Left) ? -4 : undefined
      width: 12
      height: width
      color: Colors.white1
    }
    Rectangle {
      z: -1
      rotation: 45
      anchors.centerIn: rect1
      width: rect1.width + 1
      height: width
      color: Colors.gray1
    }
  }

  ToolTipInfo {
    id: toolTipInfo
  }
}
