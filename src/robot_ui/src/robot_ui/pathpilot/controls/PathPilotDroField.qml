import QtQuick
import QtQuick.Window
import QtQuick.Controls
import pathpilot.core
import pathpilot.controls

PathPilotTextField {
  id: root
  property int decimals: 4
  property double value: 0.0
  property double from: -Number.MAX_VALUE
  property double to: Number.MAX_VALUE

  signal valueUpdated(double value)
  horizontalAlignment: Text.AlignRight

  Binding {
    root.text: d.toFixed(root.value)
    when: !root.activeFocus
    restoreMode: Binding.RestoreBinding
  }

  QtObject {
    id: d
    readonly property bool error: !root.acceptableInput || evalError
    property bool evalError: false
    readonly property double threshold: Math.pow(10, -root.decimals)
    readonly property string zeros: "0" + (root.decimals ? "." : "") + "0".repeat(root.decimals)

    function resetValue() {
      root.text = d.toFixed(root.value);
    }

    // JS toFixed may return -0.0000, we always want 0.0000
    function toFixed(value: double) {
      if (Math.abs(value) < d.threshold) {
        return d.zeros;
      } else {
        return value.toFixed(root.decimals);
      }
    }
  }

  onEditingFinished: {
    if (readOnly) {
      return;
    }
    var result = null;
    result = DroMath.evaluate(text, String(root.value));
    if (result === undefined) {
      d.evalError = true;
    } else {
      var newText = d.toFixed(result);
      var newValue = Number(newText);
      if (newValue < root.from || newValue > root.to) {
        d.evalError = true;
      } else {
        d.evalError = false;
        if (newValue !== value) {
          root.valueUpdated(newValue);
        }
      }
    }
  }

  function validate() {
    var result = DroMath.evaluate(text, String(root.value));
    error = result === undefined || (result < root.from || result > root.to);
  }

  onTextChanged: validate()
}
