import QtQuick
import pathpilot.core

QtObject {
  Component.onCompleted: {
    for (var key in parsedArguments) {
      processOption(key, parsedArguments[key]);
    }
  }

  function processOption(option, argument) {
    if (option === "test_deployment") {
      if (argument === true) {
        Qt.quit();
      }
    }
  }
}
