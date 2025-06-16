import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.file

ColumnLayout {
  id: root
  property var leftSelection
  property var rightSelection

  signal copyLeftToRight
  signal copyRightToLeft

  readonly property QtObject _d: QtObject {
    id: d
    property bool rightToLeft: false
  }

  CopyFromToButton {
    id: copyFromRightToLeftButton

    icon_: Icons.filepanel.left
    enabled: rightSelection.files.length > 0
    onClicked: {
      collisionChecker.sourceSelection = rightSelection;
      collisionChecker.targetSelection = leftSelection;
      collisionChecker.update();
      if (collisionChecker.hasCollisions) {
        d.rightToLeft = true;
        collisionPopup.open();
      } else {
        root.copyRightToLeft();
      }
    }
    PathPilotToolTip {
      itemId: "msg_copy_external_to_pp"
    }
  }

  CopyFromToButton {
    id: copyFromLeftToRightButton
    icon_: Icons.filepanel.right
    enabled: leftSelection.files.length > 0
    onClicked: {
      collisionChecker.sourceSelection = leftSelection;
      collisionChecker.targetSelection = rightSelection;
      collisionChecker.update();
      if (collisionChecker.hasCollisions) {
        d.rightToLeft = false;
        collisionPopup.open();
      } else {
        root.copyLeftToRight();
      }
    }

    PathPilotToolTip {
      itemId: "msg_copy_pp_to_external"
    }
  }

  FileCollisionChecker {
    id: collisionChecker
    sourceSelection: leftSelection
    targetSelection: rightSelection
  }

  FileCollisionPopup {
    id: collisionPopup
    collisions: collisionChecker.collisions
    onAccepted: {
      if (d.rightToLeft) {
        root.copyRightToLeft();
      } else {
        root.copyLeftToRight();
      }
    }
  }
}
