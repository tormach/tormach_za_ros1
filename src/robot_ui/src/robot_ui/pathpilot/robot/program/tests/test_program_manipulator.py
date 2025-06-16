import pytest

from robot_command import Waypoint
from robot_command.program_blocks import (
    RPLBlock,
    RootBlock,
    ProgramBlock,
    CallBlock,
)
from robot_command.testing.program_test_data import DummyProgram, DummyBlock
from robot_ui.pathpilot.robot.program import RobotProgram, ProgramManipulator


@pytest.fixture
def test_program():
    """
    :return: A program tree:
    root
      [0] molassy
      [1] straught
    """
    robot_program = RobotProgram()
    root_block = RootBlock(DummyBlock((0, 0), (20, 0)), robot_program)
    root_block.add_child(
        RPLBlock(DummyBlock((1, 0), (2, 0)), root_block, type_='molassy'),
        modify=False,
    )
    root_block.add_child(
        RPLBlock(DummyBlock((2, 0), (3, 0)), root_block, type_='straught'),
        modify=False,
    )

    robot_program.reset_data(root_block=root_block)
    return robot_program


@pytest.fixture
def test_program2():
    """
    :return: Waypoints:
    [0] haply
    [1] frosteds
    [2] feterita
    """
    robot_program = RobotProgram()
    waypoints = [
        Waypoint(name='haply'),
        Waypoint(name='frosteds'),
        Waypoint(name='feterita'),
    ]
    robot_program.reset_data(waypoints=waypoints)
    return robot_program


@pytest.fixture
def program_with_sub_programs():
    """
    root
      [0] sub_program_1
      [1] sub_program_2
      [2] main
        [0] call sub_program_1
    """
    robot_program = RobotProgram()
    root_block = RootBlock(DummyBlock((0, 0), (20, 0)), robot_program)
    root_block.add_child(
        ProgramBlock(
            DummyBlock((1, 0), (2, 0)),
            root_block,
            name='sub_prog_1',
            type_='subprogram',
        )
    )
    root_block.add_child(
        ProgramBlock(
            DummyBlock((3, 0), (4, 0)),
            root_block,
            name='sub_prog_2',
            type_='subprogram',
        )
    )
    main_block = ProgramBlock(
        DummyBlock((5, 0), (20, 0)), root_block, type_='mainprogram'
    )
    root_block.add_child(main_block)
    main_block.add_child(
        CallBlock(DummyBlock((6, 0), (7, 0)), main_block, name='sub_prog_1')
    )
    robot_program.reset_data(root_block=root_block)
    return robot_program


@pytest.fixture()
def test_blocks():
    """
    :return: A tree of blocks:
    root
      [0] jeddock
    """

    root_block = RootBlock(DummyBlock((0, 0), (20, 0)), DummyProgram(path=''))
    root_block.add_child(
        RPLBlock(DummyBlock((1, 0), (2, 0)), root_block, type_='jeddock'),
        modify=False,
    )

    return root_block


def test_when_source_program_is_set_modified_program_tree_is_reset(
    test_program,
):
    manipulator = ProgramManipulator()

    manipulator.sourceProgram = test_program

    assert manipulator.modifiedProgram.root_block.children[1].type == 'straught'


def test_when_source_program_is_modified_modifed_program_is_reset(
    test_program, test_blocks
):
    manipulator = ProgramManipulator()

    manipulator.sourceProgram = test_program
    manipulator.sourceProgram.reset_data(root_block=test_blocks)

    assert manipulator.modifiedProgram.root_block.children[0].type == 'jeddock'


def test_remove_block_removes_the_program_block(test_program):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program

    block_uuid = test_program.root_block.children[1].uuid
    manipulator.removeBlock(block_uuid)

    assert len(test_program.root_block.children) == 2
    assert len(manipulator.modifiedProgram.root_block.children) == 1
    assert manipulator.modifiedProgram.root_block.children[0].type == 'molassy'


def test_remove_waypoint_removes_the_waypoint_from_the_modified_program(
    test_program2,
):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program2

    waypoint_uuid = test_program2.waypoints[1].uuid
    manipulator.removeWaypoint(waypoint_uuid)

    assert len(test_program2.waypoints) == 3
    assert len(manipulator.modifiedProgram.waypoints) == 2
    assert manipulator.modifiedProgram.waypoints[1].name == 'feterita'


def test_reset_manipulator_reverts_any_modifications_to_the_robot_program(
    test_program,
):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program

    before_uuid = test_program.root_block.children[1].uuid
    manipulator.createBlock(before_uuid, type_='movel')
    manipulator.createBlock(before_uuid, type_='movel')
    manipulator.resetHistory()

    assert len(manipulator.modifiedProgram.root_block.children) == 2


@pytest.fixture()
def program_with_modifiable_block(test_program):
    class ModifyableBlock(RPLBlock):
        def __init__(self, block, parent, **kwargs):
            super().__init__(block, parent, **kwargs)
            self.property1 = ''
            self.property2 = 0

    test_program.root_block.add_child(
        ModifyableBlock(DummyBlock((0, 0), (20, 0)), test_program.root_block),
        modify=False,
    )

    return test_program


def test_update_block_updates_properties_of_the_program_block(
    program_with_modifiable_block,
):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = program_with_modifiable_block
    block = program_with_modifiable_block.root_block.children[2]

    manipulator.updateBlock(
        block.uuid, {'property1': 'basalia', 'property2': 515}
    )

    out_block = manipulator.modifiedProgram.root_block.children[2]
    assert out_block.property1 == 'basalia'
    assert out_block.property2 == 515


def test_create_block_adds_a_new_block(test_program):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program

    target_uuid = test_program.root_block.children[0].uuid
    uuid = manipulator.createBlock(target_uuid, type_='movel')

    assert test_program.root_block.children[0].type == 'molassy'
    assert manipulator.modifiedProgram.root_block.children[0].type == 'molassy'
    out_block = manipulator.modifiedProgram.root_block.children[1]
    assert out_block.type == 'movel'
    assert out_block.uuid == uuid


def test_copy_block_copies_a_block(test_program):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program

    before_uuid = test_program.root_block.children[0].uuid
    source_uuid = test_program.root_block.children[1].uuid
    uuid = manipulator.copyBlock(source_uuid, before_uuid)

    assert test_program.root_block.children[0].type == 'molassy'
    assert manipulator.modifiedProgram.root_block.children[0].type == 'molassy'
    out_block = manipulator.modifiedProgram.root_block.children[1]
    assert out_block.type == 'straught'
    assert out_block.uuid == uuid


def test_create_child_block_adds_a_new_child_block(test_program):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program

    parent_uuid = test_program.root_block.children[0].uuid
    uuid = manipulator.createChildBlock(parent_uuid, type_='movel')

    assert len(test_program.root_block.children[0].children) == 0
    assert len(manipulator.modifiedProgram.root_block.children[0].children) == 1
    out_block = manipulator.modifiedProgram.root_block.children[0].children[0]
    assert out_block.type == 'movel'
    assert out_block.uuid == uuid


def test_create_group_block_adds_a_new_group_block(test_program):
    manipulator = ProgramManipulator()
    test_program.root_block.children[0].add_to_group(
        test_program.root_block.children[1]
    )
    manipulator.sourceProgram = test_program

    group_block_uuid = test_program.root_block.children[0].uuid
    uuid = manipulator.createGroupBlock(
        group_block_uuid, type_='movel', append=True
    )

    assert len(test_program.root_block.children) == 2
    assert len(manipulator.modifiedProgram.root_block.children) == 3
    out_block = manipulator.modifiedProgram.root_block.children[2]
    assert out_block.type == 'movel'
    assert out_block.uuid == uuid


def test_update_block_with_partial_error_is_completely_rolled_back(
    program_with_modifiable_block,
):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = program_with_modifiable_block
    block = program_with_modifiable_block.root_block.children[2]

    manipulator.updateBlock(block.uuid, {'property1': 'belay', 'placated': 561})

    out_block = manipulator.modifiedProgram.root_block.children[2]
    assert out_block.property1 == ''
    assert out_block.property2 == 0


def test_update_waypoint_updates_properties_of_the_waypoint(test_program2):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program2

    waypoint = test_program2.waypoints[0]
    manipulator.updateWaypoint(
        waypoint.uuid, {'name': 'upquiver', 'target': []}
    )

    assert test_program2.waypoints[0].name == 'haply'
    assert manipulator.modifiedProgram.waypoints[1].name == 'frosteds'
    out_waypoint = manipulator.modifiedProgram.waypoints[0]
    assert out_waypoint.name == 'upquiver'
    assert out_waypoint.target == []


def test_update_waypoint_with_partial_error_is_completely_rolled_back(
    test_program2,
):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program2

    waypoint = test_program2.waypoints[2]
    manipulator.updateWaypoint(
        waypoint.uuid, {'name': 'anilid', 'MRnQM': 266.48}
    )

    out_waypoint = manipulator.modifiedProgram.waypoints[2]
    assert out_waypoint.name == 'feterita'


def test_add_waypoint_adds_a_new_waypoint_and_updates_the_properties(
    test_program2,
):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program2

    manipulator.addWaypoint({'name': 'doddery'})

    assert len(test_program2.waypoints) == 3
    assert len(manipulator.modifiedProgram.waypoints) == 4
    assert manipulator.modifiedProgram.waypoints[3].name == 'doddery'


def test_move_block_with_before_moves_the_block_before_the_other_block(
    test_program,
):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program

    block_uuid = test_program.root_block.children[1].uuid
    before_uuid = test_program.root_block.children[0].uuid
    manipulator.moveBlock(block_uuid, before_uuid, before=True)

    assert manipulator.sourceProgram.root_block.children[0].uuid == before_uuid
    assert manipulator.sourceProgram.root_block.children[1].uuid == block_uuid
    assert manipulator.modifiedProgram.root_block.children[0].uuid == block_uuid
    assert (
        manipulator.modifiedProgram.root_block.children[1].uuid == before_uuid
    )


def test_move_block_with_after_moves_the_block_after_the_other_block(
    test_program,
):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program

    block_uuid = test_program.root_block.children[0].uuid
    after_uuid = test_program.root_block.children[1].uuid
    manipulator.moveBlock(block_uuid, after_uuid, before=False)

    assert manipulator.sourceProgram.root_block.children[1].uuid == after_uuid
    assert manipulator.sourceProgram.root_block.children[0].uuid == block_uuid
    assert manipulator.modifiedProgram.root_block.children[1].uuid == block_uuid
    assert manipulator.modifiedProgram.root_block.children[0].uuid == after_uuid


def test_move_block_where_target_is_next_after_block_is_ignored(test_program):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = test_program

    block_uuid = test_program.root_block.children[0].uuid
    before_uuid = test_program.root_block.children[1].uuid

    assert manipulator.modifiedProgram.root_block.children[0].uuid == block_uuid
    assert (
        manipulator.modifiedProgram.root_block.children[1].uuid == before_uuid
    )


def test_rename_sub_program_renames_sub_programs_and_calls(
    program_with_sub_programs,
):
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = program_with_sub_programs

    manipulator.renameSubProgram('sub_prog_1', 'new_name')

    assert program_with_sub_programs.root_block.children[0].name == 'sub_prog_1'
    assert manipulator.modifiedProgram.root_block.children[0].name == 'new_name'
    main_block = program_with_sub_programs.root_block.children[2]
    assert main_block.children[0].name == 'sub_prog_1'
    main_block = manipulator.modifiedProgram.root_block.children[2]
    assert main_block.children[0].name == 'new_name'
