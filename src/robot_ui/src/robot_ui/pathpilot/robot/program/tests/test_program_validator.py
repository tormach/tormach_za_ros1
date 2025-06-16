import pytest

from robot_ui.pathpilot.robot.program import ProgramReader, Waypoints
from robot_ui.pathpilot.robot.program.program_validator import ProgramValidator


def create_program(tmpdir, data):
    program = tmpdir.join('program.py')
    program.write(data)
    reader = ProgramReader()
    reader.path = str(program)
    return reader.program


@pytest.fixture
def simple_program(tmpdir):
    data = '''\
def main():
    tool()
'''
    return create_program(tmpdir, data)


def test_program_is_valid_per_default(simple_program):
    validator = ProgramValidator()
    validator.program = simple_program

    assert validator.valid is True
    assert len(validator.warnings) == 0


def test_simple_program_is_valid(simple_program):
    validator = ProgramValidator()
    validator.program = simple_program

    validator.analyzeProgram()

    assert validator.valid is True
    assert len(validator.warnings) == 0


@pytest.fixture
def name_overlap_program(tmpdir):
    data = '''\
ornament = p[0, 0, 0, 0, 0, 0]

def ornament():
    pass

def main():
    movej(ornament)
'''
    return create_program(tmpdir, data)


def test_analyze_program_finds_waypoint_names_matching_sub_program(
    name_overlap_program,
):
    validator = ProgramValidator()
    validator.program = name_overlap_program

    validator.analyzeProgram()

    assert validator.valid is False
    assert len(validator.warnings) == 2


@pytest.fixture
def missing_waypoint_program(tmpdir):
    data = '''\
toe = j[0,0,0,0,0,0]

def main():
    movel("with")
    movej(swell)
    movel("mineral")
    movef(toe)
    movej("with")
'''
    return create_program(tmpdir, data)


def test_analyze_program_finds_move_commands_with_missing_waypoints(
    missing_waypoint_program,
):
    validator = ProgramValidator()
    validator.program = missing_waypoint_program
    waypoints = Waypoints()
    wp = waypoints.create_waypoint()
    wp.name = "mineral"
    validator.globalWaypoints = waypoints

    validator.analyzeProgram()

    assert validator.valid is False
    assert len(validator.warnings) == 3


@pytest.fixture
def local_global_waypoint_program(tmpdir):
    data = '''\
widower = p[1,2,3,4,5,6]

def main():
    exit()
    '''
    return create_program(tmpdir, data)


def test_analyze_program_finds_local_waypoint_with_same_name_as_global_waypoint(
    local_global_waypoint_program,
):
    validator = ProgramValidator()
    validator.program = local_global_waypoint_program
    waypoints = Waypoints()
    wp = waypoints.create_waypoint()
    wp.name = "widower"
    validator.globalWaypoints = waypoints

    validator.analyzeProgram()

    assert validator.valid is False
    assert len(validator.warnings) == 1


@pytest.fixture
def builtin_name_program(tmpdir):
    data = '''
def bool():
    pass

def main():
    lake()
    '''
    return create_program(tmpdir, data)


def test_analyze_program_finds_overlap_with_python_builtin(
    builtin_name_program,
):
    validator = ProgramValidator()
    validator.program = builtin_name_program

    validator.analyzeProgram()

    assert validator.valid is False
    assert len(validator.warnings) == 1


@pytest.fixture
def digital_io_program(tmpdir):
    data = '''\
def main():
    set_digital_out("collect", True)
    while get_digital_in("same") is False:
        sync()
    set_digital_out("popular", False)
    while get_digital_in("cheer") is True:
        sync()
    set_digital_out("popular", True)
    set_digital_out(3, False)
    while get_digital_in(9) is True:
        sync()
    '''
    return create_program(tmpdir, data)


def test_analyze_program_finds_missing_digital_io_names(digital_io_program):
    validator = ProgramValidator()
    validator.program = digital_io_program
    validator.digitalInputNames = ["cheer"]
    validator.digitalOutputNames = ["collect"]

    validator.analyzeProgram()

    assert validator.valid is False
    assert len(validator.warnings) == 3


@pytest.fixture
def frame_program(tmpdir):
    data = '''\
piece = p[1,2,3,4,5,6, "bite"]
shallow = p[0,0,0,0,0,0, "some"]
preach = j[0,0,0,0,0,0]
desk = p[6,5,4,3,2,1, "some"]

def main():
    change_user_frame("pig")
    change_tool_frame("employee")
    change_user_frame("bite")
    change_tool_frame("fail")
    change_user_frame("pig")
    change_tool_frame("fail")
    '''
    return create_program(tmpdir, data)


def test_analyze_program_finds_missing_user_and_tool_frames(
    frame_program,
):
    validator = ProgramValidator()
    validator.program = frame_program
    validator.userFrameNames = ["bite"]
    validator.toolFrameNames = ["employee"]

    validator.analyzeProgram()

    assert validator.valid is False
    assert len(validator.warnings) == 6


@pytest.fixture
def default_frame_program(tmpdir):
    data = '''\
def main():
    change_user_frame("")
    change_tool_frame("")
    '''
    return create_program(tmpdir, data)


def test_analyze_program_ignores_default_frames(
    default_frame_program,
):
    validator = ProgramValidator()
    validator.program = default_frame_program

    validator.analyzeProgram()

    assert validator.valid is True


def test_analyze_program_finds_main_loop_when_warning_is_enabled(
    simple_program,
):
    validator = ProgramValidator()
    validator.program = simple_program
    validator.mainLoopWarningEnabled = True

    validator.analyzeProgram()

    assert validator.valid is False
    assert len(validator.warnings) == 1


@pytest.fixture
def main_program_with_exit(tmpdir):
    data = '''\
def main():
    exit()
'''
    return create_program(tmpdir, data)


def test_analyze_program_does_not_create_warning_when_main_contains_exit(
    main_program_with_exit,
):
    validator = ProgramValidator()
    validator.program = main_program_with_exit
    validator.mainLoopWarningEnabled = True

    validator.analyzeProgram()

    assert validator.valid is True


@pytest.fixture
def main_program_with_first_movel(tmpdir):
    data = '''\
waypoint = p[0, 0, 0, 0, 0, 0]

def main():
    movel(waypoint)
    '''
    return create_program(tmpdir, data)


def test_analyze_program_finds_first_movel(main_program_with_first_movel):
    validator = ProgramValidator()
    validator.program = main_program_with_first_movel
    validator.firstMoveWarningEnabled = True

    validator.analyzeProgram()

    assert validator.valid is False, "no warning was created"
    assert len(validator.warnings) == 1


@pytest.fixture
def main_program_with_first_movej(tmpdir):
    data = '''\
waypoint = p[0, 0, 0, 0, 0, 0]

def main():
    movej(waypoint)
    movel(waypoint)
    '''
    return create_program(tmpdir, data)


def test_analyze_program_does_not_create_warning_when_first_is_not_movel(
    main_program_with_first_movej,
):
    validator = ProgramValidator()
    validator.program = main_program_with_first_movej
    validator.firstMoveWarningEnabled = True

    validator.analyzeProgram()

    assert validator.valid is True
