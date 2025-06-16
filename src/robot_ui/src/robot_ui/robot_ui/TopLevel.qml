import QtQuick
import pathpilot.base
import pathpilot.core
import pathpilot.controls
import pathpilot.screens.main
import pathpilot.handlers

Rectangle {
  id: root
  property string title: qsTr("PathPilot Robot Edition")
  width: 1920
  height: 1080
  visible: true
  color: Colors.gray5

  ProgramHandler {
    id: programHandler
    programModified: conversationalHandler.programModified
    programWriting: conversationalHandler.programWriting
  }

  ConversationalHandler {
    id: conversationalHandler
    programHandler: programHandler
    stateHandler: Handlers.state
  }

  AppHandler {
    id: appHandler
    programHandler: programHandler
    stateHandler: Handlers.state
    jogHandler: Handlers.jog
  }

  Loader {
    id: loader
    anchors.fill: parent
    sourceComponent: container
    active: false

    Component {
      id: container
      ScaleContainer {
        MainScreen {
          id: ui
          anchors.fill: parent
        }
      }
    }
  }

  ApplicationArguments {
  }

  Component.onCompleted: {
    Handlers.program = programHandler;
    Handlers.conversational = conversationalHandler;
    Handlers.app = appHandler;
    loader.active = true;
  }
}
