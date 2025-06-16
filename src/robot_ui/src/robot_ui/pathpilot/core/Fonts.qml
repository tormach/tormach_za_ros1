pragma Singleton
import QtQuick
import pathpilot.base

QtObject {
  id: root
  readonly property string font1: bebas.name
  readonly property string font2: notoSansRegular.name
  readonly property string font3: robotoCondensedRegular.name

  readonly property QtObject controls: QtObject {
    readonly property int button1: root.scaleFont(18)
    readonly property int toggleButton1: root.scaleFont(11)
    readonly property int label1: root.scaleFont(18)
    readonly property int textField1: root.scaleFont(20)
    readonly property int tabButton1: root.scaleFont(12)
    readonly property int slider1: root.scaleFont(20)
    readonly property int radioButton1: root.scaleFont(18)
    readonly property int tableView: root.scaleFont(14)
  }

  readonly property QtObject leftPanel: QtObject {
    readonly property int size1: root.scaleFont(24)
    readonly property int size2: root.scaleFont(18)
    readonly property int size3: root.scaleFont(11)
  }

  readonly property QtObject centerPanel: QtObject {
    readonly property int size1: root.scaleFont(22)
    readonly property int size2: root.scaleFont(20)
    readonly property int size3: root.scaleFont(36)
  }

  readonly property QtObject rightPanel: QtObject {
    readonly property int size1: root.scaleFont(14)
  }

  readonly property QtObject filePanel: QtObject {
    readonly property int size1: root.scaleFont(16)
    readonly property int size2: root.scaleFont(20)
    readonly property int size3: root.scaleFont(14)
  }

  readonly property QtObject statusPanel: QtObject {
    readonly property int size1: root.scaleFont(14)
  }

  readonly property QtObject mainPanel: QtObject {
    readonly property int size1: root.scaleFont(20)
    readonly property int size2: root.scaleFont(14)
  }

  readonly property QtObject jointPositionControl: QtObject {
    readonly property int size1: root.scaleFont(28)
    readonly property int size2: root.scaleFont(6)
    readonly property int size3: root.scaleFont(36)
    readonly property int size4: root.scaleFont(15)
  }

  readonly property QtObject jogControls: QtObject {
    readonly property int size1: root.scaleFont(16)
  }

  readonly property QtObject jogPanel: QtObject {
    readonly property int size1: root.scaleFont(16)
    readonly property int size2: root.scaleFont(20)
    readonly property int size3: root.scaleFont(18)
  }

  readonly property QtObject conversationalPanel: QtObject {
    readonly property int size1: root.scaleFont(16)
    readonly property int size2: root.scaleFont(14)
  }

  readonly property QtObject conversationalButtons: QtObject {
    readonly property int size1: root.scaleFont(16)
    readonly property int size2: root.scaleFont(14)
  }

  readonly property QtObject conversationalPopups: QtObject {
    readonly property int size1: root.scaleFont(16)
    readonly property int size2: root.scaleFont(18)
  }

  readonly property QtObject toolControls: QtObject {
    readonly property int size1: root.scaleFont(34)
    readonly property int size2: root.scaleFont(26)
    readonly property int size3: root.scaleFont(14)
    readonly property int size4: root.scaleFont(12)
    readonly property int size5: root.scaleFont(12)
    readonly property int size6: root.scaleFont(16)
  }

  readonly property QtObject versionInfo: QtObject {
    readonly property int size1: root.scaleFont(11)
  }

  readonly property QtObject exitButton: QtObject {
    readonly property int size1: root.scaleFont(16)
    readonly property int size2: root.scaleFont(16)
  }

  readonly property QtObject programTreeView: QtObject {
    readonly property int size1: root.scaleFont(14)
  }

  readonly property QtObject waypointTableView: QtObject {
    readonly property int size1: root.scaleFont(18)
  }

  readonly property QtObject frameTableView: QtObject {
    readonly property int size1: root.scaleFont(18)
  }

  readonly property QtObject preview: QtObject {
    readonly property int size1: root.scaleFont(12)
  }

  readonly property QtObject notificationPopup: QtObject {
    readonly property int size1: root.scaleFont(16)
    readonly property int size2: root.scaleFont(18)
  }

  readonly property QtObject launcher: QtObject {
    readonly property int size1: root.scaleFont(14)
    readonly property int size2: root.scaleFont(16)
  }

  readonly property FontLoader bebas: FontLoader {
    source: ResourcePaths.fontPath + "/Bebas.ttf"
  }

  readonly property FontLoader robotoCondensedRegular: FontLoader {
    source: ResourcePaths.fontPath + "/RobotoCondensed-Regular.ttf"
  }

  readonly property FontLoader notoSansRegular: FontLoader {
    source: ResourcePaths.fontPath + "/NotoSans-Regular.ttf"
  }

  function scaleFont(size) {
    return ~~(size * 1.0);
  }
}
