import os
import pytest

from PySide6.QtCore import QUrl
from robot_ui.pathpilot.robot.program.program_templates import TemplateType


@pytest.fixture
def templates():
    from robot_ui.pathpilot.robot.program.program_templates import (
        ProgramTemplates,
    )

    return ProgramTemplates()


def write_file(path, data, name):
    f = path.join(name)
    f.write(data)


@pytest.fixture
def one_template(tmpdir):
    testdata = '''\
name: empty
title: Empty Program
description: Templates which creates an empty program.
type: simple
'''
    pydata = '''\
def program_name():
    pass
'''
    subdir = tmpdir.mkdir('GyyZRRO')
    write_file(subdir, testdata, 'template.yaml')
    write_file(subdir, pydata, 'program_name.py')
    return subdir


@pytest.fixture
def second_template(tmpdir):
    testdata = '''\
name: flaffer
title: Adela Flaffer
type: simple
'''
    pydata = '''\
def program_name():
    print('hello world')
'''
    subdir = tmpdir.mkdir('qP1')
    write_file(subdir, testdata, 'template.yaml')
    write_file(subdir, pydata, 'program_name.py')
    return subdir


@pytest.fixture
def disabled_template(tmpdir):
    testdata = '''\
name: hydnoid
title: eavesing Minhah
type: simple
enabled: false
'''
    pydata = '''\
def program_name():
    pass
'''
    subdir = tmpdir.mkdir('twPPP2')
    write_file(subdir, testdata, 'template.yaml')
    write_file(subdir, pydata, 'program_name.py')
    return subdir


def test_reading_empty_directory_finds_no_templates(tmpdir, templates):
    templates.searchPaths = [str(tmpdir)]

    templates.update()

    assert len(templates.templates) == 0


@pytest.mark.dependency()
def test_reading_directory_with_one_template_file_finds_one_program_template(
    one_template, templates
):
    templates.searchPaths = [str(one_template)]

    templates.update()

    assert len(templates.templates) == 1
    item1 = templates.templates[0]
    assert item1.name == 'empty'
    assert item1.title == 'Empty Program'
    assert item1.description == 'Templates which creates an empty program.'
    assert item1.type == TemplateType.SimpleTemplate
    assert item1.path == str(one_template)


def test_reading_directory_with_one_template_file_finds_one_program_template_in_subdirectory(
    one_template, templates
):
    templates.searchPaths = [os.path.dirname(str(one_template))]

    templates.update()

    assert len(templates.templates) == 1


def test_reading_two_directories_with_two_template_files_finds_two_program_templates(
    one_template, second_template, templates
):
    templates.searchPaths = [
        str(one_template),
        QUrl.fromLocalFile(str(second_template)).toString(),
    ]

    templates.update()

    assert len(templates.templates) == 2
    item2 = templates.templates[1]
    assert item2.name == 'flaffer'
    assert item2.title == 'Adela Flaffer'
    assert item2.description == ''
    assert item2.type == TemplateType.SimpleTemplate
    assert item2.path == str(second_template)


@pytest.mark.dependency(
    depends=[
        'test_reading_directory_with_one_template_file_finds_one_program_template'
    ]
)
def test_clearing_templates_works(one_template, templates):
    templates.searchPaths = [str(one_template)]
    templates.update()

    templates.clear()

    assert len(templates.templates) == 0


@pytest.mark.dependency(
    depends=[
        'test_reading_directory_with_one_template_file_finds_one_program_template'
    ]
)
def test_applying_template_works(tmpdir, one_template, templates):
    templates.searchPaths = [str(one_template)]
    templates.update()
    template = templates.templates[0]
    target_dir = str(tmpdir.mkdir('rEzKR'))
    target_path = os.path.join(target_dir, 'turkman.py')

    template.apply(target_path)

    assert os.path.isfile(target_path)
    with open(target_path) as f:
        data = f.read()
    assert (
        data
        == '''\
def turkman():
    pass
'''
    )


def test_disabled_template_is_not_added(disabled_template, templates):
    templates.searchPaths = [str(disabled_template)]

    templates.update()

    assert len(templates.templates) == 0
