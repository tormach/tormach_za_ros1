from enum import IntEnum
from parso.python import tree

from robot_command.program_blocks.parse_helpers import (
    FunctionParser,
    Argument,
    ParseException,
)
from .rpl_block import RPLBlock, mark_modified


class FrameType(IntEnum):
    ScopedUserFrame = 0
    ChangeUserFrame = 1
    ChangeToolFrame = 2


class FrameBlock(RPLBlock):
    type = 'frame'

    def __init__(
        self,
        node,
        parent,
        frame_type=FrameType.ChangeUserFrame,
        name='',
        pose='',
        position='',
        orientation='',
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)

        self._frame_type = frame_type
        self._name = name
        self._pose = pose
        self._position = position
        self._orientation = orientation

    @property
    def frame_type(self):
        return self._frame_type

    @frame_type.setter
    @mark_modified()
    def frame_type(self, value):
        self._frame_type = value

    @property
    def name(self):
        return self._name

    @name.setter
    @mark_modified()
    def name(self, value):
        self._name = value

    @property
    def pose(self):
        return self._pose

    @pose.setter
    @mark_modified()
    def pose(self, value):
        self._pose = value

    @property
    def position(self):
        return self._position

    @position.setter
    @mark_modified()
    def position(self, value):
        self._position = value

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    @mark_modified()
    def orientation(self, value):
        self._orientation = value

    @staticmethod
    def read(node, parent):
        if isinstance(node, tree.WithStmt):
            stmt = node.children[1]
            suite = node.children[3]
            yield from FrameBlock._read_with(node, parent, suite, stmt)
        elif node.type == 'simple_stmt' and node.children:
            yield from FrameBlock._read_simple(node, parent, node.children[0])

    @staticmethod
    def _read_with(node, parent, suite, stmt):
        parser = FunctionParser(
            name='user_frame',
            args=[
                Argument(
                    name='pose',
                    parsefunct=FrameBlock._parse_pose,
                    optional=True,
                ),
                Argument(
                    name='position',
                    parsefunct=FrameBlock._parse_pose,
                    optional=True,
                ),
                Argument(
                    name='orientation',
                    parsefunct=FrameBlock._parse_pose,
                    optional=True,
                ),
            ],
        )
        success, args = parser.parse(stmt)
        if not success or len(args) == 0:
            return

        block = FrameBlock(
            node,
            parent,
            frame_type=FrameType.ScopedUserFrame,
            pose=args.get('pose', ''),
            position=args.get('position', ''),
            orientation=args.get('orientation', ''),
        )
        for node_child in suite.children:
            for child in block.program.read_block(node_child, block):
                block.add_child(child, modify=False)
        yield block

    @staticmethod
    def _read_simple(node, parent, stmt):
        parser = FunctionParser(
            name='change_user_frame', args=[Argument(name='name', type=str)]
        )
        frame_type = FrameType.ChangeUserFrame
        success, args = parser.parse(stmt)

        if not success:
            parser = FunctionParser(
                name='change_tool_frame',
                args=[Argument(name='name', type=str)],
            )
            success, args = parser.parse(stmt)
            frame_type = FrameType.ChangeToolFrame

        if not success:
            return

        name = args.get('name')
        yield FrameBlock(node, parent, frame_type=frame_type, name=name)

    @staticmethod
    def _parse_pose(node, _target_type):
        if isinstance(node, (tree.Name, tree.String)):
            return node.value
        else:
            raise ParseException('Could not read pose.')

    def write(self):
        yield from self._write_disabled()

        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
            return

        if self._frame_type == FrameType.ScopedUserFrame:
            args = []
            if self._pose:
                args.append(self.pose)
            if self._position:
                args.append(f'position={self._position}')
            if self._orientation:
                args.append(f'orientation={self._orientation}')
            yield '{}with user_frame({args}):\n'.format(
                self._get_indent(), args=', '.join(args)
            )
            for child in self.children:
                yield from child.write()
        elif self._frame_type == FrameType.ChangeUserFrame:
            yield '{indent}change_user_frame("{name}")\n'.format(
                indent=self._get_indent(), name=self._name
            )
        else:
            yield '{indent}change_tool_frame("{name}")\n'.format(
                indent=self._get_indent(), name=self._name
            )
