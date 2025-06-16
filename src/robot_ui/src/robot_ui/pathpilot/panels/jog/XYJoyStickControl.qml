import QtQuick

Item {
  id: root

  /*! This property holds the maximum alowed value in x and y direction.
        The output value is in the range of  - \c maximumValue to \c{maximumValue}.

        The default value is \c{100}.
    */
  property double maximumValue: 100.0

  /*! This property holds the output value step size.

      The default value is \c{1}.
    */
  property double stepSize: 1.0

  /*! This property holds wheter the joystick should be automacially fall back
        to the center position or not.

        The default value is \c{true}.
    */
  property bool autoCenter: true

  /*! This property holds joystick position in x direction
    */
  property double xValue: 0

  /*! This property holds joystick position in y direction
    */
  property double yValue: 0

  /*! This property holds whether the x axis should be enabled or not.
        The joystick will not move on this axis if disabled.

        The default value is \c{true}.
    */
  property bool xEnabled: true

  /*! This property holds whether the x axis should be enabled or not.
        The joystick will not move on this axis if disabled.

        The default value is \c{true}.
    */
  property bool yEnabled: true

  property double threshold: 50.0

  property bool hoverEnabled: false

  readonly property bool xPlusActive: xValue > threshold && controlArea.pressed
  readonly property bool xMinusActive: -xValue > threshold && controlArea.pressed
  readonly property bool yPlusActive: yValue > threshold && controlArea.pressed
  readonly property bool yMinusActive: -yValue > threshold && controlArea.pressed
  readonly property bool xPlusHovered: xValue > threshold && controlArea.containsMouse
  readonly property bool xMinusHovered: -xValue > threshold && controlArea.containsMouse
  readonly property bool yPlusHovered: yValue > threshold && controlArea.containsMouse
  readonly property bool yMinusHovered: -yValue > threshold && controlArea.containsMouse
  width: 430
  height: 430

  QtObject {
    id: d
    readonly property int centeredX: (root.width - control.width) / 2
    readonly property int centeredY: (root.height - control.height) / 2
    readonly property double maxX: root.width - control.width
    readonly property double maxY: root.height - control.height
    readonly property double maxControlX: (control.width - root.width) / 2
    readonly property double maxControlY: (control.height - root.height) / 2

    function calculateNewX() {
      if (root.xEnabled) {
        var newControlX = 0;
        newControlX = controlArea.mouseX - control.width / 2;
        if (newControlX > maxX) {
          newControlX = maxX;
        } else if (newControlX < 0) {
          newControlX = 0;
        }
        control.x = newControlX;
      }
    }

    function calculateNewY() {
      if (root.yEnabled) {
        var newControlY = 0;
        newControlY = controlArea.mouseY - control.height / 2;
        if (newControlY > maxY) {
          newControlY = maxY;
        } else if (newControlY < 0) {
          newControlY = 0;
        }
        control.y = newControlY;
      }
    }
  }

  Binding {
    target: root
    property: "yValue"
    value: -(Math.floor(((control.y + d.maxControlY) / Math.abs(d.maxControlY) * root.maximumValue) / root.stepSize) * root.stepSize)
    when: root.hoverEnabled || controlArea.pressed
  }

  Binding {
    target: root
    property: "xValue"
    value: (Math.floor(((control.x + d.maxControlX) / Math.abs(d.maxControlX) * root.maximumValue) / root.stepSize) * root.stepSize)
    when: root.hoverEnabled || controlArea.pressed
  }

  Rectangle {
    id: knobShadow
    anchors.centerIn: control
    anchors.verticalCenterOffset: root.yValue / root.maximumValue * 20
    anchors.horizontalCenterOffset: -root.xValue / root.maximumValue * 20
  }

  Rectangle {
    id: control
    property bool movable: false
    x: d.centeredX
    y: d.centeredY
    z: 1
  }

  MouseArea {
    id: controlArea

    anchors.fill: parent
    enabled: root.enabled
    hoverEnabled: true

    onPressedChanged: {
      if (pressed) {
        control.movable = true;
        d.calculateNewX();
        d.calculateNewY();
      } else {
        control.movable = false;
        if (root.autoCenter) {
          control.x = d.centeredX;
          control.y = d.centeredY;
        }
      }
    }

    onPositionChanged: {
      if (root.hoverEnabled) {
        d.calculateNewX();
        d.calculateNewY();
      }
    }

    onMouseXChanged: {
      if (root.hoverEnabled && control.movable) {
        d.calculateNewX();
      }
    }

    onMouseYChanged: {
      if (root.hoverEnabled && control.movable) {
        d.calculateNewY();
      }
    }
  }
}
