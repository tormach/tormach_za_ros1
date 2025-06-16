from PySide6.QtCore import (  # noqa: F401
    QAbstractItemModel,
    QModelIndex,
)


class ModelIndexWalker:
    root = None  # type: QModelIndex
    model = None  # type: QAbstractItemModel

    def __init__(self, model, root):
        self.model = model
        self.root = root

    def _walk(self, index):
        rows = self.model.rowCount(index)
        for child in (self.model.index(i, 0, index) for i in range(rows)):
            yield from self._walk(child)
        if index.isValid():
            yield index

    def __iter__(self):
        return self._walk(self.root)
