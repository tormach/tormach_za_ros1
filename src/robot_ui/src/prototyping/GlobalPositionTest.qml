import QtQuick
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.preview

UnscaledTestBase {
  id: root

  TabBar {
    id: bar
    width: parent.width
    currentIndex: 0

    TabButton {
      text: "One"
    }
    TabButton {
      text: "Two"
    }
    TabButton {
      text: "Three"
    }
    TabButton {
      text: "Four"
    }
  }

  StackLayout {
    id: stack
    currentIndex: bar.currentIndex
    anchors.right: parent.right
    anchors.left: parent.left
    anchors.bottom: parent.bottom
    anchors.top: bar.bottom
    anchors.margins: 20

    Rectangle {
      id: panel
      color: "orange"

      PathPilotCheckBox {
        id: checkBox
        text: "Start RViz"
        anchors.centerIn: parent
        checked: rvizProcess.active

        Binding {
          target: rvizProcess
          property: "active"
          value: checkBox.checked
        }
      }

      Rectangle {
        id: controller
        width: 250
        height: 200
        color: "red"

        GlobalPositionController {
          id: globalPositionController
          source: controller
          target: globalPositionObject
          active: controller.visible
        }
      }
    }

    Rectangle {
      id: panel2
      color: "magenta"

      Rectangle {
        id: controller2
        anchors.centerIn: parent
        width: 500
        height: 100
        color: "blue"

        GlobalPositionController {
          id: globalPositionController2
          source: controller2
          target: globalPositionObject
          active: controller2.visible
        }
      }
    }

    Rectangle {
      id: panel3
      color: "brown"
    }

    Rectangle {
      id: panel4
      color: "lightgreen"

      ScaleContainer {
        anchors.fill: parent
        anchors.margins: 50
        scale: 0.6

        Rectangle {
          id: controller3
          anchors.fill: parent
          color: "blue"

          GlobalPositionController {
            id: globalPositionController3
            source: controller3
            target: globalPositionObject
            active: controller3.visible
          }
        }
      }
    }
  }

  GlobalPositionObject {
    id: globalPositionObject
    target: windowController
    //target: previewWindow //niceLoader.item
    onActiveChanged: function (active) {
      if (active) {
        windowController.active = true;
      }
    }
    //niceLoader.active = true
  }

  WindowController {
    id: windowController
    width: 100
    height: 100
    winId: windowIdSubscriber.winId
  }

  WindowIdSubscriber {
    id: windowIdSubscriber
    topic: "/rviz/window_id" //"/window_test/window_id"
  }

  // needs to be placed after the window controller for proper cleanup
  SystemProcess {
    id: rvizProcess
    command: "rosrun rviz rviz -s \"\" -d /home/alexander/repos/tormach/ros-work1/src/robot_ui/config/empty.rviz -e __name:=rviz"
  }

  Loader {
    id: niceLoader
    active: false
    sourceComponent: rectComponent
  }

  Component {
    id: rectComponent
    Rectangle {

      width: 100
      height: 100
      visible: false
      color: "green"
    }
  }
}
