from PySide6.QtCore import (
    QObject,
    QThread,
    Signal,
    Property,
    Slot,
)

from ..qt_helpers import ensure_cleanup


class WorkerThread(QThread):
    workerDone = Signal()

    def __init__(self, worker_description, target=None, args=(), kwargs=None):
        super().__init__()
        self.worker_description = worker_description
        self.target = target
        self.args = args
        self.kwargs = {} if kwargs is None else kwargs
        self.result = None
        self.request_exception = None

        self.finished.connect(self.deleteLater)

    def run(self):
        try:
            self.result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            self.request_exception = e

        self.workerDone.emit()


class WorkerManager(QObject):
    activeWorkerCountChanged = Signal()

    def __init__(self, parent=None):
        """
        Create a worker manager to parallelize the downloading of files in PP Hub
        """
        super().__init__(parent)
        self._workers = set()

        ensure_cleanup(self._stop_workers)

    @Property(int, notify=activeWorkerCountChanged)
    def activeWorkerCount(self):
        return len(self._workers)

    def execute_task(
        self,
        target,
        target_args=(),
        target_kwargs=None,
        worker_description=None,
        ui_callback=None,
    ):
        """
        Execute a task in a new worker thread. The thread will be added to the self.workers set and removed when it
        finishes.

        :param target: The target function to run in a worker
        :param target_args: *args for the target function
        :param target_kwargs: **kwargs for the target function
        :param worker_description: Human readable description of the worker's task
        :param ui_callback: Callback to be executed with glib.idle_add when the task is complete
        """

        worker = WorkerThread(
            worker_description=worker_description,
            target=target,
            args=target_args,
            kwargs=target_kwargs,
        )
        self._workers.add(worker)

        def callback():
            ui_callback(worker.request_exception, worker.result)
            self._workers.remove(worker)
            self.activeWorkerCountChanged.emit()

        worker.workerDone.connect(callback)
        worker.start()

        self.activeWorkerCountChanged.emit()

    def active_workers(self):
        """
        Get a list of all worker threads that have not completed.

        """
        return [worker for worker in self._workers if worker.isRunning()]

    def all_workers(self):
        return self._workers

    @Slot()
    def _stop_workers(self):
        for worker in self._workers:
            if worker.isRunning():
                worker.quit()
