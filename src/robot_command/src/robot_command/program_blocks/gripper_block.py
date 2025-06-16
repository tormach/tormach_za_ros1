from robot_command.program_blocks.parse_helpers import (
    FunctionParser,
    Argument,
)
from .rpl_block import RPLBlock, mark_modified


class GripperBlock(RPLBlock):
    type = 'actuate_gripper'

    DEFAULT_POSITION = 0.0
    DEFAULT_EFFORT = 0.2
    DEFAULT_WAIT = True

    def __init__(
        self,
        node,
        parent,
        position=DEFAULT_POSITION,
        effort=DEFAULT_EFFORT,
        wait=DEFAULT_WAIT,
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)

        self._position = position
        self._effort = effort
        self._wait = wait

    @property
    def position(self):
        return self._position

    @position.setter
    @mark_modified()
    def position(self, value):
        self._position = value

    @property
    def effort(self):
        return self._effort

    @effort.setter
    @mark_modified()
    def effort(self, value):
        self._effort = value

    @property
    def wait(self):
        return self._wait

    @wait.setter
    @mark_modified()
    def wait(self, value):
        self._wait = value

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt' or not node.children:
            return

        parser = FunctionParser(
            name='actuate_gripper',
            args=[
                Argument(name='position', type=float),
                Argument(name='effort', type=float, optional=True),
                Argument(name='wait', type=bool, optional=True),
            ],
        )
        success, args = parser.parse(node.children[0])
        if not success:
            return

        yield GripperBlock(
            node,
            parent,
            position=args.get('position'),
            effort=args.get('effort', GripperBlock.DEFAULT_EFFORT),
            wait=args.get('wait', GripperBlock.DEFAULT_WAIT),
        )

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
        else:
            args = [f'{self._position}']
            if self._effort != self.DEFAULT_EFFORT:
                args.append(f'effort={self._effort}')
            if self._wait is not self.DEFAULT_WAIT:
                args.append(f'wait={self._wait}')
            yield f'{self._get_indent()}{self.type}({", ".join(args)})\n'
