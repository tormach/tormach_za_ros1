import os
import shutil
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_LZMA

import rospy
from PySide6.QtCore import (
    QObject,
    QDateTime,
    Signal,
    Property,
    Slot,
)
from PySide6.QtQml import QmlElement

from ..core.worker import WorkerManager


QML_IMPORT_NAME = 'pathpilot.logging'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class LogReporter(QObject):
    DEFAULT_ROS_LOG_PATH = os.path.expanduser('~/.ros/log')
    DEFAULT_HAL_LOG_PATH = '/var/log/hal.log'
    TMP_PATH = os.path.expanduser('~/tmp')

    outputPathChanged = Signal(str)
    rosLogPathChanged = Signal(str)
    halLogPathChanged = Signal(str)
    logReportCompleted = Signal(str, arguments=['path'])
    taskRunningChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._output_path = ""
        self._ros_log_path = self.DEFAULT_ROS_LOG_PATH
        self._hal_log_path = self.DEFAULT_HAL_LOG_PATH
        self._hub_connector = None
        self._machine_guid = ""

        self._worker_manager = WorkerManager()
        self._worker_manager.activeWorkerCountChanged.connect(
            self.taskRunningChanged
        )

    @Property(str, notify=outputPathChanged)
    def outputPath(self):
        return self._output_path

    @outputPath.setter
    def outputPath(self, value):
        if value == self._output_path:
            return
        self._output_path = value
        self.outputPathChanged.emit(value)

    @Property(str, notify=rosLogPathChanged)
    def rosLogPath(self):
        return self._ros_log_path

    @rosLogPath.setter
    def rosLogPath(self, value):
        if value == self._ros_log_path:
            return
        self._ros_log_path = value
        self.rosLogPathChanged.emit(value)

    @Property(str, notify=halLogPathChanged)
    def halLogPath(self):
        return self._hal_log_path

    @halLogPath.setter
    def halLogPath(self, value):
        if value == self._hal_log_path:
            return
        self._hal_log_path = value
        self.halLogPathChanged.emit(value)

    @Property(bool, notify=taskRunningChanged)
    def taskRunning(self):
        return self._worker_manager.activeWorkerCount > 0

    @staticmethod
    def _dump_ros_params(path):
        try:
            subprocess.check_call(['rosparam', 'dump', path])
        except subprocess.CalledProcessError:
            rospy.logerr(f"Could not dump ROS parameters to {path}")

    @staticmethod
    def _create_log_report(
        zip_path,
        hal_log_path,
        ros_log_path,
        output_path,
        param_dump_path,
    ):
        with ZipFile(zip_path, 'w', compression=ZIP_LZMA) as zip_file:
            # add HAL log
            if os.path.exists(hal_log_path):
                zip_file.write(hal_log_path, os.path.basename(hal_log_path))
            # add ROS log
            if os.path.exists(ros_log_path):
                for root, dirs, files in os.walk(ros_log_path):
                    for f in files:
                        file_path = os.path.join(root, f)
                        file_name = os.path.join(
                            'ros_log', file_path[len(ros_log_path) + 1 :]
                        )
                        zip_file.write(file_path, file_name)
            # add ROS param dump
            LogReporter._dump_ros_params(param_dump_path)
            zip_file.write(param_dump_path, os.path.basename(param_dump_path))

        outfile_name = f'logdata_{QDateTime.currentDateTime().toString("yyyy-MM-dd_hh-mm-ss")}.zip'
        outfile_path = os.path.join(output_path, outfile_name)
        shutil.copy2(zip_path, outfile_path)

        return outfile_path

    @Slot()
    def createLogReport(self):
        hal_log_path = os.path.expanduser(self._hal_log_path)
        ros_log_path = os.path.expanduser(self._ros_log_path)
        output_path = os.path.expanduser(self._output_path)
        if not os.path.isdir(output_path):
            rospy.logerr(
                f"Output path \"{output_path }\" does not exist, "
                f"cannot create log report."
            )
            return
        if not os.path.isdir(self.TMP_PATH):
            os.mkdir(self.TMP_PATH)
        logdata_tmpdir = tempfile.mkdtemp(prefix='logdata_', dir=self.TMP_PATH)
        zip_path = os.path.join(logdata_tmpdir, 'logreport.zip')

        param_dump_path = os.path.join(logdata_tmpdir, 'params.yaml')

        def callback(request_exception, result):
            if request_exception:
                rospy.logerr(f"Error creating log report {request_exception}")
            else:
                rospy.logdebug(f"Finished creating log report {result}")
                self.logReportCompleted.emit(result)

            shutil.rmtree(logdata_tmpdir)

        self._worker_manager.execute_task(
            self._create_log_report,
            target_args=(
                zip_path,
                hal_log_path,
                ros_log_path,
                output_path,
                param_dump_path,
            ),
            worker_description=f"Creating log report: {zip_path}",
            ui_callback=callback,
        )
