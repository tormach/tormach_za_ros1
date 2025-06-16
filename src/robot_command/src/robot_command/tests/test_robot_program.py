import pytest

from robot_command.program_blocks import RPLBlock, RootBlock, PassBlock
from robot_command.robot_program import RobotProgram
from robot_command.rpl import Pose, Joints
from robot_command.waypoint import Waypoint, TargetType
from robot_command.testing.program_test_data import DummyBlock


@pytest.fixture
def test_program():
    """
    :return: A program tree
    root
      [0] foo
      [1] bar
      [2] baz
        [0] foo
        [1] bar
    """
    robot_program = RobotProgram()
    root_node = RootBlock(DummyBlock((0, 0), (20, 0)), robot_program)
    root_node.add_child(
        RPLBlock(DummyBlock((1, 0), (2, 0)), root_node, type_='foo'),
        modify=False,
    )
    root_node.add_child(
        RPLBlock(DummyBlock((2, 0), (3, 0)), root_node, type_='bar'),
        modify=False,
    )
    baz_node = RPLBlock(DummyBlock((4, 0), (20, 0)), root_node, type_='baz')
    root_node.add_child(baz_node, modify=False)
    baz_node.add_child(
        RPLBlock(DummyBlock((4, 0), (15, 0)), baz_node, type_='foo'),
        modify=False,
    )
    baz_node.add_child(
        RPLBlock(DummyBlock((16, 0), (20, 0)), baz_node, type_='bar'),
        modify=False,
    )
    waypoints = [
        Waypoint(
            name='debugger',
            target=Pose(385, 115.77, 315.27, -974.45, 701.10, 601.75),
        ),
        Waypoint(
            name='papier',
            target=Joints(495.83, 917, 136.82, -524.00, 540.38, -668),
        ),
    ]
    robot_program.reset_data(root_block=root_node, waypoints=waypoints)
    return robot_program


def test_copying_the_robot_program_creates_a_deepcopy_of_the_nodes(
    test_program,
):
    program = RobotProgram()

    test_program.copy_data_to(program)

    assert program.root_block is not test_program.root_block
    assert (
        program.root_block.children[0]
        is not test_program.root_block.children[0]
    )
    assert (
        program.root_block.children[2].children[0]
        is not test_program.root_block.children[2].children[0]
    )
    assert (
        program.root_block.children[0].node
        == test_program.root_block.children[0].node
    )


def test_copying_the_robot_program_creates_a_deepcopy_of_the_waypoints(
    test_program,
):
    program = RobotProgram()

    test_program.copy_data_to(program)

    assert len(program.waypoints) == 2, 'did not copy the waypoints'
    assert program.waypoints[0] is not test_program.waypoints[0]
    assert program.waypoints[1] is not test_program.waypoints[1]


def test_copying_the_robot_program_does_not_change_the_uuids_of_the_nodes(
    test_program,
):
    program = RobotProgram()

    test_program.copy_data_to(program)

    assert program.root_block.uuid == test_program.root_block.uuid
    assert (
        program.root_block.children[0].uuid
        == test_program.root_block.children[0].uuid
    )
    assert (
        program.root_block.children[2].children[0].uuid
        == test_program.root_block.children[2].children[0].uuid
    )


def test_copying_the_robot_program_does_not_change_the_uuids_of_the_waypoints(
    test_program,
):
    program = RobotProgram()

    test_program.copy_data_to(program)

    assert program.waypoints[0].uuid == test_program.waypoints[0].uuid
    assert program.waypoints[1].uuid == test_program.waypoints[1].uuid


def test_copying_the_robot_program_updates_references_to_the_robot_program_inside_the_nodes(
    test_program,
):
    program = RobotProgram()

    test_program.copy_data_to(program)

    assert program.root_block.program == program
    assert program.root_block.children[0].program == program
    assert program.root_block.children[2].children[1].program == program


def test_copying_the_robot_program_copies_the_program_name(test_program):
    program = RobotProgram()
    test_program.reset_data(name='trusten')

    test_program.copy_data_to(program)

    assert program.name == 'trusten'


def test_copying_the_robot_program_copies_the_path(test_program):
    program = RobotProgram()
    test_program.reset_data(path='/grugrus')

    test_program.copy_data_to(program)

    assert program.path == '/grugrus'


def test_copying_the_robot_program_copies_the_units(test_program):
    program = RobotProgram()
    test_program.reset_data(linear_unit='mm', angular_unit='deg', time_unit='s')

    test_program.copy_data_to(program)

    assert program.linear_unit == 'mm'
    assert program.angular_unit == 'deg'
    assert program.time_unit == 's'


def test_nodes_are_accessible_by_uuid(test_program):
    node, uuid = test_program.root_block, test_program.root_block.uuid
    assert node == test_program.get_block(uuid)
    node, uuid = (
        test_program.root_block.children[2],
        test_program.root_block.children[2].uuid,
    )
    assert node == test_program.get_block(uuid)


def test_waypoints_are_accessible_by_uuid(test_program):
    waypoint, uuid = test_program.waypoints[0], test_program.waypoints[0].uuid
    assert waypoint == test_program.get_waypoint(uuid)


@pytest.fixture
def waypoint_program(tmpdir):
    data = '''\
waypoint_1 = p[144.86, 798.35, -940.22, 129.56, 178.14, 414.95]
waypoint_2 = j[245.87, -558.97, 513.11, 565.52, -173.20, 448.39]

def main():
    movel(waypoint_1)
    movej(waypoint_2)
    '''
    program = tmpdir.join('waypoint_program.py')
    program.write(data)
    return str(program)


@pytest.mark.dependency()
def test_waypoints_are_extracted_correctly_when_reading_program(
    waypoint_program,
):
    program = RobotProgram()

    program.read_from_file(waypoint_program)

    assert len(program.waypoints) == 2, 'failed to extract waypoints'
    assert (
        len(program.root_block.children) == 1
    ), 'failed to remove waypoints from program'
    assert program.waypoints[0].name == 'waypoint_1'
    assert program.waypoints[1].name == 'waypoint_2'


@pytest.mark.dependency(
    depends=['test_waypoints_are_extracted_correctly_when_reading_program']
)
def test_root_node_is_not_modified_after_extracting_waypoints(waypoint_program):
    program = RobotProgram()

    program.read_from_file(waypoint_program)

    assert program.root_block.modified is False


@pytest.fixture
def program_with_unit_definition(tmpdir):
    data = '''\
set_units("mm", "deg", "s")

def main():
    pass
'''
    program = tmpdir.join('unit_program.py')
    program.write(data)
    return str(program)


@pytest.mark.dependency()
def test_units_are_extracted_correctly_when_reading_program(
    program_with_unit_definition,
):
    program = RobotProgram()

    program.read_from_file(program_with_unit_definition)

    assert program.linear_unit == "mm"
    assert program.angular_unit == "deg"
    assert program.time_unit == "s"
    assert (
        len(program.root_block.children) == 1
    ), "failed to remove set_units from program"


@pytest.mark.dependency(
    depends=['test_units_are_extracted_correctly_when_reading_program']
)
def test_root_node_is_not_modified_after_extracting_units(
    program_with_unit_definition,
):
    program = RobotProgram()

    program.read_from_file(program_with_unit_definition)

    assert program.root_block.modified is False


@pytest.fixture
def program_without_unit_definition(tmpdir):
    data = '''\
from robot_command.rpl import *

def main():
    pass
'''
    program = tmpdir.join('people.py')
    program.write(data)
    return str(program)


def test_program_without_unit_definition_is_marked_as_auto_updated(
    program_without_unit_definition,
):
    program = RobotProgram()

    program.read_from_file(program_without_unit_definition)

    assert program.header_auto_updated


@pytest.fixture
def simple_program(tmpdir):
    data = '''\
# sweep marriage
from robot_command.rpl import *
# walk burst sit!
set_units("mm", "rad")
waypoint_2 = j[245.87, -558.97, 513.11, 565.52, -173.20, 448.39]  # rundle jacu

# road rage
def main():
    # some movement commands
    movel(p[0, 0, 0, 0, 0, 0])
    movel(p[0, 2.0, 0, 0, 0, 0])
    movel(p[10, 0, 0, 0, 0, 0])
'''
    program = tmpdir.join('my_program.py')
    program.write(data)
    return str(program)


@pytest.mark.dependency()
def test_reading_program_throws_no_errors(simple_program):
    program = RobotProgram()

    program.read_from_file(simple_program)

    assert program.name == 'my_program'


@pytest.fixture
def broken_program(tmpdir):
    data = '''\
def roofmen():
    pass
'''
    program = tmpdir.join('my_program.py')
    program.write(data)
    return str(program)


def test_reading_program_without_main_program_throws_runtime_error(
    broken_program,
):
    program = RobotProgram()

    with pytest.raises(RuntimeError):
        program.read_from_file(broken_program)


@pytest.fixture
def program_without_newline(tmpdir):
    data = '''\
def main():
    pass\
'''
    program = tmpdir.join('knee.py')
    program.write(data)
    return str(program)


def test_reading_program_without_newline_at_end_correctly_reads_node(
    program_without_newline,
):
    program = RobotProgram()

    program.read_from_file(program_without_newline)

    node = program.root_block.children[0].children[0]
    assert node.type == 'pass'


@pytest.mark.dependency(depends=['test_reading_program_throws_no_errors'])
def test_clearing_program_throws_no_errors(simple_program):
    program = RobotProgram()
    program.read_from_file(simple_program)

    program.clear()

    assert program.name == ''


def test_waypoints_are_inserted_correctly_when_writing_program(simple_program):
    program = RobotProgram()
    program.read_from_file(simple_program)
    program.linear_unit_decimals = 2
    program.angular_unit_decimals = 2

    program.waypoints.append(
        Waypoint(
            name='insures',
            target=[833.18, -770.36, 205.32, -357.29, 763.21, 658],
            target_type=TargetType.Pose,
        )
    )
    program.waypoints.append(
        Waypoint(
            name='deaconed',
            target=[-397.94, 727.79, -266.18, -23, 774.83, 996.16],
            target_type=TargetType.Joints,
        )
    )
    lines = list(program.generate_code())

    assert (
        'insures = p[833.18, -770.36, 205.32, -357.29, 763.21, 658.00]\n'
        == lines[3]
    )
    assert (
        'deaconed = j[-397.94, 727.79, -266.18, -23.00, 774.83, 996.16]\n'
        == lines[4]
    )


def test_units_are_inserted_correctly_when_writing_program(simple_program):
    program = RobotProgram()
    program.read_from_file(simple_program)

    program.reset_data(linear_unit="in", angular_unit="rad", time_unit="min")
    lines = list(program.generate_code())

    assert 'set_units("in", "rad", "min")\n' == lines[1]


@pytest.fixture
def program_without_rpl_import(tmpdir):
    data = '''\
set_units("in", "rad")

def main():
    pass
'''
    program = tmpdir.join('whatever.py')
    program.write(data)
    return str(program)


def test_rpl_import_is_correctly_injected_into_program(
    program_without_rpl_import,
):
    program = RobotProgram()
    program.read_from_file(program_without_rpl_import)

    lines = list(program.generate_code())

    assert 'from robot_command.rpl import *\n' == lines[0]


def test_program_without_rpl_import_is_marked_as_auto_updated(
    program_without_rpl_import,
):
    program = RobotProgram()

    program.read_from_file(program_without_rpl_import)

    assert program.header_auto_updated


def test_program_with_rpl_import_and_unit_definition_is_not_marked_as_auto_updated(
    simple_program,
):
    program = RobotProgram()
    program.read_from_file(simple_program)

    assert program.header_auto_updated is False


def test_written_program_contains_all_comments_and_empty_lines(
    simple_program, tmpdir
):
    program = RobotProgram()
    program_file = str(tmpdir.join('out_program.py'))

    program.read_from_file(simple_program)
    program.write_to_file(program_file)

    with open(program_file) as f:
        data = f.read()

    assert len(data.split('\n')) == 13
    assert '# sweep marriage' in data
    assert '# walk burst sit!' in data
    assert '# road rage' in data
    assert '# some movement commands' in data
    assert '# rundle jacu' in data


def test_new_node_is_inserted_before_other_node_when_created(test_program):
    before_node = test_program.root_block.children[0]

    new_node = test_program.create_block(before_node, type_='movel')

    assert new_node is test_program.root_block.children[0]
    assert before_node is test_program.root_block.children[1]
    assert new_node is test_program.get_block(new_node.uuid)


def test_new_node_is_inserted_after_node_when_created(test_program):
    after_node = test_program.root_block.children[0]

    new_node = test_program.create_block(
        after_node, type_='movel', before=False
    )

    assert new_node is test_program.root_block.children[1]
    assert after_node is test_program.root_block.children[0]
    assert new_node is test_program.get_block(new_node.uuid)


@pytest.fixture
def main_program():
    """
    :return: A program tree
    root
      [0] mainprogram
        [0] foo
        [1] bar
    """
    robot_program = RobotProgram()
    root_node = RootBlock(DummyBlock((0, 0), (3, 0)), robot_program)
    main_node = root_node.add_child(
        RPLBlock(DummyBlock((0, 0), (3, 0)), root_node, type_='mainprogram'),
        modify=False,
    )
    main_node.add_child(
        RPLBlock(DummyBlock((1, 0), (2, 0)), main_node, type_='foo'),
        modify=False,
    )
    main_node.add_child(
        RPLBlock(DummyBlock((2, 0), (3, 0)), main_node, type_='bar'),
        modify=False,
    )
    robot_program.reset_data(root_block=root_node, waypoints=[])
    return robot_program


def test_new_node_is_inserted_at_end_of_program_when_created_with_empty_uuid(
    main_program,
):
    target_node = main_program.root_block.children[0].children[1]

    new_node = main_program.create_block(None, type_='movel')

    assert new_node == main_program.root_block.children[0].children[2]
    assert target_node == main_program.root_block.children[0].children[1]
    assert new_node == main_program.get_block(new_node.uuid)


def test_new_child_node_is_correctly_inserted_as_child_when_created(
    test_program,
):
    parent_node = test_program.root_block.children[0]

    new_node = test_program.create_child_block(parent_node, type_='movel')

    assert len(test_program.root_block.children[0].children) == 1
    assert new_node == test_program.root_block.children[0].children[0]


def test_new_group_node_is_correctly_inserted_at_end_of_group_inside_program(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)

    new_node = test_program.create_group_block(
        node1, type_='movel', append=True
    )

    assert new_node == test_program.root_block.children[2]
    assert new_node.group_head is node1
    assert node1 == test_program.root_block.children[0]
    assert node2 == test_program.root_block.children[1]


def test_new_group_node_is_correctly_inserted_at_end_of_group_at_end_of_program(
    test_program,
):
    node1 = test_program.root_block.children[1]
    node2 = test_program.root_block.children[2]
    node1.add_to_group(node2)

    new_node = test_program.create_group_block(
        node2, type_='movel', append=True
    )

    assert new_node == test_program.root_block.children[3]
    assert new_node.group_head is node1
    assert node1 == test_program.root_block.children[1]
    assert node2 == test_program.root_block.children[2]


def test_new_group_node_is_correctly_inserted_before_node_when_node_is_not_already_in_group(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)

    new_node = test_program.create_group_block(node2, type_='movel')

    assert new_node == test_program.root_block.children[1]
    assert new_node.group_head is node1
    assert node1 == test_program.root_block.children[0]
    assert node2 == test_program.root_block.children[2]


def test_new_group_node_for_head_of_group_inserts_new_node_after_head(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)

    new_node = test_program.create_group_block(node1, type_='movel')

    assert new_node == test_program.root_block.children[1]
    assert new_node.group_head is node1
    assert node1 == test_program.root_block.children[0]
    assert node2 == test_program.root_block.children[2]


def test_new_group_node_for_node_not_in_group_appends_new_node_to_group(
    test_program,
):
    node1 = test_program.root_block.children[0]

    new_node = test_program.create_group_block(node1, type_='movel')

    assert new_node == test_program.root_block.children[1]
    assert new_node.group_head is node1
    assert node1 == test_program.root_block.children[0]


def test_new_node_is_correctly_inserted_before_group_when_created_with_group_node_as_target(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)

    new_node = test_program.create_block(node2, type_='movel', before=True)

    assert new_node == test_program.root_block.children[0]
    assert node1 == test_program.root_block.children[1]
    assert node2 == test_program.root_block.children[2]


def test_new_node_is_correctly_inserted_after_group_when_created_with_group_node_as_target(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)

    new_node = test_program.create_block(node2, type_='movel', before=False)

    assert node1 == test_program.root_block.children[0]
    assert node2 == test_program.root_block.children[1]
    assert new_node == test_program.root_block.children[2]


def test_node_created_after_group_is_correctly_inserted_after_group(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)
    node3 = test_program.root_block.children[2]

    new_node = test_program.create_block(node3, type_='movel')

    assert new_node == test_program.root_block.children[2]
    assert node3 == test_program.root_block.children[3]


@pytest.fixture
def empty_program():
    """
    :return: A program tree
    root
      [0] pass
    """
    robot_program = RobotProgram()
    root_node = RootBlock(DummyBlock((0, 0), (1, 0)), robot_program)
    root_node.add_child(PassBlock(None, root_node), modify=False)
    robot_program.reset_data(root_block=root_node)
    return robot_program


@pytest.mark.dependency()
def test_pass_node_is_replaced_with_new_node_when_created(empty_program):
    before_node = empty_program.root_block.children[0]

    new_node = empty_program.create_block(before_node, type_='movel')

    assert new_node == empty_program.root_block.children[0]
    assert len(empty_program.root_block.children) == 1


def test_remove_node_correctly_removes_node_from_program(test_program):
    node = test_program.root_block.children[2].children[0]

    test_program.remove_block(node)

    assert test_program.root_block.children[2].children[0].type == 'bar'
    assert not test_program.get_block(node.uuid)


def test_remove_node_with_children_also_removes_children_from_program(
    test_program,
):
    node = test_program.root_block.children[2]
    node1 = test_program.root_block.children[2].children[0]
    node2 = test_program.root_block.children[2].children[1]

    test_program.remove_block(node)

    assert len(test_program.root_block.children) == 2
    assert not test_program.get_block(node1.uuid)
    assert not test_program.get_block(node2.uuid)


def test_remove_node_which_is_in_group_removes_node_from_program_and_updates_link(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)

    test_program.remove_block(node2)

    assert len(test_program.root_block.children) == 2
    assert not test_program.get_block(node2.uuid)
    assert node2 not in node1.group_links


def test_remove_node_which_is_head_of_group_also_removes_other_members(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)

    test_program.remove_block(node1)

    assert len(test_program.root_block.children) == 1
    assert not test_program.get_block(node1.uuid)
    assert not test_program.get_block(node2.uuid)


@pytest.fixture()
def almost_empty_program():
    """
    :return: A program tree
    root
      [0] clobber
    """
    robot_program = RobotProgram()
    root_node = RootBlock(DummyBlock((0, 0), (2, 0)), robot_program)
    root_node.add_child(
        RPLBlock(DummyBlock((1, 0), (2, 0)), root_node, type_='clobber'),
        modify=False,
    )
    robot_program.reset_data(root_block=root_node)
    return robot_program


def test_pass_node_is_inserted_when_node_is_removed_and_tree_is_empty(
    almost_empty_program,
):
    program = almost_empty_program
    node = program.root_block.children[0]

    program.remove_block(node)

    assert len(program.root_block.children) == 1
    assert program.root_block.children[0].type == 'pass'


def test_pass_node_is_inserted_when_group_is_removed_and_tree_is_empty(
    test_program,
):
    node1 = test_program.root_block.children[2].children[0]
    node2 = test_program.root_block.children[2].children[1]
    node1.add_to_group(node2)

    test_program.remove_block(node1)

    assert len(test_program.root_block.children[2].children) == 1
    assert test_program.root_block.children[2].children[0].type == 'pass'


@pytest.mark.dependency(
    [
        'test_pass_node_is_replaced_with_new_node_when_created',
        'test_pass_node_is_inserted_when_node_is_removed_and_tree_is_empty',
    ]
)
def test_pass_node_created_as_a_result_of_removing_node_has_a_consistent_uuid(
    empty_program,
):
    program = empty_program

    node = program.root_block.children[0]
    new_node = program.create_block(node, type_='movel')
    same_uuid = new_node.uuid
    program.remove_block(new_node)
    node = program.root_block.children[0]
    first_uuid = node.uuid
    new_node = program.create_block(node, type_='movel', uuid=same_uuid)
    program.remove_block(new_node)
    node = program.root_block.children[0]
    second_uuid = node.uuid

    assert first_uuid == second_uuid


def test_key_error_is_raised_when_attempting_to_remove_a_node_that_is_not_in_the_program(
    test_program,
):
    fake_node = RPLBlock(
        DummyBlock((1, 0), (2, 0)), parent=test_program.root_block
    )

    with pytest.raises(KeyError):
        test_program.remove_block(fake_node)


def test_update_node_property_updates_a_property_of_node(test_program):
    node = test_program.root_block.children[0]
    setattr(node, 'hoared', 5)  # create dummy attribute

    test_program.update_block(node, 'hoared', 10)

    assert node.hoared == 10


def test_update_node_property_which_does_not_exist_raises_attribute_error(
    test_program,
):
    node = test_program.root_block.children[1]

    with pytest.raises(AttributeError):
        test_program.update_block(node, 'aphakial', 962.26)


def test_updating_disabled_property_of_node_in_group_updates_the_whole_group(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)

    test_program.update_block(node1, 'disabled', True)

    assert node1.disabled is True
    assert node2.disabled is True


def test_move_node_before_node_in_same_hierarchical_level_works(test_program):
    node = test_program.root_block.children[1]
    before_node = test_program.root_block.children[0]

    test_program.move_block(node, before_node, before=True)

    assert test_program.root_block.children[0] == node
    assert test_program.root_block.children[1] == before_node


def test_move_node_after_node_in_same_hierarchical_level_works(test_program):
    node = test_program.root_block.children[0]
    after_node = test_program.root_block.children[1]

    test_program.move_block(node, after_node, before=False)

    assert test_program.root_block.children[1] == node
    assert test_program.root_block.children[0] == after_node


def test_move_node_before_node_in_different_hierarchical_level_works(
    test_program,
):
    node = test_program.root_block.children[1]
    before_node = test_program.root_block.children[2].children[1]

    test_program.move_block(node, before_node, before=True)

    assert test_program.root_block.children[1].children[1] == node
    assert (
        test_program.root_block.children[1].children[1].parent
        == test_program.root_block.children[1]
    )
    assert test_program.root_block.children[1].children[1].level == 2


def test_move_node_tree_ancestor_to_child_does_not_move_node(test_program):
    node = test_program.root_block.children[2]
    before_node = test_program.root_block.children[2].children[1]

    test_program.move_block(node, before_node)

    assert len(test_program.root_block.children) == 3
    assert test_program.root_block.children[2] is node
    assert test_program.root_block.children[2].children[1] is before_node


def test_move_node_in_group_before_target_inside_same_group_works(test_program):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)
    node1.add_to_group(node3)

    test_program.move_block(node3, node2, before=True)

    assert test_program.root_block.children[1] is node3
    assert test_program.root_block.children[2] is node2
    assert node1.group_links[0] is node3
    assert node1.group_links[1] is node2


def test_move_node_in_group_after_target_inside_same_group_works(test_program):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)
    node1.add_to_group(node3)

    test_program.move_block(node2, node3, before=False)

    assert test_program.root_block.children[1] is node3
    assert test_program.root_block.children[2] is node2
    assert node1.group_links[0] is node3
    assert node1.group_links[1] is node2


def test_move_node_in_group_before_head_does_not_move_node(test_program):
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node2.add_to_group(node3)

    test_program.move_block(node3, node2)

    assert test_program.root_block.children[1] is node2
    assert test_program.root_block.children[2] is node3


def test_move_node_in_group_after_head_moves_node(test_program):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)
    node1.add_to_group(node3)

    test_program.move_block(node3, node1, before=False)

    assert test_program.root_block.children[0] is node1
    assert test_program.root_block.children[1] is node3
    assert node1.group_links[0] is node3


def test_move_fixed_node_in_group_before_other_node_does_not_move_node(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)
    node1.add_to_group(node3)
    node3.group_fixed = True

    test_program.move_block(node3, node2, before=True)

    assert test_program.root_block.children[1] is node2
    assert test_program.root_block.children[2] is node3


def test_move_node_after_fixed_node_does_not_move_node(test_program):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)
    node1.add_to_group(node3)
    node3.group_fixed = True

    test_program.move_block(node2, node3, before=False)

    assert test_program.root_block.children[0] is node1
    assert test_program.root_block.children[1] is node2
    assert test_program.root_block.children[2] is node3


def test_move_head_node_to_group_target_does_not_move_node(test_program):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)

    test_program.move_block(node1, node2, before=False)

    assert test_program.root_block.children[0] is node1
    assert test_program.root_block.children[1] is node2


def test_move_node_in_group_before_target_outside_of_group_moves_whole_group(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node2.add_to_group(node3)

    test_program.move_block(node3, node1, before=True)

    assert test_program.root_block.children[0] is node2
    assert test_program.root_block.children[1] is node3
    assert test_program.root_block.children[2] is node1


def test_move_node_in_group_after_target_outside_of_group_moves_whole_group(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)

    test_program.move_block(node2, node3, before=False)

    assert test_program.root_block.children[0] is node3
    assert test_program.root_block.children[1] is node1
    assert test_program.root_block.children[2] is node2


def test_move_node_outside_of_group_into_group_with_before_moves_node_before_group(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)

    test_program.move_block(node3, node2, before=True)

    assert test_program.root_block.children[0] is node3
    assert test_program.root_block.children[1] is node1
    assert test_program.root_block.children[2] is node2


def test_move_node_outside_of_group_into_group_with_after_moves_node_after_group(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node2.add_to_group(node3)

    test_program.move_block(node1, node2, before=False)

    assert test_program.root_block.children[0] is node2
    assert test_program.root_block.children[1] is node3
    assert test_program.root_block.children[2] is node1


def test_move_node_after_group_into_group_with_after_does_not_move_node(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)

    result = test_program.move_block(node3, node1, before=False)

    assert result is False
    assert test_program.root_block.children[0] is node1
    assert test_program.root_block.children[1] is node2
    assert test_program.root_block.children[2] is node3


@pytest.fixture()
def empty_tree_test_program():
    """
    :return: A program tree
    root
      [0] foo
        [0] baz
      [1] bar
        [0] pass
    """
    robot_program = RobotProgram()
    root_node = RootBlock(DummyBlock((0, 0), (10, 0)), robot_program)
    foo_node = RPLBlock(DummyBlock((1, 0), (3, 0)), root_node, type_='foo')
    root_node.add_child(foo_node, modify=False)
    foo_node.add_child(
        RPLBlock(DummyBlock((2, 0), (3, 0)), foo_node, type_='baz'),
        modify=False,
    )
    bar_node = RPLBlock(DummyBlock((4, 0), (10, 0)), root_node, type_='bar')
    root_node.add_child(bar_node, modify=False)
    bar_node.add_child(PassBlock(None, bar_node), modify=False)
    robot_program.reset_data(root_block=root_node)

    return robot_program


def test_move_node_that_leaves_behind_an_empty_tree_inserts_pass_node(
    empty_tree_test_program,
):
    program = empty_tree_test_program
    node = program.root_block.children[0].children[0]
    before_node = program.root_block.children[1].children[0]

    program.move_block(node, before_node)

    assert len(program.root_block.children[0].children) == 1
    assert program.root_block.children[0].children[0].type == 'pass'
    assert program.get_block(node.uuid) == node


def test_when_node_is_moved_into_a_tree_with_pass_node_pass_node_is_removed(
    empty_tree_test_program,
):
    program = empty_tree_test_program
    node = program.root_block.children[0].children[0]
    before_node = program.root_block.children[1].children[0]

    program.move_block(node, before_node)

    assert len(program.root_block.children[1].children) == 1
    assert program.root_block.children[1].children[0].type == 'baz'


@pytest.mark.dependency(
    [
        'test_move_node_that_leaves_behind_an_empty_tree_inserts_pass_node',
        'test_when_node_is_moved_into_a_tree_with_pass_node_pass_node_is_removed',
    ]
)
def test_pass_node_created_as_a_result_of_moving_node_has_a_consistent_uuid(
    empty_tree_test_program,
):
    program = empty_tree_test_program

    node = program.root_block.children[0].children[0]
    before_node = program.root_block.children[1].children[0]
    program.move_block(node, before_node)
    pass_node = program.root_block.children[0].children[0]
    first_uuid = pass_node.uuid
    program.move_block(node, pass_node)
    before_node = program.root_block.children[1].children[0]
    program.move_block(node, before_node)
    pass_node = program.root_block.children[0].children[0]
    second_uuid = pass_node.uuid

    assert first_uuid == second_uuid


def test_moving_node_before_itself_is_ignored(test_program):
    node = test_program.root_block.children[0]

    done = test_program.move_block(node, node, before=True)

    assert not done


def test_moving_node_before_node_after_itself_is_ignore(test_program):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]

    done = test_program.move_block(node1, node2, before=True)

    assert not done


def test_moving_node_after_itself_is_ignored(test_program):
    node = test_program.root_block.children[0]

    done = test_program.move_block(node, node, before=False)

    assert not done


def test_moving_node_after_node_before_itself_is_ignored(test_program):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]

    done = test_program.move_block(node2, node1, before=False)

    assert not done


def test_copy_node_copies_node_before_other_node(test_program):
    before_node = test_program.root_block.children[0]
    source_node = test_program.root_block.children[1]

    new_node = test_program.copy_block(source_node, before_node)

    assert new_node == test_program.root_block.children[0]
    assert before_node == test_program.root_block.children[1]
    assert new_node == test_program.get_block(new_node.uuid)
    assert new_node.uuid != source_node.uuid


def test_copy_node_copies_node_after_other_node(test_program):
    after_node = test_program.root_block.children[0]
    source_node = test_program.root_block.children[1]

    new_node = test_program.copy_block(source_node, after_node, before=False)

    assert new_node == test_program.root_block.children[1]
    assert after_node == test_program.root_block.children[0]
    assert new_node == test_program.get_block(new_node.uuid)
    assert new_node.uuid != source_node.uuid


def test_copying_node_with_children_also_copies_children_and_updates_uuids(
    test_program,
):
    before_node = test_program.root_block.children[0]
    source_node = test_program.root_block.children[2]

    new_node = test_program.copy_block(source_node, before_node)

    assert new_node == test_program.root_block.children[0]
    assert len(test_program.root_block.children[0].children) == 2
    first_child = test_program.root_block.children[0].children[0]
    assert (
        first_child.uuid != test_program.root_block.children[3].children[0].uuid
    )
    assert first_child == test_program.get_block(first_child.uuid)
    second_child = test_program.root_block.children[0].children[1]
    assert (
        second_child.uuid
        != test_program.root_block.children[3].children[1].uuid
    )
    assert second_child == test_program.get_block(second_child.uuid)


def test_copying_node_in_group_before_target_inside_group_works(test_program):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)
    node1.add_to_group(node3)

    new_node = test_program.copy_block(node3, node2)

    assert test_program.root_block.children[1] is new_node
    assert new_node.type == node3.type


def test_copying_node_in_group_after_target_inside_group_works(test_program):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)
    node1.add_to_group(node3)

    new_node = test_program.copy_block(node3, node2, before=False)

    assert test_program.root_block.children[2] is new_node
    assert new_node.type == node3.type
    assert new_node.in_group
    assert new_node.group_head is node1
    assert node1.group_links[1] is new_node


def test_copy_node_in_group_before_head_does_not_copy_node(test_program):
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node2.add_to_group(node3)

    test_program.copy_block(node3, node2)

    assert test_program.root_block.children[1] is node2
    assert test_program.root_block.children[2] is node3


def test_copy_node_in_group_after_head_copies_node(test_program):
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node2.add_to_group(node3)

    new_node = test_program.copy_block(node3, node2, before=False)

    assert test_program.root_block.children[2] is new_node
    assert new_node.type == node3.type
    assert new_node.in_group
    assert node2.group_links[0] is new_node


def test_copy_fixed_node_in_group_before_other_node_does_not_copy_node(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node1.add_to_group(node2)
    node1.add_to_group(node3)
    node3.group_fixed = True

    test_program.copy_block(node3, node2, before=True)

    assert test_program.root_block.children[1] is node2
    assert test_program.root_block.children[2] is node3


def test_copy_node_in_group_before_target_outside_of_group_copies_whole_group_before_target(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node2.add_to_group(node3)

    new_node = test_program.copy_block(node3, node1)

    assert test_program.root_block.children[0] is new_node
    assert len(test_program.root_block.children) == 5
    new_node2 = test_program.root_block.children[0]
    new_node3 = test_program.root_block.children[1]
    assert node2 is not new_node2
    assert node2.type == new_node2.type
    assert node3 is not new_node3
    assert node3.type == new_node3.type
    assert new_node2.in_group
    assert new_node3.in_group
    assert new_node3.group_head is new_node2


def test_copy_node_in_group_after_target_outside_of_group_copies_whole_group_after_target(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node3 = test_program.root_block.children[2]
    node2.add_to_group(node3)

    new_node = test_program.copy_block(node3, node1, before=False)

    assert test_program.root_block.children[1] is new_node
    assert len(test_program.root_block.children) == 5
    new_node2 = test_program.root_block.children[1]
    new_node3 = test_program.root_block.children[2]
    assert node2 is not new_node2
    assert node2.type == new_node2.type
    assert node3 is not new_node3
    assert node3.type == new_node3.type
    assert new_node2.in_group
    assert new_node3.in_group
    assert new_node3.group_head is new_node2


def test_copy_node_outside_of_group_into_group_with_before_copies_node_before_group(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)
    source_node = test_program.root_block.children[2]

    new_node = test_program.copy_block(source_node, node2)

    assert new_node == test_program.root_block.children[0]
    assert node1 == test_program.root_block.children[1]
    assert node2 == test_program.root_block.children[2]


def test_copy_node_outside_of_group_into_group_with_after_copies_node_after_group(
    test_program,
):
    node1 = test_program.root_block.children[0]
    node2 = test_program.root_block.children[1]
    node1.add_to_group(node2)
    source_node = test_program.root_block.children[2]

    new_node = test_program.copy_block(source_node, node2, before=False)

    assert new_node == test_program.root_block.children[2]
    assert node1 == test_program.root_block.children[0]
    assert node2 == test_program.root_block.children[1]


def test_when_node_is_copied_into_a_tree_with_pass_node_pass_node_is_removed(
    empty_tree_test_program,
):
    program = empty_tree_test_program
    node = program.root_block.children[0].children[0]
    before_node = program.root_block.children[1].children[0]

    program.copy_block(node, before_node)

    assert len(program.root_block.children[1].children) == 1
    assert program.root_block.children[1].children[0].type == 'baz'


def test_create_waypoint_adds_new_waypoint_and_inserts_uuid(test_program):
    waypoint = test_program.create_waypoint()

    assert waypoint in test_program.waypoints
    assert waypoint == test_program.get_waypoint(waypoint.uuid)


def test_remove_waypoint_removes_waypoint_and_removes_uuid(test_program):
    waypoint = test_program.waypoints[0]

    test_program.remove_waypoint(waypoint)

    assert waypoint not in test_program.waypoints
    assert test_program.get_waypoint(waypoint.uuid) is None


def test_removing_waypoint_not_in_program_raises_a_keyerror(test_program):
    waypoint = Waypoint()

    with pytest.raises(KeyError):
        test_program.remove_waypoint(waypoint)


def test_update_waypoint_property_updates_a_property_of_the_waypoint(
    test_program,
):
    waypoint = test_program.waypoints[1]
    setattr(waypoint, 'biotites', 61)  # create dummy attribute

    test_program.update_waypoint(waypoint, 'biotites', 456)

    assert waypoint.biotites == 456


def test_update_waypoint_property_which_does_not_exist_raises_attribute_error(
    test_program,
):
    waypoint = test_program.waypoints[0]

    with pytest.raises(AttributeError):
        test_program.update_waypoint(waypoint, 'subcase', '1LJydSz')
