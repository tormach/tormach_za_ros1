import os
import yaml
from enum import IntEnum, auto

from PySide6.QtCore import (
    QObject,
    Property,
    QUrl,
    Signal,
    Slot,
    QEnum,
)
from PySide6.QtQml import QmlElement, QmlUncreatable

CONFIG_FILE_NAME = 'template.yaml'
PROGRAM_FILE_NAME = 'program_name.py'


class TemplateType(IntEnum):
    UnknownTemplate = auto()
    SimpleTemplate = auto()

    @staticmethod
    def by_name(name):
        switch = {'simple': TemplateType.SimpleTemplate}
        return switch.get(name, TemplateType.UnknownTemplate)


QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlUncreatable("ProgramTemplateItem is not creatable in QML")
class ProgramTemplateItem(QObject):
    QEnum(TemplateType)
    nameChanged = Signal(str)
    titleChanged = Signal(str)
    descriptionChanged = Signal(str)
    typeChanged = Signal(int)
    pathChanged = Signal(str)

    def __init__(
        self,
        parent=None,
        name='',
        title='',
        description='',
        type_=TemplateType.UnknownTemplate,
        path='',
    ):
        super().__init__(parent)

        self._name = name
        self._title = title
        self._description = description
        self._type = type_
        self._path = path

    @Property(str, notify=nameChanged)
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value == self._name:
            return
        self._name = value
        self.nameChanged.emit(value)

    @Property(str, notify=titleChanged)
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if value == self._title:
            return
        self._title = value
        self.titleChanged.emit(value)

    @Property(str, notify=descriptionChanged)
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if value == self._description:
            return
        self._description = value
        self.descriptionChanged.emit(value)

    @Property(int, notify=typeChanged)
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value == self._type:
            return
        self._type = TemplateType(value)
        self.typeChanged.emit(value)

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == self._path:
            return
        self._path = value
        self.pathChanged.emit(value)

    @Slot(str)
    def apply(self, target_path):
        name, _ = os.path.splitext(os.path.basename(target_path))
        source_path = os.path.join(self._path, PROGRAM_FILE_NAME)

        with open(source_path) as f:
            data = f.read()
        data = data.replace(
            'program_name', name
        )  # NOTE: it might be pretty cool to use Jinja 2 here
        with open(target_path, 'w') as f:
            f.write(data)


QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramTemplates(QObject):
    searchPathsChanged = Signal('QStringList')
    templatesChanged = Signal()

    def __init__(self, parent=None, search_paths=None, templates=None):
        super().__init__(parent)
        if templates is None:
            templates = []
        if search_paths is None:
            search_paths = []

        self._templates = templates
        self._search_paths = search_paths

    @Property('QStringList', notify=searchPathsChanged)
    def searchPaths(self):
        return self._search_paths

    @searchPaths.setter
    def searchPaths(self, value):
        if value == self._search_paths:
            return
        self._search_paths = value
        self.searchPathsChanged.emit(value)

    @Property(list, notify=templatesChanged)
    def templates(self):
        return self._templates

    @Slot()
    def update(self):
        del self.templates[:]

        for path in self._search_paths:
            if QUrl(path).isLocalFile():
                path = QUrl(path).toLocalFile()

            if not os.path.isdir(path):
                continue

            for root, _dirs, files in os.walk(path):
                for name in files:
                    if name == CONFIG_FILE_NAME:
                        self._read_template_config(os.path.join(root, name))

        self.templatesChanged.emit()

    @Slot()
    def clear(self):
        del self._templates[:]
        self.templatesChanged.emit()

    def _read_template_config(self, file_path):
        with open(file_path) as f:
            data = yaml.safe_load(f)

        program_file = os.path.join(
            os.path.dirname(file_path), PROGRAM_FILE_NAME
        )
        if not os.path.isfile(program_file):
            raise OSError(f'Template must have a program file {program_file}')

        name = data.get('name', 'unnamed')
        title = data.get('title', 'Untitled')
        description = data.get('description', '')
        type_string = data.get('type', 'simple')
        enabled = data.get('enabled', 'True')

        if not enabled:
            return

        path = os.path.dirname(file_path)
        type_ = TemplateType.by_name(type_string)

        item = ProgramTemplateItem(
            name=name,
            title=title,
            description=description,
            type_=type_,
            path=path,
        )
        self._templates.append(item)
