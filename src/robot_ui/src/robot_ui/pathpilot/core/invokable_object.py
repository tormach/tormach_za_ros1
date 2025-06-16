from PySide6.QtCore import QObject, Signal
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class InvokableObject(QObject):
    """
    Object which provides generic signals to invoke functions in QML.
    """

    callArg0 = Signal(str, arguments=['name'])
    callArg1 = Signal(str, 'QVariant', arguments=['name', 'arg1'])
    callArg2 = Signal(
        str, 'QVariant', 'QVariant', arguments=['name', 'arg1', 'arg2']
    )
    callArg3 = Signal(
        str,
        'QVariant',
        'QVariant',
        'QVariant',
        arguments=['name', 'arg1', 'arg2', 'arg3'],
    )
    callArg4 = Signal(
        str,
        'QVariant',
        'QVariant',
        'QVariant',
        'QVariant',
        arguments=['name', 'arg1', 'arg2', 'arg3', 'arg4'],
    )

    def __init__(self, parent=None):
        super().__init__(parent)
