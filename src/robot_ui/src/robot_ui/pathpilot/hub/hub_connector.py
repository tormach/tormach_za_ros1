import os
import tempfile
from enum import IntEnum, auto

import rospy
from PySide6.QtCore import (
    QUrl,
    QTimer,
    Signal,
    Property,
    Slot,
    QEnum,
    QMimeDatabase,
    QByteArray,
)
from PySide6.QtQml import QPyQmlParserStatus, QmlElement
from redis import Redis
from pathpilot_lib.pp_hub.connector import (
    Connector,
    APIError,
    TokenError,
    CloudItem,
    TransferItem,
)
from ..core.worker import WorkerManager
from ..file.file_utils import get_files_from_qml_data

QML_IMPORT_NAME = 'pathpilot.hub'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class HubConnectorStatus(IntEnum):
    IdleStatus = auto()
    ErrorStatus = auto()
    LoginStatus = auto()
    LogoutStatus = auto()
    ReloadFilesStatus = auto()
    CreateFolderStatus = auto()
    DeleteAllStatus = auto()
    RenameStatus = auto()
    DownloadFilePreviewStatus = auto()
    DownloadStatus = auto()
    UploadStatus = auto()
    UploadMachineLogdataStatus = auto()


@QmlElement
class HubConnector(QPyQmlParserStatus):
    _CHECK_RESULT_INTERVAL_MS = 100
    DOWNLOAD_SIZE_LIMIT = 1024 * 1024 * 2  # 2MiB

    QEnum(HubConnectorStatus)

    ppHubUrlChanged = Signal(QUrl)
    emailChanged = Signal(str)
    tokenChanged = Signal(str)
    passwordChanged = Signal(str)
    loggedInChanged = Signal(bool)
    errorStringChanged = Signal(str)
    statusChanged = Signal(int)
    taskRunningChanged = Signal()
    usedBytesChanged = Signal(float)
    availableBytesChanged = Signal(float)
    filesUpdated = Signal()
    pathChanged = Signal(str)
    filesChanged = Signal()
    fileCountChanged = Signal(int)
    folderCountChanged = Signal(int)
    filePreviewContentChanged = Signal()
    filePreviewableChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._redis = None
        self._skip_redis = False
        self._connector = None
        self._pp_hub_url = QUrl()
        self._email = ''
        self._token = ''
        self._password = ''
        self._logged_in = False
        self._error_string = ''
        self._status = HubConnectorStatus.IdleStatus
        self._asyncresult = None
        self._dirs = {}
        self._used_bytes = 0.0
        self._available_bytes = 0.0
        self._path = ""
        self._files = []
        self._file_count = 0
        self._folder_count = 0
        self._mime_db = QMimeDatabase()
        self._file_preview_content = ""
        self._file_previewable = False

        self._check_result_timer = QTimer()
        self._check_result_timer.setInterval(self._CHECK_RESULT_INTERVAL_MS)
        self._check_result_timer.timeout.connect(self._check_result)

        self._worker_manager = WorkerManager()
        self._worker_manager.activeWorkerCountChanged.connect(
            self.taskRunningChanged
        )

        self.pathChanged.connect(self._update_file_metrics)
        self.filesChanged.connect(self._update_file_metrics)

    def classBegin(self):
        pass

    def componentComplete(self):
        self._create_connection()
        self._update_logged_in_status()

    @Property(bool, notify=loggedInChanged)
    def loggedIn(self):
        return self._logged_in

    @Property(QUrl, notify=ppHubUrlChanged)
    def ppHubUrl(self):
        return self._pp_hub_url

    @ppHubUrl.setter
    def ppHubUrl(self, value):
        if value == self._pp_hub_url:
            return
        self._pp_hub_url = value
        self.ppHubUrlChanged.emit(value)

    @Property(str, notify=emailChanged)
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if value == self._email:
            return
        self._email = value
        self.emailChanged.emit(value)

    @Property(str, notify=tokenChanged)
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        if value == self._token:
            return
        self._token = value
        self.tokenChanged.emit(value)

    @Property(str, notify=passwordChanged)
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        if value == self._password:
            return
        self._password = value
        self.passwordChanged.emit(value)

    @Property(str, notify=errorStringChanged)
    def errorString(self):
        return self._error_string

    @Property(int, notify=statusChanged)
    def status(self):
        return self._status

    def _set_status(self, status):
        if status == self._status:
            return
        self._status = HubConnectorStatus(status)
        self.statusChanged.emit(status)

    @Property(bool, notify=taskRunningChanged)
    def taskRunning(self):
        return self._worker_manager.activeWorkerCount > 0

    @Property(float, notify=usedBytesChanged)
    def usedBytes(self):
        return self._used_bytes

    @Property(float, notify=availableBytesChanged)
    def availableBytes(self):
        return self._available_bytes

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == self._path:
            return
        self._path = value
        self.pathChanged.emit(value)

    @Property(list, notify=filesChanged)
    def files(self):
        return self._files

    @files.setter
    def files(self, value):
        if value == self._files:
            return
        self._files = value
        self.filesChanged.emit()

    @Property(int, notify=fileCountChanged)
    def fileCount(self):
        return self._file_count

    @Property(int, notify=folderCountChanged)
    def folderCount(self):
        return self._folder_count

    @Property(str, notify=filePreviewContentChanged)
    def filePreviewContent(self):
        return self._file_preview_content

    @Property(bool, notify=filePreviewableChanged)
    def filePreviewable(self):
        return self._file_previewable

    def listdir(self, fullpath):
        return [f['name'] for f in self._dirs.get(fullpath, [])]

    def isdir(self, fullpath):
        return fullpath in self._dirs

    @Slot()
    def login(self):
        self._set_status(HubConnectorStatus.LoginStatus)
        self._asyncresult = self._connector.login(self._email, self._password)
        self._check_result_timer.start()

    @Slot()
    def logout(self):
        if not self._check_logged_in_and_idle("log out"):
            return
        self._set_status(HubConnectorStatus.LogoutStatus)
        self._asyncresult = self._connector.logout()
        self._check_result_timer.start()

    @Slot()
    def reloadFiles(self):
        if not self._check_logged_in_and_idle(self.tr("reload files")):
            return

        def callback(request_exception, result):
            if request_exception:
                try:
                    self._error_string = str(request_exception)
                except TypeError:
                    self._error_string = self.tr("Unknown error")
                rospy.logwarn(
                    f"HUB: error while getting cloud files: {self._error_string}"
                )
                self._set_status(HubConnectorStatus.ErrorStatus)
                if isinstance(request_exception, TokenError):
                    self._update_logged_in_status()
                return

            if result is not None and len(result) > 0:
                self._dirs.clear()

                def extract_dirs(entries, path):
                    for entry in entries:
                        if 'fullpath' not in entry:
                            fullpath = os.path.join(path, entry['name'])
                            entry['fullpath'] = fullpath
                        else:
                            fullpath = entry['fullpath']
                        if entry['type'] == 'd':
                            self._dirs[fullpath] = entry['children']
                            extract_dirs(entry['children'], fullpath)

                extract_dirs(result['contents'], '')
                self._used_bytes = result['storage_used']
                self._available_bytes = result['storage_avail']

                self.filesUpdated.emit()
                self.usedBytesChanged.emit(self._used_bytes)
                self.availableBytesChanged.emit(self._available_bytes)
            self._set_status(HubConnectorStatus.IdleStatus)

        self._set_status(HubConnectorStatus.ReloadFilesStatus)
        self._worker_manager.execute_task(
            self._connector.get_cloud_files,
            worker_description="Refreshing cloud files.",
            ui_callback=callback,
        )

    @Slot(str)
    def createFolder(self, name):
        if not self._check_logged_in_and_idle(self.tr("create folder")):
            return

        def callback(request_exception, _result):
            if request_exception:
                try:
                    self._error_string = str(request_exception)
                except TypeError:
                    self._error_string = self.tr("Unknown error")
                rospy.logwarn(
                    f"HUB: error while creating new folder: {self._error_string}"
                )
                self._set_status(HubConnectorStatus.ErrorStatus)
                if isinstance(request_exception, TokenError):
                    self._update_logged_in_status()
                return

            self._set_status(HubConnectorStatus.IdleStatus)
            self.reloadFiles()

        self._set_status(HubConnectorStatus.CreateFolderStatus)
        self._worker_manager.execute_task(
            self._connector.new_cloud_folder,
            (self._token, self._path, name),
            worker_description="Create folder.",
            ui_callback=callback,
        )

    @Slot()
    def deleteAll(self):
        if not self._check_logged_in_and_idle(self.tr("delete all")):
            return
        if self._path not in self._dirs:
            return
        cloud_items = self._get_cloud_items_for_selected()

        def callback(request_exception, result):
            if request_exception:
                try:
                    self._error_string = str(request_exception)
                except TypeError:
                    self._error_string = self.tr("Unknown error")
                rospy.logwarn(
                    f"HUB: error while deleting: {self._error_string}"
                )
                self._set_status(HubConnectorStatus.ErrorStatus)
                if isinstance(request_exception, TokenError):
                    self._update_logged_in_status()
                return

            rospy.logdebug(f"HUB: finished deleting items with status {result}")
            self._set_status(HubConnectorStatus.IdleStatus)
            self.reloadFiles()

        self._set_status(HubConnectorStatus.DeleteAllStatus)
        self._worker_manager.execute_task(
            self._connector.delete_cloud_items,
            (cloud_items,),
            worker_description="Delete items.",
            ui_callback=callback,
        )

    @Slot(str)
    def rename(self, new_name):
        if not self._check_logged_in_and_idle(self.tr("rename")):
            return
        items = get_files_from_qml_data(self._files)
        if len(items) != 1:
            return
        old_name = os.path.join(self._path, items[0])

        def callback(request_exception, _result):
            if request_exception:
                try:
                    self._error_string = str(request_exception)
                except TypeError:
                    self._error_string = self.tr("Unknown error")
                rospy.logwarn(
                    f"HUB: error while renaming: {self._error_string}"
                )
                self._set_status(HubConnectorStatus.ErrorStatus)
                if isinstance(request_exception, TokenError):
                    self._update_logged_in_status()
                return
            self._set_status(HubConnectorStatus.IdleStatus)
            self.reloadFiles()

        self._set_status(HubConnectorStatus.RenameStatus)
        self._worker_manager.execute_task(
            self._connector.rename_cloud_item,
            (None, old_name, new_name),
            worker_description="Rename.",
            ui_callback=callback,
        )

    @Slot(str)
    def downloadFilePreview(self, name):
        file_previewable = self._check_file_previewable(name)
        if self._file_previewable != file_previewable:
            self._file_previewable = file_previewable
            self.filePreviewableChanged.emit(self._file_previewable)

        if self._file_preview_content:
            self._file_preview_content = ""
            self.filePreviewContentChanged.emit()

        if not file_previewable:
            return

        if not self._check_logged_in_and_idle(self.tr("download file preview")):
            return

        cloud_item = CloudItem(
            fullpath=os.path.join(self._path, name),
            itemtype='f',
            group_id=None,
            group_type=None,
        )

        rospy.logdebug(
            f"HUB: downloading {self.DOWNLOAD_SIZE_LIMIT:d} bytes of "
            f"file {cloud_item.fullpath:s} for preview"
        )

        tmpfile = tempfile.NamedTemporaryFile(
            mode='w', prefix='hub_', delete=False
        )
        tmpfile.close()
        item = TransferItem(
            diskpath=tmpfile.name,
            cloud_item=cloud_item,
            maxbytes=self.DOWNLOAD_SIZE_LIMIT,
        )
        txitem_list = [
            item,
        ]

        def callback(request_exception, result):
            if request_exception:
                try:
                    self._error_string = str(request_exception)
                except TypeError:
                    self._error_string = self.tr("Unknown error")
                rospy.logdebug(
                    f"HUB: error while trying to download preview: {self._error_string}"
                )
                self._set_status(HubConnectorStatus.ErrorStatus)
                if isinstance(request_exception, TokenError):
                    self._update_logged_in_status()
                return

            rospy.logdebug(
                f"HUB: finished preview download with status {result}"
            )
            with open(tmpfile.name) as f:
                self._file_preview_content = f.read()
                self.filePreviewContentChanged.emit()
            self._set_status(HubConnectorStatus.IdleStatus)

            # Clean up the tmp preview file now that we are done
            os.remove(tmpfile.name)

        self._set_status(HubConnectorStatus.DownloadFilePreviewStatus)
        self._worker_manager.execute_task(
            self._connector.download_cloud_items,
            target_args=(txitem_list,),
            worker_description="Download items",
            ui_callback=callback,
        )

    def _check_file_previewable(self, name):
        if not name:
            return False

        if self._path not in self._dirs:
            rospy.logwarn("Cannot download file preview for non-existent path.")
            return False

        tree_item = None
        for item in self._dirs[self._path]:
            if item['name'] == name:
                tree_item = item
                break
        if not tree_item:
            rospy.logwarn("Cannot download file preview for non-existent file.")
            return False

        if tree_item['type'] != 'f':
            return False

        if tree_item['size'] > self.DOWNLOAD_SIZE_LIMIT:
            return False

        type_ = self._mime_db.mimeTypeForFileNameAndData(name, QByteArray(b" "))
        return bool(type_.name().startswith('text'))

    @Slot(str)
    def download(self, target_path):
        if not self._check_logged_in_and_idle(self.tr("download")):
            return
        if self._path not in self._dirs:
            return

        txitem_list = []
        cloud_items = self._get_cloud_items_for_selected()
        for item in cloud_items:
            fpath = item.fullpath
            # trim left gcode/ from cloud path when forming local disk path if needed
            if fpath.startswith(self._path):
                fpath = fpath[len(self._path) :]
            if fpath.startswith('/'):
                fpath = fpath[1:]
            target_fullpath = os.path.join(target_path, fpath)
            if item.itemtype == 'd':
                # trim trailing path separator if needed
                if target_fullpath.endswith(os.path.sep):
                    target_fullpath = target_fullpath[:-1]
                cloud_items += self._get_cloud_items_for_path(item.fullpath)
            txitem_list.append(
                TransferItem(
                    diskpath=target_fullpath,
                    cloud_item=item,
                    maxbytes=None,
                )
            )

        if not txitem_list:
            return
        rospy.logdebug(f"HUB: downloading {len(txitem_list)} files")

        def callback(request_exception, result):
            if request_exception:
                try:
                    self._error_string = str(request_exception)
                except TypeError:
                    self._error_string = self.tr("Unknown error")
                rospy.logwarn(
                    f"HUB: error while downloading: {self._error_string}"
                )
                self._set_status(HubConnectorStatus.ErrorStatus)
                if isinstance(request_exception, TokenError):
                    self._update_logged_in_status()
                return

            rospy.logdebug(f"HUB: finished downloading with status {result}")
            self._set_status(HubConnectorStatus.IdleStatus)

        self._set_status(HubConnectorStatus.DownloadStatus)
        self._worker_manager.execute_task(
            self._connector.download_cloud_items,
            target_args=(txitem_list,),
            worker_description="Download items",
            ui_callback=callback,
        )

    @Slot('QVariant')
    def upload(self, source_selection):
        if not self._check_logged_in_and_idle(self.tr("upload")):
            return
        if self._path not in self._dirs:
            return

        txitem_list = []

        def create_tx_for_dir(source_path, target_path, source_files=None):
            source_files = (
                source_selection.listdir(source_path)
                if source_files is None
                else source_files
            )
            for name in source_files:
                sub_source_path = os.path.join(source_path, name)
                sub_target_path = os.path.join(target_path, name)
                itemtype = (
                    'd' if source_selection.isdir(sub_source_path) else 'f'
                )
                cloud_item = CloudItem(
                    fullpath=sub_target_path,
                    itemtype=itemtype,
                    group_id=None,
                    group_type=None,
                )
                txitem_list.append(
                    TransferItem(
                        diskpath=sub_source_path,
                        cloud_item=cloud_item,
                        maxbytes=None,
                    )
                )
                if itemtype == 'd':
                    create_tx_for_dir(sub_source_path, sub_target_path)

        files = get_files_from_qml_data(source_selection.files)
        create_tx_for_dir(source_selection.path, self._path, files)

        if not txitem_list:
            return
        rospy.logdebug(f"HUB: uploading {len(txitem_list)} files to account.")

        def callback(request_exception, result):
            if request_exception:
                try:
                    self._error_string = str(request_exception)
                except TypeError:
                    self._error_string = self.tr("Unknown error")
                rospy.logwarn(
                    f"HUB: error while uploading {self._error_string}"
                )
                self._set_status(HubConnectorStatus.ErrorStatus)
                if isinstance(request_exception, TokenError):
                    self._update_logged_in_status()
                return

            rospy.logdebug(
                f"HUB: finished uploading to {self._path} with status {result}"
            )
            self._set_status(HubConnectorStatus.IdleStatus)
            self.reloadFiles()

        self._set_status(HubConnectorStatus.UploadStatus)
        self._worker_manager.execute_task(
            self._connector.upload_cloud_items,
            target_args=(txitem_list, False),
            worker_description=f"Uploading files to: {self._path}",
            ui_callback=callback,
        )

    @Slot(str, str)
    def uploadMachineLogdata(self, machine_guid, path):
        if not self._check_logged_in_and_idle(
            self.tr("upload machine logdata")
        ):
            return

        def callback(request_exception, result):
            if request_exception:
                self._error_string = str(request_exception)
                rospy.logwarn(
                    f"HUB: error while upload log file {request_exception}"
                )
                self._set_status(HubConnectorStatus.ErrorStatus)
                if isinstance(request_exception, TokenError):
                    self._update_logged_in_status()
                return

            rospy.logdebug(
                f"HUB: finished uploading machine logdata {path} "
                f"for machine {machine_guid} with status {result}"
            )
            self._set_status(HubConnectorStatus.IdleStatus)
            self.reloadFiles()

        self._set_status(HubConnectorStatus.UploadMachineLogdataStatus)
        self._worker_manager.execute_task(
            self._connector.upload_machine_logdata,
            target_args=(machine_guid, path),
            worker_description=f"Uploading machine log data: {path}",
            ui_callback=callback,
        )

    def get_files_for_path(self, path):
        return self._dirs.get(path, [])

    def _get_cloud_items_for_selected(self):
        tree_items = {d['name']: d for d in self._dirs[self._path]}
        cloud_items = []
        items = get_files_from_qml_data(self._files)
        for item in items:
            tree_item = tree_items[item]
            cloud_items.append(
                CloudItem(
                    fullpath=tree_item['fullpath'],
                    itemtype=tree_item['type'],
                    group_type=None,
                    group_id=None,
                )
            )
        return cloud_items

    def _get_cloud_items_for_path(self, path):
        items = self._dirs[path]
        return [
            CloudItem(
                fullpath=item['fullpath'],
                itemtype=item['type'],
                group_type=None,
                group_id=None,
            )
            for item in items
        ]

    def _check_logged_in_and_idle(self, operation):
        if not self._logged_in:
            rospy.logerr(f"Can't {operation} when not logged in.")
            return False
        if self._status not in (
            HubConnectorStatus.IdleStatus,
            HubConnectorStatus.ErrorStatus,
        ):
            rospy.logerr(f"Can't {operation} files when not idle.")
            return False
        return True

    def _update_logged_in_status(self):
        token = self._connector.get_token_for_logged_in_user()
        self.token = token.decode() if token else ''
        email = self._connector.get_logged_in_email()
        self.email = email.decode() if email else ''
        self._logged_in = self._token != ''
        self.loggedInChanged.emit(self._logged_in)
        if not self._logged_in and self._dirs:
            self._dirs.clear()
            self.filesUpdated.emit()

    def _create_connection(self):
        if not self._skip_redis:
            redis_host = rospy.get_param('redis_host', 'localhost')
            redis_port = rospy.get_param('redis_port', 6379)
            redis_db = rospy.get_param('~redis_db', 1)
            self._redis = Redis(host=redis_host, port=redis_port, db=redis_db)
        self._connector = Connector(
            self._pp_hub_url.toString(),
            self._redis,
            email=self._email,
            token=self._token,
        )

    @Slot()
    def _check_result(self):
        if not self._asyncresult or not self._asyncresult.ready():
            return
        switch = {
            HubConnectorStatus.LoginStatus: lambda: self._process_login_result(),
            HubConnectorStatus.LogoutStatus: lambda: self._process_logout_result(),
        }
        switch.get(
            self._status, lambda: rospy.logerr("Check result in unknown state")
        )()
        self._check_result_timer.stop()

    def _process_login_result(self):
        try:
            self._asyncresult.get()
        except APIError as e:
            self._error_string = self.tr(
                "{0}\nForgot password? Reset it by visiting:\n{1}"
            ).format(e.message, self._pp_hub_url.toString())
            self.errorStringChanged.emit(self._error_string)
            self._set_status(HubConnectorStatus.ErrorStatus)
        else:
            self._set_status(HubConnectorStatus.IdleStatus)
            self._update_logged_in_status()

    def _process_logout_result(self):
        try:
            self._asyncresult.get()
        except APIError as e:
            rospy.logwarn(
                self.tr("HUB: APIError while logging out: {0}").format(
                    e.message
                )
            )
            return
        finally:
            self._set_status(HubConnectorStatus.IdleStatus)

        self._update_logged_in_status()

    @Slot()
    def _update_file_metrics(self):
        items = get_files_from_qml_data(self._files)
        files = 0
        folders = 0

        for item in items:
            path = os.path.join(self._path, item)
            if path in self._dirs:
                item_files, item_folders = self._count_files_and_folders(
                    self._dirs[path]
                )
                files += item_files
                folders += item_folders
            else:
                files += 1

        self._folder_count = folders
        self._file_count = files
        self.folderCountChanged.emit(folders)
        self.fileCountChanged.emit(files)

    @staticmethod
    def _count_files_and_folders(items):
        folders = 1
        files = 0

        for item_ in items:
            if item_['type'] == 'd':
                (
                    item_files,
                    item_folders,
                ) = HubConnector._count_files_and_folders(item_['children'])
                files += item_files
                folders += item_folders
            else:
                files += 1

        return files, folders


class MockRedis:
    def __init__(self):
        self._d = {}

    def hexists(self, h, k):
        if h == "pp_hub_settings":
            return k in self._d
        return False

    def hset(self, h, k, v):
        if h == "pp_hub_settings":
            if isinstance(v, str):
                self._d[k] = v.encode()
            elif isinstance(v, bytes):
                self.d_[k] = v

    def hget(self, h, k):
        if h == "pp_hub_settings":
            return self._d.get(k)
        return None

    def hgetall(self, h):
        if h == "pp_hub_settings":
            return self._d
        return {}


@QmlElement
class HubConnectorWithoutRedis(HubConnector):
    """Create a HubConnector that does not use Redis"""

    def __init__(self):
        super().__init__()
        self._skip_redis = True
        self._redis = MockRedis()
