import QtQuick
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.robot.frame
import pathpilot.models
import Qt.labs.qmlmodels

PathPilotTableView {
  id: root
  property QtObject frames: null // Frames type, prevent type conflict
  property bool modelTypeVisible: false

  signal updateFrameModelTypeRequested(string name, var pose, string modelType)
  model: sortFilterModel
  font.pixelSize: Fonts.frameTableView.size1
  fillColumn: 1

  readonly property QtObject _d: QtObject {
    id: d
    readonly property real valueFieldWidth: 100
    readonly property real nameFieldWidth: 80
    readonly property real modelTypeFieldWidth: 100

    function renameFrame(pose, oldName, newName) {
      frames.setFrame(newName, pose);
      frames.deleteFrame(oldName);
    }

    function setFrameAxis(name, axisIndex, value) {
      frames.setFrameAxis(name, axisIndex, value);
    }

    function setFrameDescription(name, pose, description) {
      frames.setFrame(name, pose, {
          "description": description
        });
    }

    function updateFrameModelType(name, pose, modelType) {
      root.updateFrameModelTypeRequested(name, pose, modelType);
    }
  }

  SortFilterProxyModel {
    id: sortFilterModel
    source: framesModel

    fields: {
      var data = [FrameTableModel.NameRole, FrameTableModel.DescriptionRole, FrameTableModel.XRole, FrameTableModel.YRole, FrameTableModel.ZRole, FrameTableModel.ARole, FrameTableModel.BRole, FrameTableModel.CRole];
      if (root.modelTypeVisible) {
        data.splice(2, 0, FrameTableModel.ModelTypeRole);
      }
      return data;
    }
    columnWidthOverrides: {
      "name": d.nameFieldWidth,
      "x": d.valueFieldWidth,
      "y": d.valueFieldWidth,
      "z": d.valueFieldWidth,
      "a": d.valueFieldWidth,
      "b": d.valueFieldWidth,
      "c": d.valueFieldWidth,
      "modelType": d.modelTypeFieldWidth
    }
    headerTitles: {
      "name": qsTr("Name"),
      "description": qsTr("Description"),
      "modelType": qsTr("Tool Model")
    }
  }

  FrameTableModel {
    id: framesModel
    frames: root.frames
  }

  delegate: DelegateChooser {
    role: "type"

    DelegateChoice {
      roleValue: "linear_number"
      PathPilotTableViewDelegateBase {
        id: item
        table: root
        onClicked: droField.forceActiveFocus()

        PathPilotDroField {
          id: droField
          anchors.fill: parent

          Binding {
            target: droField
            property: "value"
            value: Units.fromRos(Number(model.number), Config.user.linearUnit)
          }
          decimals: Config.data.dro.decimals[Config.user.linearUnit]
          color: error ? Colors.red1 : item.textColor
          background: Item {
          }

          onValueUpdated: function (value) {
            d.setFrameAxis(model.name, model.axis, Units.toRos(value, Config.user.linearUnit));
          }
        }
      }
    }

    DelegateChoice {
      roleValue: "angular_number"
      PathPilotTableViewDelegateBase {
        id: item
        table: root
        onClicked: droField.forceActiveFocus()

        PathPilotDroField {
          id: droField
          anchors.fill: parent

          Binding {
            target: droField
            property: "value"
            value: Units.fromRos(Number(model.number), Config.user.angularUnit)
          }
          decimals: Config.data.dro.decimals[Config.user.angularUnit]
          color: error ? Colors.red1 : item.textColor
          background: Item {
          }

          onValueUpdated: function (value) {
            d.setFrameAxis(model.name, model.axis, Units.toRos(value, Config.user.angularUnit));
          }
        }
      }
    }

    DelegateChoice {
      roleValue: "description"
      PathPilotTableViewDelegateBase {
        id: item
        table: root
        onClicked: textField.forceActiveFocus()

        PathPilotTextField {
          id: textField
          anchors.fill: parent
          text: model.display
          font: root.font
          horizontalAlignment: Text.AlignLeft
          color: item.textColor
          background: Item {
          }

          onEditingFinished: {
            if (text !== model.display) {
              d.setFrameDescription(model.name, model.pose, text);
            }
          }
        }
      }
    }

    DelegateChoice {
      roleValue: "name"
      PathPilotTableViewDelegateBase {
        id: item
        table: root
        onClicked: textField.forceActiveFocus()

        PathPilotTextField {
          id: textField
          anchors.fill: parent
          font: root.font
          horizontalAlignment: Text.AlignLeft
          color: error ? Colors.red1 : item.textColor
          background: Item {
          }

          Binding {
            target: textField
            property: "text"
            value: model.display
          }

          NameValidator {
            id: frameNameValidator
            names: frames.frameNames
            ignoredName: model.display
          }

          validator: FrameNameValidator {
          }

          function validate() {
            error = !frameNameValidator.validate(text, 0);
          }

          onTextEdited: {
            text = text.replace(/\s/g, '_');
            validate();
          }

          onEditingFinished: {
            if (error) {
              text = model.display;
              return;
            }
            if (text == model.display) {
              return;
            }
            d.renameFrame(model.pose, model.display, text);
          }
        }
      }
    }

    DelegateChoice {
      roleValue: "modelType"
      PathPilotTableViewDelegateBase {
        id: item
        table: root
        onClicked: d.updateFrameModelType(model.name, model.pose, model.modelType)

        Text {
          id: textField
          anchors.fill: parent
          text: model.display
          font: root.font
          verticalAlignment: Text.AlignVCenter
          elide: Text.ElideRight
          color: item.textColor
        }
      }
    }

    DelegateChoice {
      PathPilotTableViewDelegateBase {
        id: item
        table: root

        Text {
          anchors.fill: parent
          anchors.leftMargin: Sizes.singleMargin
          anchors.rightMargin: Sizes.singleMargin
          font: root.font
          verticalAlignment: Text.AlignVCenter
          text: model.display
          elide: Text.ElideRight
          color: item.textColor
        }
      }
    }
  }
}
