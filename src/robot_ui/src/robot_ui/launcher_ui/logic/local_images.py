import logging
from enum import IntEnum, auto
from . import (
    qt_launcher_image_version_helper,
    qt_launcher_release_channel_helper,
)

from PySide6.QtCore import (
    QAbstractItemModel,
    QByteArray,
    Qt,
    QModelIndex,
    QEnum,
    Signal,
    Slot,
    Property,
)
from PySide6.QtQml import QmlElement
from pp_ros_launch.launcher.updates import Updater

import qasync

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0

module_name = "LocalImages"


@QmlElement
class LocalImages(QAbstractItemModel):
    class Roles(IntEnum):
        VersionRole = Qt.UserRole
        CodenameRole = auto()
        ChannelRole = auto()
        DescriptionRole = auto()
        CreationDateRole = auto()
        ChangelogRole = auto()
        TagRole = auto()
        NameRole = auto()
        SelectedRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.VersionRole: QByteArray(b"version"),
        Roles.CodenameRole: QByteArray(b"codename"),
        Roles.ChannelRole: QByteArray(b"channel"),
        Roles.DescriptionRole: QByteArray(b"description"),
        Roles.CreationDateRole: QByteArray(b"creationDate"),
        Roles.ChangelogRole: QByteArray(b"changelog"),
        Roles.TagRole: QByteArray(b"tag"),
        Roles.NameRole: QByteArray(b"name"),
        Roles.SelectedRole: QByteArray(b"selected"),
    }

    loadingStarted = Signal()
    loadingCompleted = Signal()
    defaultIndexChanged = Signal(int)
    changelogDataChanged = Signal(str)
    stagedImageNameChanged = Signal(str)
    pathPilotChannelChanged = Signal(str)
    channelFilterChanged = Signal(str)
    channelsUpdated = Signal()
    pathPilotChannelsChanged = Signal()
    deletingStarted = Signal()
    deletingCompleted = Signal()
    deletionPossibleChanged = Signal(bool)
    startPossibleChanged = Signal(bool)

    logger = logging.getLogger(f"{__name__} ({module_name})")

    def __init__(self, parent=None):
        super().__init__(parent)

        self._launcher_images = list()
        self._selected_images = list()
        self._channel_filter = None
        self._default_index = 0
        self._channels = None

    @qasync.asyncSlot()
    async def loadImages(self) -> None:
        self.loadingStarted.emit()
        self.logger.debug(f"{module_name} reloading Docker images")
        self.beginResetModel()
        self._launcher_images.clear()
        self._selected_images.clear()
        if self._channel_filter:
            self._launcher_images = await Updater.get_local_images(
                self._channel_filter
            )
            self.logger.debug(
                f"For channel {self._channel_filter} retrieved "
                f"local images: {[i.name for i in self._launcher_images]}"
            )
        else:
            self._launcher_images = await Updater.get_all_local_images()
            self.logger.debug(
                f"For all available channels retrieved "
                f"local images: {[i.name for i in self._launcher_images]}"
            )

        # Temporary hack to select the first image in a list to display the changelog
        # sidebar (make it more obvious to the user)
        if self._launcher_images and len(self._launcher_images) > 0:
            self._selected_images.append(self._launcher_images[0])
            self.startPossibleChanged.emit(self.startPossible)
            self.deletionPossibleChanged.emit(self.deletionPossible)
            self.changelogDataChanged.emit(self.changelogData)

        self.endResetModel()
        self.loadingCompleted.emit()

    def data(self, index, role):
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self._launcher_images):
            return None

        _image = self._launcher_images[index.row()]
        switch = {
            Qt.DisplayRole: lambda: _image.tag,
            self.Roles.VersionRole: lambda: qt_launcher_image_version_helper.get_version(
                _image, self
            ),
            self.Roles.CodenameRole: lambda: qt_launcher_image_version_helper.get_codename(
                _image, self
            ),
            self.Roles.ChannelRole: lambda: qt_launcher_release_channel_helper.get_label(
                qt_launcher_image_version_helper.get_channel_name(_image), self
            ),
            self.Roles.DescriptionRole: lambda: qt_launcher_image_version_helper.get_description(
                _image, self
            ),
            self.Roles.CreationDateRole: lambda: qt_launcher_image_version_helper.get_creation_date(
                _image, self
            ),
            self.Roles.ChangelogRole: lambda: qt_launcher_image_version_helper.get_changelog(
                _image, self
            ),
            self.Roles.TagRole: lambda: _image.tag,
            self.Roles.NameRole: lambda: _image.name,
            self.Roles.SelectedRole: lambda: _image in self._selected_images,
        }

        return switch.get(role, lambda: None)()

    def roleNames(self):
        return self._ROLE_NAMES

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return None

        return self._ROLE_NAMES.get(role, "").title()

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._launcher_images[row]
        except IndexError:
            return QModelIndex()
        else:
            return self.createIndex(row, column, item)

    def parent(self, _index):
        return QModelIndex()

    def columnCount(self, _parent):
        return len(self._ROLE_NAMES)

    def rowCount(self, parent=QModelIndex()):
        if parent == QModelIndex():
            return len(self._launcher_images)
        else:
            return 0

    @Slot()
    def setData(self, index, value, role=None):
        if role == self.Roles.SelectedRole and isinstance(value, bool):
            image = self._launcher_images[index.row()]
            if value:
                if image not in self._selected_images:
                    self._selected_images.append(image)
            else:
                if image in self._selected_images:
                    self._selected_images.remove(image)

            self.dataChanged.emit(index, index, [])

            self.startPossibleChanged.emit(self.startPossible)
            self.deletionPossibleChanged.emit(self.deletionPossible)
            self.changelogDataChanged.emit(self.changelogData)
            return True
        else:
            self.logger.error(
                f"setData function called with unsupported role: {role} and/or value: {value} of type: {type(value)}"
            )
        return False

    """
    Poor-man's implementation of functionality of the DelegateModel QML object used
    to support usual multi-select tricks
    """

    @Slot()
    def deselectAll(self) -> None:
        self.beginResetModel()
        self._selected_images.clear()
        self.endResetModel()
        self.startPossibleChanged.emit(self.startPossible)
        self.deletionPossibleChanged.emit(self.deletionPossible)
        self.changelogDataChanged.emit(self.changelogData)

    @Slot(int)
    def selectSingle(self, index) -> None:
        self.beginResetModel()
        image = self._launcher_images[index]
        self._selected_images.clear()
        self._selected_images.append(image)
        self.endResetModel()
        self.startPossibleChanged.emit(self.startPossible)
        self.deletionPossibleChanged.emit(self.deletionPossible)
        self.changelogDataChanged.emit(self.changelogData)

    @Slot(int, bool)
    def selectToggleSingle(self, index, select) -> None:
        self.beginResetModel()
        image = self._launcher_images[index]
        if select and image not in self._selected_images:
            self._selected_images.append(image)
        elif not select and image in self._selected_images:
            self._selected_images.remove(image)
        self.endResetModel()
        self.startPossibleChanged.emit(self.startPossible)
        self.deletionPossibleChanged.emit(self.deletionPossible)
        self.changelogDataChanged.emit(self.changelogData)

    @Slot(int)
    def selectMulti(self, index) -> None:
        self.beginResetModel()
        image = self._launcher_images[index]
        if not self._selected_images:
            self._selected_images.append(image)
        else:
            last_selected_image = self._selected_images[-1]
            last_selected_image_index = self._launcher_images.index(
                last_selected_image
            )
            start_index = (
                last_selected_image_index
                if last_selected_image_index <= index
                else index
            )
            end_index = (
                last_selected_image_index
                if last_selected_image_index >= index
                else index
            )

            while start_index != end_index:
                modified = self._launcher_images[start_index]
                if modified not in self._selected_images:
                    self._selected_images.append(modified)
                start_index = start_index + 1

        self.endResetModel()
        self.startPossibleChanged.emit(self.startPossible)
        self.deletionPossibleChanged.emit(self.deletionPossible)
        self.changelogDataChanged.emit(self.changelogData)

    @qasync.asyncSlot()
    async def deleteImages(self) -> None:
        if not self._selected_images:
            self.logger.error(
                "No selected images ready for deletion! Process aborted."
            )
            return

        self.deletingStarted.emit()
        self.logger.info(
            "Deleting selected images:\n"
            f"{[image.name for image in self._selected_images]}"
        )

        await Updater.delete_local_images(self._selected_images)
        await self.loadImages()
        self.deletingCompleted.emit()

    @Property(str, notify=channelFilterChanged)
    def channelFilter(self) -> str:
        return self._channel_filter if self._channel_filter else ""

    @channelFilter.setter
    def channelFilter(self, value):
        if value == "":
            value = None
        self._channel_filter = value

    @Property(bool, notify=deletionPossibleChanged)
    def deletionPossible(self) -> bool:
        return len(self._selected_images) > 0

    @Property(bool, notify=startPossibleChanged)
    def startPossible(self) -> bool:
        return len(self._selected_images) == 1

    @Property(str, notify=changelogDataChanged)
    def changelogData(self) -> str:
        if self.startPossible:
            return qt_launcher_image_version_helper.get_changelog(
                self._selected_images[0], self
            )
        return ""

    @Property(str, notify=stagedImageNameChanged)
    def stagedImageName(self) -> str:
        if self.startPossible:
            return self._selected_images[0].name
        return ""
