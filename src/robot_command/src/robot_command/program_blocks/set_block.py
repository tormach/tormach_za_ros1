from enum import IntEnum
from robot_command.program_blocks.parse_helpers import (
    Argument,
    FunctionParser,
    convert_string,
    ParseException,
    prepare_string,
)
from .rpl_block import RPLBlock, mark_modified


class SetType(IntEnum):
    SetDigitalOut = 0
    SetVariable = 1


class SetBlock(RPLBlock):
    type = 'set'

    def __init__(
        self,
        node,
        parent,
        set_type=SetType.SetDigitalOut,
        digital_out_nr=0,
        digital_out_name='',
        digital_out_state=False,
        **kwargs
    ):
        super().__init__(node, parent, **kwargs)

        self._set_type = set_type
        self._digital_out_nr = digital_out_nr
        self._digital_out_name = digital_out_name
        self._digital_out_state = digital_out_state

    @property
    def set_type(self):
        return self._set_type

    @set_type.setter
    @mark_modified()
    def set_type(self, value):
        self._set_type = value

    @property
    def digital_out_nr(self):
        return self._digital_out_nr

    @digital_out_nr.setter
    @mark_modified()
    def digital_out_nr(self, value):
        self._digital_out_nr = value

    @property
    def digital_out_name(self):
        return self._digital_out_name

    @digital_out_name.setter
    @mark_modified()
    def digital_out_name(self, value):
        self._digital_out_name = value

    @property
    def digital_out_state(self):
        return self._digital_out_state

    @digital_out_state.setter
    def digital_out_state(self, value):
        self._digital_out_state = value

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt' or not node.children:
            return

        parser = FunctionParser(
            name='set_digital_out',
            args=[
                Argument(
                    name='nr_or_name',
                    parsefunct=SetBlock._parse_number_or_string,
                ),
                Argument(name='state', type=bool),
            ],
        )
        success, args = parser.parse(node.children[0])
        if not success:
            return

        nr, name = args.get('nr_or_name')
        state = args.get('state')
        yield SetBlock(
            node,
            parent,
            set_type=SetType.SetDigitalOut,
            digital_out_nr=nr,
            digital_out_name=name,
            digital_out_state=state,
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
            return

        if self._digital_out_name:
            nr_or_name = prepare_string(self._digital_out_name)
        else:
            nr_or_name = self._digital_out_nr
        yield '{indent}set_digital_out({nr_or_name}, {state})\n'.format(
            indent=self._get_indent(),
            nr_or_name=nr_or_name,
            state=self.digital_out_state,
        )
