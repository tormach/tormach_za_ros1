import contextlib
from enum import IntEnum, auto
from PySide6.QtCore import (
    QByteArray,
    Qt,
    QEnum,
    Signal,
    Property,
    Slot,
    QModelIndex,
    QObject,
)
from PySide6.QtQml import QmlElement

from robot_ui.pathpilot.models.base_table_model import (
    BaseTableModel,
)

QML_IMPORT_NAME = 'pathpilot.robot.frame'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class FrameTableModel(BaseTableModel):
    class Roles(IntEnum):
        SortRole = Qt.UserRole
        TypeRole = auto()
        NumberRole = auto()
        AxisRole = auto()
        FirstDataRole = auto()  # here begins the data field roles
        NameRole = auto()
        PoseRole = auto()
        XRole = auto()
        YRole = auto()
        ZRole = auto()
        ARole = auto()
        BRole = auto()
        CRole = auto()
        DescriptionRole = auto()
        ModelTypeRole = auto()
        LastDataRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.SortRole: QByteArray(b'sort'),
        Roles.TypeRole: QByteArray(b'type'),
        Roles.NumberRole: QByteArray(b'number'),
        Roles.AxisRole: QByteArray(b'axis'),
        Roles.NameRole: QByteArray(b'name'),
        Roles.PoseRole: QByteArray(b'pose'),
        Roles.XRole: QByteArray(b'x'),
        Roles.YRole: QByteArray(b'y'),
        Roles.ZRole: QByteArray(b'z'),
        Roles.ARole: QByteArray(b'a'),
        Roles.BRole: QByteArray(b'b'),
        Roles.CRole: QByteArray(b'c'),
        Roles.DescriptionRole: QByteArray(b'description'),
        Roles.ModelTypeRole: QByteArray(b'modelType'),
    }

    framesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._frames = None
        self._frame_list = []

        self._role_names.update(self._ROLE_NAMES)

        self.framesChanged.connect(self._on_frames_reset)

    @Property(QObject, notify=framesChanged)  # Frames type
    def frames(self):
        return self._frames

    @frames.setter
    def frames(self, new_frames):
        if new_frames == self._frames:
            return
        old_frames = self._frames
        self._frames = new_frames
        self.framesChanged.emit()

        if old_frames:
            with contextlib.suppress(RuntimeError):
                old_frames.framesChanged.disconnect(self._on_frames_changed)
        if new_frames:
            new_frames.framesChanged.connect(self._on_frames_changed)

    @Slot()
    def _on_frames_reset(self):
        self.beginResetModel()
        self._frame_list = self._get_frames()
        self.endResetModel()

    def _on_frames_changed(self):
        old_frames = self._frame_list
        new_frames = self._get_frames()

        old_frame_names = {item[0] for item in old_frames}
        new_frame_names = {item[0] for item in new_frames}

        # Handle renames first by looking at frame data
        renamed = set()
        for new_name, new_data in new_frames:
            if new_name not in old_frame_names:
                # Look for a matching frame by comparing data
                for old_name, old_data in old_frames:
                    if (
                        old_name not in new_frame_names
                        and old_data == new_data
                        and old_name not in renamed
                    ):
                        # Found a rename
                        renamed.add(old_name)
                        # Update the name in the old frames list
                        idx = old_frames.index((old_name, old_data))
                        old_frames[idx] = (new_name, new_data)
                        # Emit data changed for this row
                        self.dataChanged.emit(
                            self.index(idx, 0),
                            self.index(idx, self.columnCount() - 1),
                        )
                        break

        # Now handle actual additions/removals/changes
        old_frame_names = {
            item[0] for item in old_frames
        }  # Recompute after renames
        new_frame_names = {item[0] for item in new_frames}

        added = new_frame_names - old_frame_names
        removed = old_frame_names - new_frame_names
        same = new_frame_names.intersection(old_frame_names)

        # Update changed frames (excluding renamed ones)
        changing = []
        new_values = {k: v for k, v in new_frames if k in same}

        def change(indizes):
            for index in indizes:
                name_ = old_frames[index][0]
                old_frames[index] = name_, new_values[name_]
            self.dataChanged.emit(
                self.index(indizes[0], 0),
                self.index(indizes[-1], self.columnCount() - 1),
            )
            del indizes[:]

        for i, item in enumerate(old_frames):
            name, value = item
            if name in same and value != new_values[name]:
                changing.append(i)
            elif changing:
                change(changing)
        if changing:
            change(changing)

        # Handle removals (excluding renamed frames)
        def remove(indizes):
            self.beginRemoveRows(QModelIndex(), indizes[0], indizes[-1])
            del old_frames[indizes[0] : indizes[-1] + 1]
            self.endRemoveRows()
            del indizes[:]

        removing = []
        for i, item in enumerate(old_frames):
            name = item[0]
            if name in removed and name not in renamed:
                removing.append(i)
            elif removing:
                remove(removing)
        if removing:
            remove(removing)

        # Handle additions (excluding renamed frames)
        def add(indizes):
            self.beginInsertRows(QModelIndex(), indizes[0], indizes[-1])
            for index in indizes:
                old_frames.insert(index, new_frames[index])
            self.endInsertRows()
            del indizes[:]

        adding = []
        for i, item in enumerate(new_frames):
            name = item[0]
            if name in added and name not in renamed:
                adding.append(i)
            elif adding:
                add(adding)
        if adding:
            add(adding)

    def _get_frames(self):
        if not self._frames:
            return []
        frames = self._frames.frames
        return list(sorted(frames.items(), key=lambda item: item[0]))

    def data(self, index, role):
        if not index.isValid():
            return None

        if role < self.Roles.FirstDataRole:
            field = self.Roles.FirstDataRole + index.column() + 1
        else:
            field = role

        if role == Qt.DisplayRole:
            return str(self.data(index, field))
        elif role == self.Roles.NumberRole:
            if self.Roles.XRole <= field <= self.Roles.CRole:
                return self.data(index, field)
            else:
                return -1
        elif role == self.Roles.AxisRole:
            if self.Roles.XRole <= field <= self.Roles.CRole:
                return field - self.Roles.XRole
            else:
                return -1
        elif role >= self.Roles.FirstDataRole:
            return self._get_data(index, role)
        elif role == Qt.InitialSortOrderRole:
            return Qt.AscendingOrder
        elif role == self.Roles.SortRole:
            return self.data(index, field)
        elif role == self.Roles.TypeRole:
            if self.Roles.XRole <= field <= self.Roles.ZRole:
                return 'linear_number'
            elif self.Roles.ARole <= field <= self.Roles.CRole:
                return 'angular_number'
            else:
                return self._role_names.get(field, None)
        else:
            return None

    def _get_data(self, index, role):
        frame_item = index.internalPointer()
        switch = {
            self.Roles.NameRole: lambda: frame_item[0],
            self.Roles.PoseRole: lambda: frame_item[1]['pose'],
            self.Roles.XRole: lambda: frame_item[1]['pose'][0],
            self.Roles.YRole: lambda: frame_item[1]['pose'][1],
            self.Roles.ZRole: lambda: frame_item[1]['pose'][2],
            self.Roles.ARole: lambda: frame_item[1]['pose'][3],
            self.Roles.BRole: lambda: frame_item[1]['pose'][4],
            self.Roles.CRole: lambda: frame_item[1]['pose'][5],
            self.Roles.DescriptionRole: lambda: frame_item[1]['data'].get(
                'description', ''
            ),
            self.Roles.ModelTypeRole: lambda: frame_item[1]['data'].get(
                'model_type', ''
            ),
        }
        return switch.get(role, lambda: None)()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._frame_list)

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._frame_list[row]
        except (IndexError, AttributeError):
            return QModelIndex()
        else:
            return self.createIndex(row, column, item)
