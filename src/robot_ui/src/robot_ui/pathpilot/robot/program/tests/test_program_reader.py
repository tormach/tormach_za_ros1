import pytest

from robot_ui.pathpilot.robot.program import ProgramReader


@pytest.fixture
def simple_program(tmpdir):
    data = '''\
def main():
    movel(p[0, 0, 0, 0, 0, 0])
    movel(p[0, 2.0, 0, 0, 0, 0])
'''
    program = tmpdir.join('simple_program.py')
    program.write(data)
    return str(program)


def test_robot_program_is_empty_per_default():
    reader = ProgramReader()

    assert len(reader.program.waypoints) == 0
    assert reader.program.root_block is None


@pytest.mark.dependency()
def test_robot_program_is_loaded_and_valid_when_path_is_changed(simple_program):
    reader = ProgramReader()

    reader.path = simple_program

    assert reader.valid is True
    assert reader.program.root_block is not None
    assert len(reader.program.root_block.children) == 1


@pytest.mark.dependency(
    depends=["test_robot_program_is_loaded_and_valid_when_path_is_changed"]
)
def test_robot_program_is_reloaded_and_valid_when_update_is_triggered(
    simple_program,
):
    reader = ProgramReader()
    reader.path = simple_program
    reader.program.waypoints.append(object())

    reader.update()

    assert reader.valid is True
    assert len(reader.program.waypoints) == 0


def test_robot_program_is_not_valid_when_loading_fails():
    reader = ProgramReader()

    reader.path = "XJZ6"

    assert reader.valid is False


@pytest.mark.dependency(
    depends=["test_robot_program_is_loaded_and_valid_when_path_is_changed"]
)
def test_robot_program_is_invalidated_when_loading_fails_and_previous_program_was_valid(
    simple_program,
):
    reader = ProgramReader()
    reader.path = simple_program

    reader.path = "Z78ML"

    assert reader.valid is False


@pytest.mark.dependency(
    depends=["test_robot_program_is_loaded_and_valid_when_path_is_changed"]
)
def test_robot_program_is_invalidated_when_clearing_path(simple_program):
    reader = ProgramReader()
    reader.path = simple_program

    reader.path = ''

    assert reader.valid is False
