import pytest

from robot_ui.pathpilot.robot.program import ProgramUiReader


@pytest.fixture
def reader():
    return ProgramUiReader()


def test_program_path_without_matching_qml_file_is_invalid(tmpdir, reader):
    program = tmpdir.join('holiday.py')
    program.write('ue1z89')

    reader.programPath = str(program)

    assert reader.valid is False
    assert reader.uiMainPath == ""


def test_program_path_with_matching_qml_file_yields_qml_main(tmpdir, reader):
    program = tmpdir.join('ceremony.py')
    program.write('UWhS4pn')
    ui = tmpdir.join('ceremony.qml')
    ui.write('Z78v1')

    reader.programPath = str(program)

    assert reader.valid is True
    assert reader.uiMainPath == str(ui)


def test_program_path_with_matching_directory_name_yields_qml_import_path(
    tmpdir, reader
):
    prog_dir = tmpdir.mkdir('ceremony')
    program = prog_dir.join('ceremony.py')
    program.write('UWhS4pn')
    ui = prog_dir.join('ceremony.qml')
    ui.write('Z78v1')

    reader.programPath = str(program)

    assert reader.valid is True
    assert reader.uiImportPath == str(prog_dir)


def test_empty_program_path_yields_empty_qml_main(tmpdir, reader):
    reader.programPath = tmpdir.join('banana.py')
    reader.programPath = ''

    assert reader.valid is False
    assert reader.uiMainPath == ""


def test_empty_program_path_yields_empty_ui_import_path(tmpdir, reader):
    reader.programPath = tmpdir.join('sunset.py')
    reader.programPath = ''

    assert reader.valid is False
    assert reader.uiImportPath == ""
