import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.frame

PathPilotPopup {
  id: root
  property Frames frames: null
  property string defaultModelTypeName: "none"
  property var frameModel: [defaultModelTypeName].concat(frames.frameNames)
  property string name: ""
  property string modelType: ""
  property alias applyFrame: applyFrameCheck.checked
  property var pose: [0, 0, 0, 0, 0, 0]

  signal accepted

  onFrameModelChanged: modelTypeCombo.model = frameModel
  onModelTypeChanged: modelTypeCombo.selectByText(modelType)
  onOpened: {
    modelTypeCombo.forceActiveFocus();
  }

  RowLayout {
    PathPilotLabel {
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      font.bold: true
      text: qsTr("Model:")
    }

    PathPilotComboBox {
      id: modelTypeCombo
    }
  }

  PathPilotCheckBox {
    id: applyFrameCheck
    text: qsTr("Apply default frame")
    checked: true
  }

  RowLayout {
    HorizontalFiller {
    }

    PathPilotButton {
      id: cancelButton
      text: qsTr("Cancel")
      onClicked: root.close()
    }

    PathPilotButton {
      id: okButton
      enabled: root.text !== ""
      text: qsTr("OK")
      onClicked: {
        root.close();
        root.modelType = (modelTypeCombo.currentText == root.defaultModelTypeName) ? "" : modelTypeCombo.currentText;
        if (root.applyFrame) {
          root.pose = root.frames.getFramePose(root.modelType);
        }
        root.accepted();
      }
    }
  }
}
