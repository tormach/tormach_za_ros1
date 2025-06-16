import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

ColumnLayout {
  id: root
  spacing: Sizes.singleSpacing

  RowLayout {
    Layout.fillWidth: true
    Layout.fillHeight: false

    Text {
      text: SoftwareVersion.robot
      color: Colors.white2
      font.pixelSize: Fonts.versionInfo.size1
      font.family: Fonts.font1
    }

    Text {
      text: RosMasterURI.ros_master_uri
      color: Colors.white2
      font.pixelSize: Fonts.versionInfo.size1
      font.family: Fonts.font1
    }

    Item {
      Layout.fillWidth: true
    }
  }

  Text {
    Layout.fillWidth: true
    text: SoftwareVersion.version + " " + SoftwareVersion.codename
    color: Colors.white1
    font.pixelSize: Fonts.versionInfo.size1
    font.family: Fonts.font1
    elide: Text.ElideRight
  }
}
