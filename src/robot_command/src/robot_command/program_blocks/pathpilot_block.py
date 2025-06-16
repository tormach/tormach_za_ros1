from enum import IntEnum
from parso.python import tree

from robot_command.program_blocks.parse_helpers import (
    Argument,
    FunctionParser,
    convert_string,
)
from .rpl_block import RPLBlock, mark_modified

PATHPILOT_STATES = ('disconnected', 'estop', 'running', 'ready', 'idle')


class CommandType(IntEnum):
    MdiCommand = 0
    CycleStartCommand = 1
    WaitForState = 2
    AbortCommand = 3


class PathPilotBlock(RPLBlock):
    type = 'pathpilot'

    def __init__(
        self,
        node,
        parent,
        command_type=CommandType.MdiCommand,
        command_line='',
        instance='',
        state='',
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)

        self._command_type = command_type
        self._command_line = command_line
        self._instance = instance
        self._state = state

    @property
    def command_type(self):
        return self._command_type

    @command_type.setter
    @mark_modified()
    def command_type(self, value):
        self._command_type = value

    @property
    def command_line(self):
        return self._command_line

    @command_line.setter
    @mark_modified()
    def command_line(self, value):
        self._command_line = value

    @property
    def instance(self):
        return self._instance

    @instance.setter
    @mark_modified()
    def instance(self, value):
        self._instance = value

    @property
    def state(self):
        return self._state

    @state.setter
    @mark_modified()
    def state(self, value):
        self._state = value

    @staticmethod
    def read(node, parent):
        if node.type == 'simple_stmt':
            n = PathPilotBlock._detect_mdi_block(node, parent)
            if n:
                yield n
                return
            n = PathPilotBlock._detect_cycle_start_block(node, parent)
            if n:
                yield n
                return
            n = PathPilotBlock._detect_abort_block(node, parent)
            if n:
                yield n
                return
        elif node.type == 'while_stmt':
            n = PathPilotBlock._detect_wait_for_state_block(node, parent)
            if n:
                yield n
                return

    @staticmethod
    def _detect_mdi_block(node, parent):
        parser = FunctionParser(
            name='pathpilot_mdi',
            args=[
                Argument(name='command', type=str),
                Argument(name='instance', type=str, optional=True),
            ],
        )
        success, args = parser.parse(node.children[0])

        if success:
            return PathPilotBlock(
                node,
                parent,
                command_type=CommandType.MdiCommand,
                command_line=args.get('command'),
                instance=args.get('instance', ''),
            )

    @staticmethod
    def _detect_cycle_start_block(node, parent):
        parser = FunctionParser(
            name='pathpilot_cycle_start',
            args=[Argument(name='instance', type=str, optional=True)],
        )
        success, args = parser.parse(node.children[0])

        if success:
            return PathPilotBlock(
                node,
                parent,
                command_type=CommandType.CycleStartCommand,
                instance=args.get('instance', ''),
            )

    @staticmethod
    def _detect_abort_block(node, parent):
        parser = FunctionParser(
            name='pathpilot_abort',
            args=[Argument(name='instance', type=str, optional=True)],
        )
        success, args = parser.parse(node.children[0])

        if success:
            return PathPilotBlock(
                node,
                parent,
                command_type=CommandType.AbortCommand,
                instance=args.get('instance', ''),
            )

    @staticmethod
    def _detect_wait_for_state_block(node, parent):
        condition = node.children[1]
        body_suite = node.children[3]

        if len(body_suite.children) != 2:  # sync + newline
            return None

        body_stmt = body_suite.children[1]
        if body_stmt.type != 'simple_stmt' or not body_stmt.children:
            return None
        parser = FunctionParser(name='sync')
        success, _ = parser.parse(body_stmt.children[0])
        if not success:
            return None

        if not (
            condition.type == 'comparison' and len(condition.children) == 3
        ):
            return None

        comparison_operator = condition.children[1]
        if (
            not isinstance(comparison_operator, tree.Operator)
            or comparison_operator.value != '!='
        ):
            return None

        state_str = condition.children[2]
        if not isinstance(state_str, tree.String):
            return None
        state, _ = convert_string(state_str.value)
        if state not in PATHPILOT_STATES:
            return None

        parser = FunctionParser(
            name='get_pathpilot_state',
            args=[Argument(name='instance', type=str, optional=True)],
        )
        success, args = parser.parse(condition.children[0])
        if not success:
            return None
        instance = args.get('instance', '')

        return PathPilotBlock(
            node,
            parent,
            command_type=CommandType.WaitForState,
            state=state,
            instance=instance,
        )

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
            return

        args = []
        if self.instance:
            args.append(f'instance="{self._instance}"')

        if self._command_type == CommandType.MdiCommand:
            args.insert(0, f'"{self._command_line}"')
            yield '{indent}pathpilot_mdi({args})\n'.format(
                indent=self._get_indent(), args=', '.join(args)
            )
        elif self._command_type == CommandType.CycleStartCommand:
            yield '{indent}pathpilot_cycle_start({args})\n'.format(
                indent=self._get_indent(), args=', '.join(args)
            )
        elif self._command_type == CommandType.AbortCommand:
            yield '{indent}pathpilot_abort({args})\n'.format(
                indent=self._get_indent(), args=', '.join(args)
            )
        elif self._command_type == CommandType.WaitForState:
            yield (
                '{indent}while get_pathpilot_state({args}) != "{state}":\n'
                '{next_indent}sync()\n'
            ).format(
                args=', '.join(args),
                state=self._state,
                indent=self._get_indent(),
                next_indent=self._get_next_indent(),
            )
