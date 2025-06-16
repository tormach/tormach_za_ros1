import os
from collections import namedtuple
from functools import partial

from robot_ui.pathpilot.file import FileCollisionChecker

MockItem = namedtuple('MockItem', 'name type children')
FileItem = partial(MockItem, type='f', children=None)
DirItem = partial(MockItem, type='d')


class SelectionMock:
    def __init__(self, files=None, file_tree=None, path=""):
        if files is None:
            files = []
        if file_tree is None:
            file_tree = []
        self._file_tree = file_tree
        self._files = files
        self._path = path

        self._dirs = {}

        def extract_dirs(path_, items):
            self._dirs[path_] = items
            for item in items:
                if item.type == 'f':
                    continue
                new_path = os.path.join(path_, item.name)
                extract_dirs(new_path, item.children)

        extract_dirs(path, file_tree)

    @property
    def files(self):
        return self._files

    @property
    def path(self):
        return self._path

    def listdir(self, fullpath):
        return [f.name for f in self._dirs.get(fullpath, [])]

    def isdir(self, fullpath):
        return fullpath in self._dirs


def test_files_and_folders_with_collision_are_found():
    checker = FileCollisionChecker()
    checker.sourceSelection = SelectionMock(
        files=["collect", "explore", "hasten", "tribe"],
        file_tree=[
            FileItem(name="collect"),
            FileItem(name="shave"),
            DirItem(
                name="explore",
                children=[FileItem(name="freeze"), FileItem("govern")],
            ),
            FileItem(name="tribe"),
            DirItem(name="extend", children=[]),
            FileItem(name="hasten"),
        ],
        path="/spoon",
    )
    checker.targetSelection = SelectionMock(
        file_tree=[
            FileItem(name="declare"),
            FileItem(name="tribe"),
            FileItem(name="color"),
            DirItem(name="hasten", children=[]),
            FileItem(name="lot"),
            FileItem(name="explode"),
            DirItem(name="explore", children=[FileItem(name="govern")]),
        ],
        path="/fellow/lung",
    )

    checker.update()

    assert checker.hasCollisions is True
    assert checker.collisions == [
        "/fellow/lung/explore/govern",
        "/fellow/lung/hasten",
        "/fellow/lung/tribe",
    ]


def test_files_and_folders_without_collision_are_not_found():
    checker = FileCollisionChecker()
    checker.sourceSelection = SelectionMock(
        files=["this", "royalty", "strong", "captain", "spin"],
        file_tree=[
            FileItem(name="this"),
            FileItem(name="royalty"),
            FileItem(name="baby"),
            FileItem(name="strong"),
            DirItem(name="captain", children=[]),
            FileItem(name="spin"),
        ],
        path="/spoon",
    )
    checker.targetSelection = SelectionMock(
        file_tree=[
            FileItem(name="shoulder"),
            FileItem(name="compete"),
            FileItem(name="habit"),
            DirItem(name="captain", children=[]),
            FileItem(name="baby"),
            FileItem(name="between"),
        ],
        path="/fellow/lung",
    )

    checker.update()

    assert checker.hasCollisions is False
    assert checker.collisions == []
