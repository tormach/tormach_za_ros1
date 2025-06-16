import sys

import pytest
import os

from PySide6.QtCore import QUrl
from robot_ui.pathpilot.core.application_plugins import PluginType


@pytest.fixture
def plugins():
    from robot_ui.pathpilot.core.application_plugins import ApplicationPlugins

    return ApplicationPlugins()


def write_plugin_file(path, data, name):
    f = path.join(name)
    f.write(data)


@pytest.fixture
def one_plugin(tmpdir):
    testdata = '''\
name: gripper
title: Gripper
description: Opens or closes the gripper
type: conversational
priority: 10
'''
    pydata = '''\
def register_types():
    print('foo')
'''
    subdir = tmpdir.mkdir('sub')
    write_plugin_file(subdir, testdata, 'plugin.yaml')
    write_plugin_file(subdir, pydata, 'gripper.py')
    return subdir


@pytest.fixture
def second_plugin(tmpdir):
    testdata = '''\
name: rotate
title: Rotate
description: Rotate the axis
type: conversational
priority: 1
'''
    pydata = '''\
def register_types():
    print('bar')
'''
    subdir = tmpdir.mkdir('sub2')
    write_plugin_file(subdir, testdata, 'plugin.yaml')
    write_plugin_file(subdir, pydata, 'rotate.py')
    return subdir


@pytest.fixture
def disabled_plugin(tmpdir):
    testdata = '''\
name: hallot
title: Hallot
enabled: False
type: conversational
'''
    pydata = '''\
def register_types():
    pass
'''
    subdir = tmpdir.mkdir('UJ6QkZq')
    write_plugin_file(subdir, testdata, 'plugin.yaml')
    write_plugin_file(subdir, pydata, 'hallot.py')
    return subdir


def test_reading_empty_directory_finds_no_application_plugins(tmpdir, plugins):
    subdir = tmpdir.mkdir('sub')
    plugins.searchPaths = [str(subdir)]

    plugins.updatePlugins()

    assert len(plugins.plugins) == 0


@pytest.mark.dependency()
def test_reading_directory_with_one_plugin_file_finds_one_application_plugin_in_directory(
    one_plugin, plugins
):
    plugins.searchPaths = [str(one_plugin)]

    plugins.updatePlugins()

    assert len(plugins.plugins) == 1
    plugin1 = plugins.plugins[0]
    assert plugin1.name == 'gripper'
    assert plugin1.title == 'Gripper'
    assert plugin1.description == 'Opens or closes the gripper'
    assert plugin1.mainFile == QUrl('file://%s/gripper.qml' % str(one_plugin))
    assert plugin1.type == PluginType.ConversationalPlugin
    assert plugin1.priority == 10


def test_reading_directory_with_one_plugin_file_finds_one_application_plugin_in_subdirectory(
    one_plugin, plugins
):
    plugins.searchPaths = [os.path.dirname(str(one_plugin))]

    plugins.updatePlugins()

    assert len(plugins.plugins) == 1


def test_reading_two_directories_with_two_plugin_files_finds_two_application_plugins_ordered_by_priority(
    one_plugin, second_plugin, plugins
):
    plugins.searchPaths = [
        str(one_plugin),
        QUrl.fromLocalFile(str(second_plugin)).toString(),
    ]

    plugins.updatePlugins()

    assert len(plugins.plugins) == 2
    assert plugins.plugins[0].name == 'rotate', 'plugin priority ignored'
    assert plugins.plugins[1].name == 'gripper', 'plugin priority ignored'
    r_plugin = plugins.plugins[0]
    assert r_plugin.name == 'rotate'
    assert r_plugin.title == 'Rotate'
    assert r_plugin.description == 'Rotate the axis'
    assert r_plugin.mainFile == QUrl(
        'file://%s/rotate.qml' % str(second_plugin)
    )
    assert r_plugin.type == PluginType.ConversationalPlugin
    assert r_plugin.priority == 1


@pytest.mark.dependency(
    depends=[
        'test_reading_directory_with_one_plugin_file_finds_one_application_plugin_in_directory'
    ]
)
def test_clearing_plugins_works(one_plugin, plugins):
    plugins.searchPaths = [str(one_plugin)]
    plugins.updatePlugins()

    plugins.clearPlugins()

    assert len(plugins.plugins) == 0


def test_loading_plugin_works(second_plugin, plugins):
    plugins.searchPaths = [str(second_plugin)]

    plugins.updatePlugins()
    plugin = plugins.plugins[0]
    plugin.loadPlugin()

    assert 'rotate' in sys.modules


def test_disabled_plugin_is_not_added(disabled_plugin, plugins):
    plugins.searchPaths = [os.path.dirname(str(disabled_plugin))]

    plugins.updatePlugins()

    assert len(plugins.plugins) == 0
