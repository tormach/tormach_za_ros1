import QtQuick
import pathpilot.controls

RegularExpressionValidator {
  id: root
  regularExpression: /(?!world\b)\b[A-Za-z_][0-9A-Za-z_ ]*/
}
