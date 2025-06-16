import sys
import yaml
from enum import IntEnum, auto
from pathlib import Path

from PySide6.QtCore import (
    QObject,
    QUrl,
    Property,
    Signal,
    Slot,
    QEnum,
)
from PySide6.QtQml import QmlElement, QmlUncreatable

from importlib import import_module
from importlib.machinery import SourceFileLoader
from importlib.util import spec_from_loader, module_from_spec

CONFIG_FILE_NAME = 'plugin.yaml'
FILTER_FILE_NAME = 'filter.py'

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class PluginType(IntEnum):
    UnknownPlugin = auto()
    ConversationalPlugin = auto()

    @staticmethod
    def by_name(name):
        switch = {'conversational': PluginType.ConversationalPlugin}
        return switch.get(name, PluginType.UnknownPlugin)


@QmlElement
@QmlUncreatable("ApplicationPluginItem is not creatable from QML")
class ApplicationPluginItem(QObject):
    QEnum(PluginType)
    nameChanged = Signal(str)
    titleChanged = Signal(str)
    descriptionChanged = Signal(str)
    typeChanged = Signal()
    pathChanged = Signal(str)
    mainFileChanged = Signal(QUrl)
    iconSourceChanged = Signal(QUrl)
    priorityChanged = Signal(int)
    toolTipItemIdChanged = Signal(str)
    toolTipPosRightChanged = Signal(bool)

    def __init__(
        self,
        parent=None,
        name='',
        title='',
        description='',
        type_=PluginType.UnknownPlugin,
        path='',
        priority=1000,
        tooltip_item_id='',
        tooltip_pos_right=True,
    ):
        super().__init__(parent)

        self._name = name
        self._title = title
        self._description = description
        self._type = type_
        self._path = path
        self._priority = priority
        self._tooltip_item_id = tooltip_item_id
        self._tooltip_pos_right = tooltip_pos_right

        self.nameChanged.connect(self._trigger_main_file_changed)
        self.pathChanged.connect(self._trigger_main_file_changed)
        self.toolTipItemIdChanged.connect(self._trigger_main_file_changed)
        self.toolTipPosRightChanged.connect(self._trigger_main_file_changed)
        self.nameChanged.connect(self._trigger_icon_source_changed)
        self.pathChanged.connect(self._trigger_icon_source_changed)

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
        self._type = PluginType(value)
        self.typeChanged.emit()

    @Property(str, notify=pathChanged)
    def path(self):
        return str(self._path)

    @path.setter
    def path(self, value):
        if not isinstance(value, Path):
            value = Path(value)
        if value == self._path:
            return
        self._path = value
        self.pathChanged.emit(value)

    @Property(int, notify=priorityChanged)
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, value):
        if value == self._priority:
            return
        self._priority = value
        self.priorityChanged.emit(value)

    @Property(QUrl, notify=iconSourceChanged)
    def iconSource(self):
        file_path = self._path / f'{self._name}.png'
        if file_path.exists():
            return QUrl('file://' + str(file_path))
        else:
            return QUrl()

    @Property(QUrl, notify=mainFileChanged)
    def mainFile(self):
        return QUrl('file://' + str(self._path / f'{self._name}.qml'))

    @Property(str, notify=toolTipItemIdChanged)
    def toolTipItemId(self) -> str:
        return self._tooltip_item_id

    @Property(bool, notify=toolTipPosRightChanged)
    def toolTipPosRight(self):
        return self._tooltip_pos_right

    @Slot()
    def loadPlugin(self):
        if str(self._path) not in sys.path:
            sys.path.insert(0, str(self._path))
        if self._name in sys.modules:  # load module only once
            return
        plugin = import_module(self._name)
        if hasattr(plugin, 'register_types'):
            plugin.register_types()

    @Slot()
    def _trigger_main_file_changed(self):
        self.mainFileChanged.emit(self.mainFile)

    @Slot()
    def _trigger_icon_source_changed(self):
        self.iconSourceChanged.emit(self.iconSource)


@QmlElement
class ApplicationPlugins(QObject):
    searchPathsChanged = Signal('QStringList')
    pluginsChanged = Signal()

    def __init__(self, parent=None, search_paths=None, plugins=None):
        super().__init__(parent)
        if plugins is None:
            plugins = []
        if search_paths is None:
            search_paths = []

        search_paths = [
            Path(path) if not isinstance(path, Path) else path
            for path in search_paths
        ]

        self._plugins = plugins
        self._search_paths = search_paths

    @Property('QStringList', notify=searchPathsChanged)
    def searchPaths(self):
        return [str(path) for path in self._search_paths]

    @searchPaths.setter
    def searchPaths(self, value):
        value = [
            Path(path) if not isinstance(path, Path) else path for path in value
        ]
        if value == self._search_paths:
            return
        self._search_paths = value
        self.searchPathsChanged.emit(value)

    @Property(list, notify=pluginsChanged)
    def plugins(self):
        return self._plugins

    @Slot()
    def updatePlugins(self):
        del self._plugins[:]

        for path in self._search_paths:
            if QUrl(str(path)).isLocalFile():
                path = Path(QUrl(str(path)).toLocalFile())

            if not path.is_dir():
                continue

            plugin_config_files = path.glob(f"**/{CONFIG_FILE_NAME}")
            for config in plugin_config_files:
                self._read_plugin_file(config)

        # sort by priority, lowest priority number first
        self._plugins.sort(key=lambda i: i.priority)

        self.pluginsChanged.emit()

    @Slot()
    def clearPlugins(self):
        del self._plugins[:]
        self.pluginsChanged.emit()

    def _read_plugin_file(self, config_file_path):
        with open(config_file_path) as f:
            data = yaml.safe_load(f)

        name = data.get('name', 'unnamed')
        title = data.get('title', 'Untitled')
        description = data.get('description', '')
        type_string = data.get('type', 'conversational')
        enabled = data.get('enabled', True)
        priority = data.get('priority', 0)
        tooltip_item_id = data.get('tooltip', '')
        tooltip_pos_right = data.get('toolTipPosRight', True)

        if not enabled:
            return

        filter_file = config_file_path.parent / FILTER_FILE_NAME
        if filter_file.exists():
            loader = SourceFileLoader(f"{name}.filter", str(filter_file))
            spec = spec_from_loader(loader.name, loader)
            module = module_from_spec(spec)
            loader.exec_module(module)
            if hasattr(module, "filter"):
                if module.filter(self):
                    return

        type_ = PluginType.by_name(type_string)
        path = config_file_path.parent

        item = ApplicationPluginItem(
            name=name,
            title=title,
            description=description,
            type_=type_,
            path=path,
            priority=priority,
            tooltip_item_id=tooltip_item_id,
            tooltip_pos_right=tooltip_pos_right,
        )
        self._plugins.append(item)
