pragma Singleton
import QtQuick
import pathpilot.base

QtObject {
  id: root
  readonly property QtObject general: QtObject {
    readonly property string background: root.getJpgIcon("general", "dark_background")
  }

  readonly property QtObject splashscreen: QtObject {
    readonly property string icon1: root.getPngIcon("splashscreen", "TorMAX-770-Enclosure_Mill-Splashscreen-Version-2")
  }

  readonly property QtObject buttons: QtObject {
    readonly property string pressed: root.getPngIcon("buttons", "Blank-Pressed")
    readonly property string hovered: root.getPngIcon("buttons", "Blank-Hover")
    readonly property string normal: root.getPngIcon("buttons", "Blank-Normal")
  }

  readonly property QtObject rightpanel: QtObject {
    readonly property IconObject icon1: IconObject {
      size: "109x27"
      source: root.getJpgIcon("rightpanel", "pathpilot")
    }
  }

  readonly property QtObject rvizpreview: QtObject {
    readonly property IconObject global: IconObject {
      size: "32x32"
      source: root.getSvgIcon("preview", "global-waypoint")
    }

    readonly property IconObject globalDisabled: IconObject {
      size: "32x32"
      source: root.getSvgIcon("preview", "global-waypoint-disabled")
    }

    readonly property IconObject program: IconObject {
      size: "32x32"
      source: root.getSvgIcon("preview", "program-waypoint")
    }

    readonly property IconObject programDisabled: IconObject {
      size: "32x32"
      source: root.getSvgIcon("preview", "program-waypoint-disabled")
    }
  }

  readonly property QtObject mainpanel: QtObject {
    readonly property IconObject icon10: IconObject {
      size: "18x38"
      source: root.getSvgIcon("mainpanel", "left-chevron")
    }
    readonly property IconObject icon11: IconObject {
      size: "18x38"
      source: root.getSvgIcon("mainpanel", "right-chevron")
    }
  }

  readonly property QtObject filepanel: QtObject {
    readonly property IconObject home: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "go-home")
    }
    readonly property IconObject folder: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "folder-green")
    }
    readonly property IconObject rename: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "edit-rename")
    }
    readonly property IconObject delete_: IconObject {
      size: "48x48"
      source: root.getSvgIcon("program", "edit-delete")
    }
    readonly property IconObject back: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "draw-arrow-back")
    }
    readonly property IconObject usb: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "drive-removable-media-usb-pendrive")
    }
    readonly property IconObject eject: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "media-eject")
    }
    readonly property IconObject left: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "go-previous")
    }
    readonly property IconObject right: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "go-next")
    }
    readonly property IconObject open: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "project-open")
    }
    readonly property IconObject save: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "document-save")
    }
    readonly property IconObject saveAs: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "document-save-as")
    }
    readonly property IconObject filter: IconObject {
      size: "32x32"
      source: root.getSvgIcon("filepanel", "view-filter")
    }
    readonly property IconObject hub: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "folder-remote")
    }
    readonly property IconObject online: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "user-online")
    }
    readonly property IconObject offline: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "user-offline")
    }
    readonly property IconObject refresh: IconObject {
      size: "48x48"
      source: root.getSvgIcon("filepanel", "view-refresh")
    }
    readonly property IconObject warning: IconObject {
      size: "24x24"
      source: root.getPngIcon("popup", "dialog-warning")
    }
    readonly property IconObject copy: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "edit-copy")
    }
  }

  readonly property QtObject program: QtObject {
    readonly property IconObject convEditFile: IconObject {
      size: "32x32"
      source: root.getPngIcon("program", "conv_edit_file_icon_32")
    }
    readonly property IconObject endMill: IconObject {
      size: "31x31"
      source: root.getPngIcon("program", "icon_end_mill.31")
    }
    readonly property IconObject faceMill: IconObject {
      size: "31x31"
      source: root.getPngIcon("program", "icon_face_mill.31")
    }
    readonly property IconObject undo: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "edit-undo")
    }
    readonly property IconObject redo: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "edit-redo")
    }
    readonly property IconObject delete_: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "edit-delete")
    }
    readonly property IconObject save: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "document-save")
    }
    readonly property IconObject saveAs: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "document-save-as")
    }
    readonly property IconObject new_: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "document-new")
    }
    readonly property IconObject up: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "go-up")
    }
    readonly property IconObject down: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "go-down")
    }
    readonly property IconObject copy: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "edit-copy")
    }
    readonly property IconObject cut: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "edit-cut")
    }
    readonly property IconObject paste: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "edit-paste")
    }
    readonly property IconObject toggleEnabled: IconObject {
      size: "48x48"
      source: root.getPngIcon("program", "toggle-enabled")
    }

    readonly property IconObject camera: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Camera")
    }
    readonly property IconObject closingGrip: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Closing_Grip")
    }
    readonly property IconObject condition: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "If-Else")
    }
    readonly property IconObject loop: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Loop")
    }
    readonly property IconObject notifyCommand: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Notify_Command")
    }
    readonly property IconObject notify: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Notify")
    }
    readonly property IconObject move: IconObject {
      size: "30x32"
      source: root.getJpgIcon("program", "Robot_Move")
    }
    readonly property IconObject moveDown: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Move_Down")
    }
    readonly property IconObject wait: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Waiting_on_Command")
    }
    readonly property IconObject mainProgram: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Main_Program_2")
    }
    readonly property IconObject subProgram: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Main_Program")
    }
    readonly property IconObject subroutine: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Step_Into_Subroutine")
    }
    readonly property IconObject empty: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "Empty_Node")
    }
    readonly property IconObject ifElse: IconObject {
      size: "30x32"
      source: root.getPngIcon("program", "If-Else")
    }
    readonly property IconObject warning: IconObject {
      size: "32x32"
      source: root.getPngIcon("popup", "dialog-warning")
    }
    readonly property IconObject blockCut: IconObject {
      size: "32x32"
      source: root.getPngIcon("program", "edit-cut")
    }
    readonly property IconObject blockCopy: IconObject {
      size: "32x32"
      source: root.getPngIcon("program", "edit-copy")
    }
  }

  readonly property QtObject jogpanel: QtObject {
    readonly property IconObject keyboard: IconObject {
      size: "48x48"
      source: root.getSvgIcon("jogpanel", "preferences-desktop-keyboard")
    }
  }

  readonly property QtObject popup: QtObject {
    readonly property IconObject notification: IconObject {
      size: "48x48"
      source: root.getPngIcon("popup", "dialog-information")
    }
    readonly property IconObject warning: IconObject {
      size: "48x48"
      source: root.getPngIcon("popup", "dialog-warning")
    }
    readonly property IconObject error: IconObject {
      size: "48x48"
      source: root.getPngIcon("popup", "dialog-error")
    }
  }

  readonly property QtObject tooltips: QtObject {
    readonly property IconObject forum: IconObject {
      size: "32x32"
      source: root.getPngIcon("popup", "dialog-information")
    }
  }

  function getPngIcon(category, name) {
    return ResourcePaths.iconPath + "/" + category + "/png/" + name + ".png";
  }

  function getJpgIcon(category, name) {
    return ResourcePaths.iconPath + "/" + category + "/jpg/" + name + ".jpg";
  }

  function getSvgIcon(category, name) {
    return ResourcePaths.iconPath + "/" + category + "/svg/" + name + ".svgz";
  }
}
