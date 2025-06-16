import asyncio
import logging
import pp_account
from enum import IntEnum, auto

from . import qt_launcher_image_version_helper
from . import qt_launcher_release_channel_helper

from PySide6.QtCore import (
    Property,
    Signal,
    QAbstractItemModel,
    QByteArray,
    Qt,
    QModelIndex,
    QEnum,
)
from PySide6.QtQml import QmlElement
from pp_ros_launch.launcher.updates import Updater

import qasync


QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class UpdateCheckerStatus(IntEnum):
    IdleStatus = 0
    CheckStatus = 1
    UpdateStatus = 2
    ErrorStatus = 3


@QmlElement
class UpdateChecker(QAbstractItemModel):
    class Roles(IntEnum):
        VersionRole = Qt.UserRole
        ChannelRole = auto()
        CodenameRole = auto()
        DescriptionRole = auto()
        CreationDateRole = auto()
        ChangelogRole = auto()
        TagRole = auto()
        NameRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.VersionRole: QByteArray(b'version'),
        Roles.ChannelRole: QByteArray(b'channel'),
        Roles.CodenameRole: QByteArray(b'codename'),
        Roles.DescriptionRole: QByteArray(b'description'),
        Roles.CreationDateRole: QByteArray(b'creationDate'),
        Roles.ChangelogRole: QByteArray(b'changelog'),
        Roles.TagRole: QByteArray(b'tag'),
        Roles.NameRole: QByteArray(b'name'),
    }

    checkingStarted = Signal()
    checkingCompleted = Signal()
    updatesAvailableChanged = Signal(bool)
    updateCompleted = Signal(str)
    statusChanged = Signal(int)
    statusMessageChanged = Signal(str)
    pullProgressOverallChanged = Signal(int)
    pullProgressCurrentChanged = Signal(int)
    errorChanged = Signal(bool)
    errorMessageChanged = Signal(str)
    updateActionsStopped = Signal()

    QEnum(UpdateCheckerStatus)

    logger = logging.getLogger('launcher.update')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._get_updates_task = None
        self._download_update_task = None
        self._updates_available = False
        self._versions_available = list()
        self._status = UpdateCheckerStatus.IdleStatus
        self._status_message = ''
        self._error_message = None
        self._pull_progress_overall = 0
        self._pull_progress_current = 0

    @Property(int, notify=statusChanged)
    def status(self):
        return self._status

    @Property(str, notify=statusMessageChanged)
    def statusMessage(self):
        return self._status_message

    @Property(bool, notify=errorChanged)
    def error(self):
        return self._error_message is not None

    @Property(str, notify=errorMessageChanged)
    def errorMessage(self):
        return self._error_message if self._error_message else ''

    @Property(bool, notify=updatesAvailableChanged)
    def updatesAvailable(self):
        return self._updates_available

    @Property(int, notify=pullProgressOverallChanged)
    def pullProgressOverall(self):
        return self._pull_progress_overall or 0

    @Property(int, notify=pullProgressCurrentChanged)
    def pullProgressCurrent(self):
        return self._pull_progress_current or 0

    def _update_signals(self):
        if self._status == UpdateCheckerStatus.ErrorStatus:
            self.logger.error(
                self._status_message + ':  ' + self._error_message
            )
            self.errorMessageChanged.emit(self._error_message)
            self.errorChanged.emit(True)
        else:
            self.logger.info(self._status_message)

        self.statusChanged.emit(self._status)
        self.statusMessageChanged.emit(self._status_message)

    @qasync.asyncSlot()
    async def checkForUpdates(self):
        self.checkingStarted.emit()
        self.beginResetModel()
        self._status = UpdateCheckerStatus.CheckStatus

        self._status_message = self.tr(
            f"Checking for new updates in OCI registry {Updater.registry_name}."
        )
        self.logger.debug(self._status_message)

        self._versions_available.clear()
        self._error_message = None
        self._updates_available = False
        self._get_updates_task = asyncio.create_task(Updater.get_all_updates())
        try:
            self._versions_available = await self._get_updates_task

            if self._versions_available:
                self._updates_available = True
                self.logger.info(
                    f"Found available updates {[(qt_launcher_image_version_helper.get_channel_name(u), qt_launcher_image_version_helper.get_version(u,self), qt_launcher_image_version_helper.get_codename(u, self)) for u in self._versions_available]}"
                )
        except (KeyboardInterrupt, asyncio.CancelledError):
            self._status_message = self.tr("Interrupted")
        except Exception as e:
            self.logger.debug(f'Exception {e.__class__.__qualname__} body: {e}')
            self._error_message = str(e)
        finally:
            self._get_updates_task = None

        if self._error_message is not None:
            self._status = UpdateCheckerStatus.ErrorStatus
            self._status_message = self.tr("Error while checking for updates")
        elif not self._updates_available:
            self._status = UpdateCheckerStatus.IdleStatus
            self._status_message = self.tr("No update available")
        else:
            self._status = UpdateCheckerStatus.IdleStatus
            self._status_message = self.tr("Updates available")
            self._updates_available = True

        self.endResetModel()

        self.updatesAvailableChanged.emit(self._updates_available)
        self.checkingCompleted.emit()

    def _update_status(self, overall, current):
        self.pullProgressOverallChanged.emit(overall)
        self.pullProgressCurrentChanged.emit(current)
        if (overall, current) != (
            self._pull_progress_overall,
            self._pull_progress_current,
        ):
            self._pull_progress_overall = overall
            self._pull_progress_current = current
            self.logger.debug(
                "...pull progress:  overall=%d%%; current=%d%%"
                % (overall, current)
            )

    @qasync.asyncSlot(int)
    async def downloadUpdate(self, index) -> None:
        _update = self._versions_available[index]
        self._status_message = self.tr(f"Pulling update {_update.name}")
        self._error_message = None
        self.logger.info(self._status_message)
        self._status = UpdateCheckerStatus.UpdateStatus
        self.statusMessageChanged.emit(self._status_message)
        self.statusChanged.emit(self._status)
        if _update is not None:
            self._download_update_task = asyncio.create_task(
                Updater.pull(_update, self._update_status)
            )
            try:
                await self._download_update_task
            except asyncio.CancelledError:
                self._error_message = 'Update cancelled by user'
            except Exception as e:
                self._error_message = str(e)
            except (
                pp_account.PathPilotAccountError,
                pp_account.NoAccountError,
                pp_account.AccountInvalidError,
            ):
                self.logger.info('Account error occured')
            finally:
                self._download_update_task = None

        if self._error_message is not None:
            self._status = UpdateCheckerStatus.ErrorStatus
            self._status_message = self.tr("Error pulling update")
        else:
            self._status = UpdateCheckerStatus.IdleStatus
            self._status_message = self.tr("Pulled update {0} v. {1}").format(
                _update.name, _update.version
            )

        self._update_signals()
        self.updateCompleted.emit(_update.name)

    @qasync.asyncSlot()
    async def abort(self) -> None:
        if self._get_updates_task:
            self._get_updates_task.cancel()
        if self._download_update_task:
            self._download_update_task.cancel()
        self.updateActionsStopped.emit()

    def data(self, index, role):
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self._versions_available):
            return None

        _image = self._versions_available[index.row()]
        switch = {
            Qt.DisplayRole: lambda: _image.tag,
            self.Roles.VersionRole: lambda: qt_launcher_image_version_helper.get_version(
                _image, self
            ),
            self.Roles.ChannelRole: lambda: qt_launcher_release_channel_helper.get_label(
                qt_launcher_image_version_helper.get_channel_name(_image), self
            ),
            self.Roles.CodenameRole: lambda: qt_launcher_image_version_helper.get_codename(
                _image, self
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

        return self._ROLE_NAMES.get(role, '').title()

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._versions_available[row]
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
            return len(self._versions_available)
        else:
            return 0
