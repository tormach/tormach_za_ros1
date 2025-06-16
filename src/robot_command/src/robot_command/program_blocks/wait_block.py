from enum import IntEnum
from parso.python import tree

from robot_command.program_blocks.parse_helpers import (
    FunctionParser,
    Argument,
    ParseException,
    convert_string,
    prepare_string,
)
from .rpl_block import RPLBlock, mark_modified


class WaitType(IntEnum):
    Sleep = 0
    WaitForDigitalIn = 1
    WaitForCondition = 2
    Pause = 3
    Exit = 4


class WaitBlock(RPLBlock):
    type = 'wait'

    def __init__(
        self,
        node,
        parent,
        wait_type=WaitType.Sleep,
        sleep_time=0.01,
        digital_in_nr=0,
        digital_in_name='',
        digital_in_state=False,
        optional=False,
        active=False,
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)

        self._wait_type = wait_type
        self._sleep_time = sleep_time
        self._digital_in_nr = digital_in_nr
        self._digital_in_name = digital_in_name
        self._digital_in_state = digital_in_state
        self._optional = optional
        self._active = active

    @property
    def wait_type(self):
        return self._wait_type

    @wait_type.setter
    @mark_modified()
    def wait_type(self, value):
        self._wait_type = value

    @property
    def sleep_time(self):
        return self._sleep_time

    @sleep_time.setter
    @mark_modified()
    def sleep_time(self, value):
        self._sleep_time = value

    @property
    def digital_in_nr(self):
        return self._digital_in_nr

    @digital_in_nr.setter
    @mark_modified()
    def digital_in_nr(self, value):
        self._digital_in_nr = value

    @property
    def digital_in_name(self):
        return self._digital_in_name

    @digital_in_name.setter
    @mark_modified()
    def digital_in_name(self, value):
        self._digital_in_name = value

    @property
    def digital_in_state(self):
        return self._digital_in_state

    @digital_in_state.setter
    @mark_modified()
    def digital_in_state(self, value):
        self._digital_in_state = value

    @property
    def optional(self):
        return self._optional

    @optional.setter
    @mark_modified()
    def optional(self, value):
        self._optional = value

    @property
    def active(self):
        return self._active

    @active.setter
    @mark_modified()
    def active(self, value):
        self._active = value

    @staticmethod
    def read(node, parent):
        if node.type == 'simple_stmt':
            n = WaitBlock._detect_sleep_block(node, parent)
            if n:
                yield n
                return
            n = WaitBlock._detect_pause_block(node, parent)
            if n:
                yield n
                return
            n = WaitBlock._detect_exit_block(node, parent)
            if n:
                yield n
                return
        elif node.type == 'while_stmt':
            n = WaitBlock._detect_digital_in_block(node, parent)
            if n:
                yield n

    @staticmethod
    def _detect_sleep_block(node, parent):
        parser = FunctionParser(
            name='sleep', args=[Argument(name='secs', type=float)]
        )
        success, args = parser.parse(node.children[0])
        if not success:
            return None

        return WaitBlock(
            node, parent, wait_type=WaitType.Sleep, sleep_time=args.get('secs')
        )

    @staticmethod
    def _detect_pause_block(node, parent):
        parser = FunctionParser(
            name='pause',
            args=[
                Argument(name='optional', type=bool, optional=True),
                Argument(name='active', type=bool, optional=True),
            ],
        )
        success, args = parser.parse(node.children[0])
        if not success:
            return None

        return WaitBlock(
            node,
            parent,
            wait_type=WaitType.Pause,
            optional=args.get('optional', False),
            active=args.get('active', False),
        )

    @staticmethod
    def _detect_exit_block(node, parent):
        parser = FunctionParser(name='exit')
        success, args = parser.parse(node.children[0])
        if not success:
            return None

        return WaitBlock(node, parent, wait_type=WaitType.Exit)

    @staticmethod
    def _detect_digital_in_block(node, parent):
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

        keyword_is = condition.children[1]
        if not isinstance(keyword_is, tree.Keyword) or keyword_is.value != 'is':
            return None

        name_bool = condition.children[2]
        if not isinstance(
            name_bool, (tree.Name, tree.Keyword)
        ) or name_bool.value not in (
            'True',
            'False',
        ):
            return None
        state = name_bool.value != 'True'

        parser = FunctionParser(
            name='get_digital_in',
            args=[
                Argument(
                    name='nr_or_name',
                    parsefunct=WaitBlock._parse_number_or_string,
                )
            ],
        )
        success, args = parser.parse(condition.children[0])
        if not success:
            return None
        nr, name = args.get('nr_or_name')

        return WaitBlock(
            node,
            parent,
            wait_type=WaitType.WaitForDigitalIn,
            digital_in_state=state,
            digital_in_nr=nr,
            digital_in_name=name,
        )

    @staticmethod
    def _parse_number_or_string(node, _type):
        if node.type == 'number':
            nr = int(node.value)
            name = ''
        elif node.type == 'string':
            name, _ = convert_string(node.value)
            nr = 0
        else:
            raise ParseException('Passed wrong type.')

        return nr, name

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
        elif self._wait_type == WaitType.Sleep:
            yield '{indent}sleep({time})\n'.format(
                indent=self._get_indent(), time=self._sleep_time
            )
        elif self._wait_type == WaitType.Pause:
            args = []
            if self._optional:
                args.append('optional=True')
            if self._active:
                args.append('active=True')
            yield '{indent}pause({args})\n'.format(
                indent=self._get_indent(), args=', '.join(args)
            )
        elif self._wait_type == WaitType.WaitForDigitalIn:
            if self._digital_in_name:
                nr_or_name = prepare_string(self._digital_in_name)
            else:
                nr_or_name = self._digital_in_nr
            yield (
                '{indent}while get_digital_in({nr_or_name}) is {state}:\n'
                '{next_indent}sync()\n'
            ).format(
                nr_or_name=nr_or_name,
                state=not self._digital_in_state,
                indent=self._get_indent(),
                next_indent=self._get_next_indent(),
            )
        else:
            yield f'{self._get_indent()}exit()\n'
