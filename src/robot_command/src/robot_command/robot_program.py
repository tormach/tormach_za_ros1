import copy
import os
import random
from typing import Optional, List, Union
from uuid import UUID, uuid4

import parso

from .waypoint import Waypoint
from .waypoints import Waypoints
from .program_blocks import (
    RPLBlockWalker,
    RPLBlockRootWalker,
    RootBlock,
    WaypointBlock,
    registered_blocks,
    UnitsBlock,
    RPLImportBlock,
    RPLBlock,
)


class RobotProgram(Waypoints):
    """Stores, reads, modifies and writes a robot program."""

    def __init__(
        self,
        root_block=None,
        waypoints=None,
        name='',
        inspector_blocks=registered_blocks,
    ):
        super().__init__(waypoints)
        self._path = ''
        self._root_block = root_block
        self._name = name
        self._units_block = UnitsBlock(None, self._root_block, program=self)
        self._rpl_import_block = RPLImportBlock(
            None, self._root_block, program=self
        )
        self._uuid_block_map = {}

        self._inspector_blocks = inspector_blocks
        self._block_type_map = {block.type: block for block in inspector_blocks}

        self.linear_unit_decimals = 4
        self.angular_unit_decimals = 3

        self._update_uuid_block_map()

    @property
    def root_block(self):
        return self._root_block

    @property
    def blocks(self):
        return RPLBlockWalker(self._root_block)

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def linear_unit(self):
        return self._units_block.linear_unit

    @property
    def angular_unit(self):
        return self._units_block.angular_unit

    @property
    def time_unit(self):
        return self._units_block.time_unit

    @property
    def header_auto_updated(self):
        return self._units_block.node is None or self._rpl_import_block.modified

    def reset_data(
        self,
        root_block: Union[RPLBlock, object, None] = object,
        waypoints: Optional[List[Waypoint]] = None,
        name: Optional[str] = None,
        path: Optional[str] = None,
        linear_unit: Optional[str] = None,
        angular_unit: Optional[str] = None,
        time_unit: Optional[str] = None,
        units_block: Optional[UnitsBlock] = None,
        rpl_import_block: Optional[RPLImportBlock] = None,
    ):
        if root_block is not object:
            self._root_block = root_block
            self._update_uuid_block_map()
        if waypoints is not None:
            self._waypoints = waypoints
            self._update_uuid_waypoint_map()
        if name is not None:
            self._name = name
        if path is not None:
            self._path = path
        if (
            linear_unit is not None
            and self._units_block.linear_unit != linear_unit
        ):
            self._units_block.linear_unit = linear_unit
        if (
            angular_unit is not None
            and self._units_block.angular_unit != angular_unit
        ):
            self._units_block.angular_unit = angular_unit
        if time_unit is not None and self._units_block.time_unit != time_unit:
            self._units_block.time_unit = time_unit
        if units_block is not None:
            self._units_block = units_block
        if rpl_import_block is not None:
            self._rpl_import_block = rpl_import_block

    def clear(self):
        self.reset_data(
            root_block=None,
            waypoints=[],
            name='',
            path='',
            units_block=UnitsBlock(None, None, program=self),
            rpl_import_block=RPLImportBlock(None, None, program=self),
        )

    def copy_data_to(self, target):
        if not isinstance(target, RobotProgram):
            raise TypeError('Can only copy data to other robot program.')

        new_blocks = copy.deepcopy(self._root_block)
        for block in RPLBlockWalker(new_blocks):
            block.program = target

        new_waypoints = copy.deepcopy(self.waypoints)

        target.reset_data(
            root_block=new_blocks,
            waypoints=new_waypoints,
            name=self._name,
            path=self._path,
            units_block=self._units_block,
            rpl_import_block=self._rpl_import_block,
        )

    def get_block(self, uuid):
        return self._uuid_block_map.get(uuid, None)

    def read_from_file(self, path):
        """Reads the robot program from a file."""
        self._path = os.path.abspath(path)
        with open(self._path) as f:
            source_code = f.read()
        if not source_code.endswith('\n'):
            source_code += '\n'
        self._name, _ = os.path.splitext(os.path.basename(self._path))
        module = parso.parse(source_code)

        num_functs = sum(
            (node.type == 'funcdef' and node.name.value == 'main')
            for node in module.children
        )
        if num_functs == 0:
            raise RuntimeError('Could not find main function in program')

        root_block = RootBlock(module, self)
        root_block.read_program()
        waypoints = self._extract_waypoints(root_block)
        units_block = self._extract_units(root_block)
        rpl_import_block = self._extract_rpl_import(root_block)
        self.reset_data(
            root_block=root_block,
            waypoints=waypoints,
            units_block=units_block,
            rpl_import_block=rpl_import_block,
        )

    def generate_code(self):
        """Generates and yields the program code line by line."""
        child_backup = copy.copy(self._root_block.children)
        self._insert_waypoints(self._root_block, self._waypoints)
        if self.angular_unit or self.linear_unit or self.time_unit:
            self._insert_units(self._root_block, self._units_block)
        self._insert_rpl_import(self._root_block, self._rpl_import_block)
        yield from self._root_block.write()
        self._root_block.children = child_backup  # restore stripped root block

    def write_to_file(self, path):
        """Writes the robot program to a file."""
        with open(path, 'w') as f:
            for line in self.generate_code():
                f.write(line)

    def read_block(self, node, parent):
        """Reads in a new block."""
        yielded = False
        for inspector_block in self._inspector_blocks:
            for new_block in inspector_block.read(node, parent):
                yield new_block
                yielded = True
            if yielded:
                return

    def _get_last_block(self):
        main_block = None
        for block in self.root_block.children:
            if block.type == 'mainprogram':
                main_block = block

        if not main_block or len(main_block.children) == 0:
            return None

        return main_block.children[-1]

    def create_block(self, target_block, type_, uuid=None, before=True):
        """
        Creates and inserts a new block into the program tree.
        :type target_block: Optional[RPLBlock]
        """
        if not target_block:
            target_block = self._get_last_block()
            before = False
        else:
            self._verify_block_exists(target_block)

        if target_block.in_group:
            target_block = (
                target_block.group_head if before else target_block.group_tail
            )

        if (
            target_block.type != 'pass'
            or len(target_block.parent.children) != 1
        ):
            return self._create_block(target_block, type_, uuid, before)

        parent = target_block.parent
        self._remove_block(target_block)
        return self._create_child_block(parent, type_, uuid)

    def _create_block(self, target_block, type_, uuid, before):
        parent = target_block.parent
        new_block = self._block_type_map[type_](
            node=None, parent=parent, uuid=uuid
        )
        parent.insert_child(new_block, target_block, before=before)
        self._uuid_block_map[new_block.uuid] = new_block

        return new_block

    def create_child_block(self, parent_block, type_, uuid=None):
        """
        Creates and inserts a new block into the program as a child of another
        block.
        :type parent_block: RPLBlock
        """
        self._verify_block_exists(parent_block)

        return self._create_child_block(parent_block, type_, uuid)

    def _create_child_block(self, parent_block, type_, uuid):
        new_block = self._block_type_map[type_](
            node=None, parent=parent_block, uuid=uuid
        )
        parent_block.add_child(new_block)
        self._uuid_block_map[new_block.uuid] = new_block

        return new_block

    def copy_block(self, block, target_block, uuid=None, before=True):
        """
        Copies a block before another block.
        :type block: RPLBlock
        :type target_block: RPLBlock
        """
        self._verify_block_exists(block)
        self._verify_block_exists(target_block)

        # group copying logic
        if block.in_group:
            head = block.group_head
            new_block = None
            if target_block.in_group:  # target is also in group
                if target_block.group_head is head:  # target is in same group
                    if target_block is head and before:
                        return None  # can't copy before the group head
                    elif block.group_fixed:
                        return None  # can't copy a fixed block
                    else:
                        new_block = self._copy_block(
                            block, target_block, uuid, before
                        )
                        target_block.group_head.insert_into_group(
                            new_block, target_block, before
                        )
                else:  # target is in other group
                    if before:
                        target_block = (
                            target_block.group_head
                        )  # copy before group
                    else:
                        target_block = (
                            target_block.group_tail
                        )  # copy after group

            if not new_block:  # block wasn't already copied into other group
                new_block = self._copy_block(head, target_block, uuid, before)
                uuid_ = new_block.uuid
                last_block = new_block
                for (
                    block_
                ) in head.group_links:  # recursively copy other group blocks
                    uuid_ = self._generate_new_reproducible_uuid(
                        new_block.parent.uuid, uuid_
                    )
                    last_block = self._copy_block(
                        block_,
                        target_block if before else last_block,
                        uuid_,
                        before,
                    )
                    new_block.add_to_group(last_block)
        else:
            if target_block.in_group:  # source not in group, target in group
                if before:
                    target_block = target_block.group_head  # copy before group
                else:
                    target_block = target_block.group_tail  # copy after group
            new_block = self._copy_block(block, target_block, uuid, before)

        if target_block.type == 'pass':
            self._remove_block(target_block)

        return new_block

    def _copy_block(self, block, target_block, uuid, before):
        new_block = block.copy()
        new_block.group_links = []
        new_block.group_target = None

        # first uuid needs to be new every time
        if uuid:
            new_block.uuid = uuid
        else:
            new_block.uuid = str(uuid4())

        # the rest of the uuids is based on the first one
        def update_uuid(block_):
            for child_block_ in block_.children:
                update_uuid(child_block_)
            block_.uuid = self._generate_new_reproducible_uuid(
                block_.parent.uuid, block_.uuid
            )
            self._uuid_block_map[block_.uuid] = block_

        for child_block in new_block.children:
            update_uuid(child_block)

        parent = target_block.parent
        parent.insert_child(new_block, target_block, before=before)
        self._uuid_block_map[new_block.uuid] = new_block

        return new_block

    def create_group_block(self, group_block, type_, append=False, uuid=None):
        """
        Creates and adds a new block and existing group or creates a new group.
        Per default, the new block is added before the group_block, except the
        specified group_block is the head of the group, then the new block is added
        after the head.

        :param append: If true the new block is appended to the end of the group.
        :type group_block: RPLBlock
        """
        self._verify_block_exists(group_block)

        if not group_block.in_group or group_block.group_head is group_block:
            force_append = True
        else:
            force_append = False

        if not (append or force_append):
            new_block = self._create_block(
                group_block, type_, uuid, before=True
            )
            group_block.group_head.add_to_group(new_block)
            return new_block

        if (
            group_block.group_head is group_block
            and not append
            or not group_block.in_group
        ):
            after_block = group_block
        else:
            links = group_block.group_head.group_links
            after_block = sorted(
                links, key=lambda n: n.parent.children.index(n)
            )[-1]
        block_is_last = after_block.parent.children[-1] is after_block

        if block_is_last:
            new_block = self._create_child_block(
                after_block.parent, type_, uuid
            )
        else:
            index = after_block.parent.children.index(after_block)
            before_block = after_block.parent.children[index + 1]
            new_block = self._create_block(
                before_block, type_, uuid, before=True
            )

        if not group_block.in_group:
            group_block.add_to_group(new_block)
        else:
            group_block.group_head.add_to_group(new_block)

        return new_block

    def remove_block(self, block):
        """
        Removes a block from the program tree.
        :type block: RPLBlock
        """
        self._verify_block_exists(block)

        blocks = {block}
        if block.in_group:
            head = block.group_head
            if head is block:
                blocks.add(head)
                blocks = blocks.union(head.group_links)
            else:
                head.remove_from_group(block)

        for block_ in blocks:
            self._remove_block(block_)

        if block.parent and len(block.parent.children) == 0:
            new_uuid = self._generate_new_reproducible_uuid(
                block.parent.uuid, block.uuid
            )
            self._create_child_block(block.parent, 'pass', uuid=new_uuid)

    def _remove_block(self, block):
        parent = block.parent
        parent.remove_child(block)
        for uuid in (block.uuid for block in RPLBlockWalker(block)):
            self._uuid_block_map.pop(uuid)

    def update_block(self, block, property_, value):
        """
        Updates a property of a block with a new value.
        :type block: RPLBlock
        """
        self._verify_block_exists(block)

        if block.in_group and property_ == 'disabled':
            for block_ in block.group_head.group_links + [block.group_head]:
                self._update_block(block_, property_, value)
        else:
            self._update_block(block, property_, value)

    def _update_block(self, block, property_, value):
        if not hasattr(block, property_):
            raise AttributeError(f'Block has no property named {property_}')
        try:
            setattr(block, property_, value)
        except AttributeError:
            raise AttributeError(f'Setting block attribute {property_} failed')

    def move_block(self, block, target_block, before=True):
        """
        Moves a block to a new position before another block.
        :type target_block: RPLBlock
        :type block: RPLBlock
        :type before: bool
        :returns: True of movement was executed.
        """
        self._verify_block_exists(block)
        self._verify_block_exists(target_block)

        def block_target_is_same(target_n):
            if block == target_n:
                return True
            if block.parent == target_n.parent:
                source_index = block.parent.children.index(block)
                target_index = block.parent.children.index(target_n)
                if before and (target_index - 1 == source_index):
                    return True
                elif not before and (target_index + 1 == source_index):
                    return True
                else:
                    return False

        # prevent no-op moves
        if block_target_is_same(target_block):
            return False
        # prevent moving to own ancestor
        if block in RPLBlockRootWalker(target_block):
            return False

        if block.parent and len(block.parent.children) == 1:
            new_uuid = self._generate_new_reproducible_uuid(
                block.parent.uuid, block.uuid
            )
            self._create_block(block, 'pass', uuid=new_uuid, before=True)

        # group moving logic
        if block.in_group:
            head = block.group_head
            done = False
            if target_block.in_group:
                if target_block.group_fixed and not before:
                    return False  # don't move after fixed
                if head is block:
                    return False  # don't move the head
                if target_block.group_head is head:  # target in same group
                    if target_block is head and before:
                        return False  # don't move before head
                    elif block.group_fixed:
                        return False  # don't move fixed
                    else:
                        self._move_block(block, target_block, before)
                        target_block.group_head.insert_into_group(
                            block, target_block, before
                        )
                        done = True
                else:
                    target_block = (
                        target_block.group_head
                        if before
                        else target_block.group_tail
                    )

            if not done:
                self._move_block(head, target_block, before)
                last_block = head
                for block_ in head.group_links:
                    self._move_block(
                        block_, target_block if before else last_block, before
                    )
                    last_block = block_
        else:
            if target_block.in_group:
                target_block = (
                    target_block.group_head
                    if before
                    else target_block.group_tail
                )
            if block_target_is_same(target_block):
                return False
            self._move_block(block, target_block, before)

        if target_block.type == 'pass':
            self._remove_block(target_block)

        return True

    def _move_block(self, block, target_block, before):
        current_parent = block.parent
        new_parent = target_block.parent

        current_parent.take_child(block)
        new_parent.insert_child(block, target_block, before=before)

    def _verify_block_exists(self, block):
        if block.uuid not in self._uuid_block_map:
            raise KeyError('Block is not part of this program')

    def _update_uuid_block_map(self):
        if self._root_block is None:
            self._uuid_block_map = {}
        else:
            self._uuid_block_map = {block.uuid: block for block in self.blocks}

    @staticmethod
    def _extract_units(root_block):
        """Find, takes and returns UnitsBlocks from the top level."""
        for block in list(root_block.children):
            if isinstance(block, UnitsBlock):
                root_block.remove_child(block, modify=False)
                return block
        return UnitsBlock(None, root_block, modified=True)

    @staticmethod
    def _extract_rpl_import(root_block):
        """Extracts the RPL import block from the top level."""
        for block in list(root_block.children):
            if not isinstance(block, RPLImportBlock):
                continue
            root_block.remove_child(block, modify=False)
            return block
        return RPLImportBlock(None, root_block, modified=True)

    @staticmethod
    def _extract_waypoints(root_block):
        """
        Finds, takes and returns all WaypointBlocks from the top level.
        """
        waypoints = []
        for block in list(root_block.children):
            if not isinstance(block, WaypointBlock):
                continue
            waypoints.append(Waypoint.from_waypoint_block(block))
            root_block.remove_child(block, modify=False)
        return waypoints

    @staticmethod
    def _insert_waypoints(root_block, waypoints):
        waypoint_blocks = [
            waypoint.to_waypoint_block(root_block) for waypoint in waypoints
        ]
        root_block.children = waypoint_blocks + root_block.children

    @staticmethod
    def _insert_units(root_block, units_block):
        root_block.children.insert(0, units_block)
        units_block.parent = root_block

    @staticmethod
    def _insert_rpl_import(root_block, rpl_import_block):
        root_block.children.insert(0, rpl_import_block)
        rpl_import_block.parent = root_block

    def __str__(self):
        lines = ['RobotProgram (']
        for block in self.blocks:
            lines.append('  {}{}'.format('-' * block.level, str(block)))
        lines.append(')')
        return '\n'.join(lines)

    @staticmethod
    def _generate_new_reproducible_uuid(uuid1, uuid2):
        rd = random.Random()
        rd.seed(a=(uuid1, uuid2))
        return str(UUID(int=rd.getrandbits(128)))
