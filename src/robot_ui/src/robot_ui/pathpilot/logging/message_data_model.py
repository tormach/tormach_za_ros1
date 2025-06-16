from enum import IntEnum, auto
from PySide6.QtCore import (
    Qt,
    QByteArray,
    QEnum,
    Signal,
    Property,
    Slot,
    QModelIndex,
)
from PySide6.QtQml import QmlElement

from ..models.base_table_model import (
    BaseTableModel,
)
from .logging import LogSeverityLevel
from .message import Message


class MessageList:
    def __init__(self):
        self._messages = []

    def __getitem__(self, key):
        return self._messages[len(self._messages) - key - 1]

    def __delitem__(self, key):
        if isinstance(key, slice):
            assert key.step is None or key.step == 1, (
                'MessageList.__delitem__ not implemented for slices with step argument '
                'different than 1'
            )
            del self._messages[
                len(self._messages) - key.stop : len(self._messages) - key.start
            ]
        else:
            del self._messages[len(self._messages) - key - 1]

    def __iter__(self):
        return reversed(self._messages)

    def __reversed__(self):
        return iter(self._messages)

    def __contains__(self, item):
        return item in self._messages

    def __len__(self):
        return len(self._messages)

    def extend(self, item):
        self._messages.extend(item)


QML_IMPORT_NAME = 'pathpilot.logging'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class MessageDataModel(BaseTableModel):
    # based on: https://github.com/ros-visualization/rqt_console/blob/master/src/rqt_console/message_data_model.py
    class Roles(IntEnum):
        SortRole = Qt.UserRole
        TypeRole = auto()
        NumberRole = auto()
        FirstDataRole = auto()  # here begin the data field roles
        MessageRole = auto()
        ExtendedInfoRole = auto()
        SeverityRole = auto()
        NodeRole = auto()
        TimestampRole = auto()
        TopicsRole = auto()
        LocationRole = auto()
        IdRole = auto()
        LastDataRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.SortRole: QByteArray(b'sort'),
        Roles.TypeRole: QByteArray(b'type'),
        Roles.NumberRole: QByteArray(b'number'),
        Roles.MessageRole: QByteArray(b'message'),
        Roles.ExtendedInfoRole: QByteArray(b'extended'),
        Roles.SeverityRole: QByteArray(b'severity'),
        Roles.NodeRole: QByteArray(b'node'),
        Roles.TimestampRole: QByteArray(b'timestamp'),
        Roles.TopicsRole: QByteArray(b'topics'),
        Roles.LocationRole: QByteArray(b'location'),
        Roles.IdRole: QByteArray(b'id'),
    }

    DEFAULT_MESSAGE_LIMIT = 20000

    messageLimitChanged = Signal(int)
    highestSeverityChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages = MessageList()
        self._message_limit = self.DEFAULT_MESSAGE_LIMIT
        self._highest_severity = LogSeverityLevel.Debug

        self._role_names.update(self._ROLE_NAMES)

        self.modelReset.connect(self._reset_highest_severity)

    @Property(int, notify=messageLimitChanged)
    def messageLimit(self):
        return self._message_limit

    @messageLimit.setter
    def messageLimit(self, value):
        if value == self._message_limit:
            return
        self._message_limit = value
        self.messageLimitChanged.emit(value)
        self._enforce_message_limit(value)

    @Property(int, notify=highestSeverityChanged)
    def highestSeverity(self):
        return self._highest_severity

    @Slot()
    def _reset_highest_severity(self):
        self._highest_severity = LogSeverityLevel.Debug
        self.highestSeverityChanged.emit(self._highest_severity)

    def rowCount(self, parent=QModelIndex()):
        return len(self._messages) if parent == QModelIndex() else 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self._messages):
            return ""

        if role < self.Roles.FirstDataRole:
            field = self.Roles.FirstDataRole + index.column() + 1
        else:
            field = role

        if role == Qt.DisplayRole:
            return str(self._message_data(index.row(), role, field))
        elif role >= self.Roles.FirstDataRole:
            return self._message_data(index.row(), role, field)
        elif role == Qt.InitialSortOrderRole:
            return (
                Qt.DescendingOrder
                if field == self.Roles.TimestampRole
                else Qt.AscendingOrder
            )
        elif role == self.Roles.SortRole:
            return self.data(index, field)
        elif role == self.Roles.TypeRole:
            return self._role_names.get(field, None)
        else:
            return None

    def _message_data(self, row, role, field):
        msg = self._messages[row]  # type: Message
        if field == self.Roles.TimestampRole:
            if role == Qt.DisplayRole:
                return msg.get_stamp_string()
            else:
                return msg.get_stamp_for_compare()
        elif field == self.Roles.SeverityRole and role == Qt.DisplayRole:
            return Message.SEVERITY_LABELS[msg.severity]
        elif self.Roles.MessageRole <= field <= self.Roles.IdRole:
            return getattr(msg, str(self._role_names[field], 'utf-8'))
        else:
            return None

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._messages[row]
        except IndexError:
            return QModelIndex()
        else:
            return self.createIndex(row, column, item)

    def _enforce_message_limit(self, limit):
        if len(self._messages) > limit:
            self.beginRemoveRows(QModelIndex(), limit, len(self._messages) - 1)
            del self._messages[limit : len(self._messages)]
            self.endRemoveRows()

    def insert_rows(self, msgs):
        # never try to insert more messages than the limit
        if len(msgs) > self._message_limit:
            msgs = msgs[-self._message_limit :]
        # reduce model before insert
        limit = self._message_limit - len(msgs)
        self._enforce_message_limit(limit)
        # insert newest messages
        # note self._messages is reversed
        severity_updated = False
        self.beginInsertRows(QModelIndex(), 0, len(msgs) - 1)
        self._messages.extend(msgs)
        for msg in msgs:
            if msg.severity > self._highest_severity:
                self._highest_severity = LogSeverityLevel(msg.severity)
                severity_updated = True
        self.endInsertRows()
        if severity_updated:
            self.highestSeverityChanged.emit(self._highest_severity)

    def remove_rows(self, rowlist):
        """
        :param rowlist: list of row indexes, ''list(int)''
        :returns: True if the indexes were removed successfully, ''bool''
        """
        if len(rowlist) == 0:
            if len(self._messages) > 0:
                try:
                    self.beginRemoveRows(QModelIndex(), 0, len(self._messages))
                    del self._messages[0 : len(self._messages)]
                    self.endRemoveRows()
                except IndexError:
                    return False
        else:
            rowlist = list(set(rowlist))
            rowlist.sort(reverse=True)
            dellist = [rowlist[0]]
            for row in rowlist[1:]:
                if dellist[-1] - 1 > row:
                    if not self._remove_row_list(dellist):
                        return False
                    dellist = []
                dellist.append(row)
            if dellist and not self._remove_row_list(dellist):
                return False
        return True

    def _remove_row_list(self, dellist):
        self.beginRemoveRows(QModelIndex(), dellist[-1], dellist[0])
        del self._messages[dellist[-1] : dellist[0] + 1]
        self.endRemoveRows()

    @Slot()
    def removeAll(self):
        try:
            self.beginResetModel()
            del self._messages[0 : len(self._messages)]
            self.endResetModel()
        except IndexError:
            return False
        else:
            return True

    def get_selected_text(self, rowlist):
        """
        Returns an easily readable block of text for the currently selected rows
        :param rowlist: list of row indexes, ''list(int)''
        :returns: the text from those indexes, ''str''
        """
        text = None
        if len(rowlist) != 0:
            rowlist = list(set(rowlist))
            text = ''.join(
                self._messages[row].pretty_print() for row in rowlist
            )
        return text

    def get_time_range(self, rowlist):
        """
        :param rowlist: a list of row indexes, ''list''
        :returns: a tuple of min and max times in a rowlist in '(unix timestamp).(fraction of second)' format, ''tuple(str,str)''
        """
        min_ = float("inf")
        max_ = float("-inf")
        for row in rowlist:
            item = self._messages[row].time_as_datestamp()
            if float(item) > float(max_):
                max_ = item
            if float(item) < float(min_):
                min_ = item
        return min_, max_

    def get_unique_nodes(self):
        return {message.block for message in self._messages}

    def get_unique_severities(self):
        return {message.severity for message in self._messages}

    def get_unique_topics(self):
        topics = set()
        for message in self._messages:
            for topic in message.topics:
                topics.add(topic)
        return topics

    def get_message_between(self, start_time, end_time=None):
        """
        :param start_time: time to start in timestamp form (including decimal
        fractions of a second is acceptable, ''unixtimestamp''
        :param end_time: time to end in timestamp form (including decimal
        fractions of a second is acceptable, ''unixtimestamp'' (Optional)
        :returns: list of messages in the time range ''list[message]''
        """
        msgs = []
        for message in self._messages:
            msg_time = message.stamp[0] + float(message.stamp[1]) / 10**9
            if msg_time >= float(start_time) and (
                end_time is None or msg_time <= float(end_time)
            ):
                msgs.append(message)
        return msgs
