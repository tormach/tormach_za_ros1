import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import launcher_ui.logic 1.0
import QtScxml

Item {
  id: root
  property StateMachine stateMachine
  property Item buttonContainer
  property bool attention: false

  readonly property QtObject _d: QtObject {
    id: d

    function checkConnection() {
      internetChecker.check();
    }

    function noConnectionAvailable() {
      root.stateMachine.submitEvent("internet_not_available");
    }

    function connectionAvailable() {
      root.stateMachine.submitEvent("internet_available");
    }
  }

  onVisibleChanged: {
    if (visible) {
      d.checkConnection();
    }
  }

  InternetChecker {
    id: internetChecker

    onCheckCompleted: function (status) {
      if (status) {
        d.connectionAvailable();
      } else {
        d.noConnectionAvailable();
      }
    }
  }

  ColumnLayout {
    anchors.fill: parent
    spacing: Sizes.doubleSpacing

    VerticalFiller {
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("Checking the internet connection")
    }

    PathPilotBusyIndicator {
      Layout.alignment: Qt.AlignHCenter
    }

    VerticalFiller {
    }
  }
}
