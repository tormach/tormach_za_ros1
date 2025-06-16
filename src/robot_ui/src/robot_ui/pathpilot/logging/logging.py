from enum import IntEnum
import rospy
from PySide6.QtCore import QEnum, QObject, Slot
from PySide6.QtQml import QmlElement, QmlSingleton, QmlUncreatable
from rosgraph_msgs.msg import Log

from .message import Message


class ExtendedMessage(Message):
    MESSAGE_SEPARATOR = '\n-- EXTENDED INFO --\n'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.extended = None

    def pretty_print(self):
        return f'{super().pretty_print()}{self.extended}'


class LogSeverityLevel(IntEnum):
    Debug = rospy.DEBUG
    Info = rospy.INFO
    Warn = rospy.WARN
    Error = rospy.ERROR
    Fatal = rospy.FATAL


QML_IMPORT_NAME = 'pathpilot.logging'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlUncreatable("LogLevel is an enum type")
class LogLevel(QObject):
    QEnum(LogSeverityLevel)


@QmlElement
@QmlSingleton
class Logging(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    @Slot(str, int)
    def log(self, message, level):
        switch = {
            LogSeverityLevel.Debug: rospy.logdebug,
            LogSeverityLevel.Info: rospy.loginfo,
            LogSeverityLevel.Warn: rospy.logwarn,
            LogSeverityLevel.Error: rospy.logerr,
            LogSeverityLevel.Fatal: rospy.logfatal,
        }
        switch.get(level, lambda _: None)(message)

    @staticmethod
    def convert_rosgraph_log_message(log_msg: Log):
        msg = ExtendedMessage()
        msg.set_stamp_format('hh:mm:ss.ZZZ (yyyy-MM-dd)')
        extended_index = log_msg.msg.find(ExtendedMessage.MESSAGE_SEPARATOR)
        if extended_index != -1:
            msg.message = log_msg.msg[:extended_index]
            msg.extended = log_msg.msg[
                extended_index + len(ExtendedMessage.MESSAGE_SEPARATOR) :
            ]
        else:
            msg.message = log_msg.msg
            msg.extended = ""
        msg.severity = log_msg.level
        msg.node = log_msg.name
        msg.stamp = (log_msg.header.stamp.secs, log_msg.header.stamp.nsecs)
        msg.topics = sorted(log_msg.topics)
        msg.location = f'{log_msg.file}:{log_msg.function}:{str(log_msg.line)}'
        return msg
