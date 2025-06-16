import pytest

from robot_command.program_blocks import RPLBlockWalker, RPLBlock
from robot_command.program_blocks.rpl_block import (
    RPLBlockRootWalker,
    RPLBlockScopeWalker,
)


def test_rpl_block_walker_does_not_iterate_over_empty_tree():
    tree = None

    walker = RPLBlockWalker(tree)

    assert sum(1 for _ in walker) == 0


def test_rpl_block_root_walker_does_not_iterate_over_empty_tree():
    tree = None

    walker = RPLBlockRootWalker(tree)

    assert sum(1 for _ in walker) == 0


@pytest.fixture
def program_tree():
    """
    0
    - 1
    -- 3
    --- 5
    -- 4
    --- 6
    --- 7
    - 2
    """
    root = RPLBlock(0, None, program=object())

    first = RPLBlock(1, root)
    root.add_child(first, modify=False)
    third = RPLBlock(3, first)
    first.add_child(third, modify=False)
    block = RPLBlock(5, third)
    third.add_child(block, modify=False)
    fourth = RPLBlock(4, first)
    first.add_child(fourth, modify=False)
    block = RPLBlock(6, fourth)
    fourth.add_child(block, modify=False)
    block = RPLBlock(7, fourth)
    fourth.add_child(block, modify=False)

    second = RPLBlock(2, root)
    root.add_child(second, modify=False)

    return root


def test_rpl_block_walker_walks_over_program_tree_bfs(program_tree):
    unfolded = [i for i in RPLBlockWalker(program_tree)]

    assert [0, 1, 3, 5, 4, 6, 7, 2] == [i.node for i in unfolded]


def test_rpl_block_walker_walks_over_program_tree_dfs(program_tree):
    unfolded = [i for i in RPLBlockWalker(program_tree, dfs=True)]

    assert [5, 3, 6, 7, 4, 1, 2, 0] == [i.node for i in unfolded]


def test_rpl_block_root_walker_iterates_over_program_root(program_tree):
    node = program_tree.children[0].children[1]
    unfolded = [i for i in RPLBlockRootWalker(node)]

    assert [4, 1, 0] == [i.node for i in unfolded]


def test_rpl_block_scope_walker_iterates_over_scopes(program_tree):
    node = program_tree.children[0].children[1].children[1]
    unfolded = [i for i in RPLBlockScopeWalker(node)]

    assert [6, 7, 3, 4, 1, 0] == [i.node for i in unfolded]


def test_rpl_block_scope_walker_with_reverse_flag_iterates_over_scope_reversed(
    program_tree,
):
    node = program_tree.children[0].children[1].children[1]
    unfolded = [i for i in RPLBlockScopeWalker(node, reverse=True)]

    assert [7, 6, 4, 3, 1, 0] == [i.node for i in unfolded]


def test_adding_child_updates_parent_and_level_of_child():
    first_block = RPLBlock(None, None, program=object())
    second_block = RPLBlock(None, None, program=object())

    first_block.add_child(second_block)

    assert second_block.level == 1
    assert second_block.parent == first_block


def test_marking_child_as_modified_marks_parent_as_needing_rewrite(
    program_tree,
):
    program_tree.children[0]._modified = True

    assert program_tree._needs_rewrite() is True


def test_marking_parent_as_modified_marks_child_as_needing_rewrite(
    program_tree,
):
    program_tree._modified = True

    assert program_tree.children[0]._needs_rewrite() is True


def test_disabling_parent_block_disables_child_block(program_tree):
    program_tree.disabled = True

    assert program_tree.children[1].disabled is True


def test_adding_child_marks_block_as_modified():
    first_block = RPLBlock(None, None, program=object())
    second_block = RPLBlock(None, first_block)

    first_block.add_child(second_block)

    assert first_block.modified is True


def test_inserting_child_updates_parent_and_level_of_child():
    first_block = RPLBlock(None, None, program=object())
    second_block = RPLBlock(None, first_block)
    third_block = RPLBlock(None, None, program=object())

    first_block.add_child(second_block)
    first_block.insert_child(third_block, second_block)

    assert third_block.level == 1
    assert third_block.parent == first_block


def test_inserting_child_marks_blocks_as_modified():
    first_block = RPLBlock(None, None, program=object())
    second_block = RPLBlock(None, first_block)
    third_block = RPLBlock(None, None, program=object())

    first_block.add_child(second_block, modify=False)
    first_block.insert_child(third_block, second_block)

    assert first_block.modified
    assert third_block.modified


def test_inserting_child_without_before_false_inserts_block_before_block():
    first_block = RPLBlock(None, None, program=object())
    second_block = RPLBlock(None, first_block)
    third_block = RPLBlock(None, None, program=object())

    first_block.add_child(second_block, modify=False)
    first_block.insert_child(third_block, second_block)

    assert first_block.children[0] is third_block


def test_inserting_child_with_before_false_inserts_block_after_other_block():
    first_block = RPLBlock(None, None, program=object())
    second_block = RPLBlock(None, first_block)
    third_block = RPLBlock(None, None, program=object())

    first_block.add_child(second_block, modify=False)
    first_block.insert_child(third_block, second_block, before=False)

    assert first_block.children[1] is third_block


@pytest.mark.dependency()
def test_adding_block_to_group_adds_block_and_set_group_main():
    first_block = RPLBlock(None, None, program=object())
    second_block = RPLBlock(None, None, program=object())

    first_block.add_to_group(second_block)

    assert second_block in first_block.group_links
    assert second_block.group_target is first_block


@pytest.mark.dependency(
    depends=['test_adding_block_to_group_adds_block_and_set_group_main']
)
def test_removing_block_from_group_removes_block_and_unsets_group_main():
    first_block = RPLBlock(None, None, program=object())
    second_block = RPLBlock(None, None, program=object())
    first_block.add_to_group(second_block)

    first_block.remove_from_group(second_block)

    assert second_block not in first_block.group_links
    assert second_block.group_target is None


@pytest.mark.dependency(
    depends=['test_adding_block_to_group_adds_block_and_set_group_main']
)
def test_inserting_block_into_same_group_changes_link_order():
    first_block = RPLBlock(None, None, program=object())
    second_block = RPLBlock(None, None, program=object())
    third_block = RPLBlock(None, None, program=object())
    first_block.add_to_group(second_block)
    first_block.add_to_group(third_block)

    first_block.insert_into_group(third_block, second_block, before=True)

    assert len(first_block.group_links) == 2
    assert first_block.group_links[0] is third_block
    assert first_block.group_links[1] is second_block


def test_copy_creates_copy_of_block_preserving_children_and_program():
    program = object()
    first_block = RPLBlock(None, None, program=program)
    second_block = RPLBlock(None, first_block)
    first_block.add_child(second_block)
    third_block = RPLBlock(None, first_block)
    first_block.add_child(third_block)

    new_block = first_block.copy()

    assert len(new_block.children) == 2
    assert new_block.program is program
    assert new_block.children[0] is not second_block
    assert new_block.children[0].program is program
    assert new_block.children[1] is not third_block
    assert new_block.children[1].program is program
