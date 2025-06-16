from .parse_helpers import (
    FunctionParser,
    Argument,
    convert_string,
    ParseException,
)
from .rpl_block import RPLBlock, mark_modified


class UnitsBlock(RPLBlock):
    def __init__(
        self,
        node,
        parent,
        linear_unit='',
        angular_unit='',
        time_unit='',
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)

        self._linear_unit = linear_unit
        self._angular_unit = angular_unit
        self._time_unit = time_unit

    @property
    def linear_unit(self):
        return self._linear_unit

    @linear_unit.setter
    @mark_modified()
    def linear_unit(self, value):
        self._linear_unit = value

    @property
    def angular_unit(self):
        return self._angular_unit

    @angular_unit.setter
    @mark_modified()
    def angular_unit(self, value):
        self._angular_unit = value

    @property
    def time_unit(self):
        return self._time_unit

    @time_unit.setter
    @mark_modified()
    def time_unit(self, value):
        self._time_unit = value

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt' or not node.children:
            return

        parser = FunctionParser(
            name='set_units',
            args=[
                Argument(
                    'linear',
                    parsefunct=UnitsBlock._parse_unit_type,
                    optional=True,
                ),
                Argument(
                    'angular',
                    parsefunct=UnitsBlock._parse_unit_type,
                    optional=True,
                ),
                Argument(
                    'time',
                    parsefunct=UnitsBlock._parse_unit_type,
                    optional=True,
                ),
            ],
        )
        success, args = parser.parse(node.children[0])
        if not success:
            return

        yield UnitsBlock(
            node,
            parent,
            linear_unit=args.get('linear', ''),
            angular_unit=args.get('angular', ''),
            time_unit=args.get('time', ''),
        )

    @staticmethod
    def _parse_unit_type(node, _type):
        if node.type == 'string':
            string, _ = convert_string(node.value)
            return string
        elif node.type in ('name', 'keyword') and node.value == 'None':
            return ''
        elif node.type in ('power', 'atom_expr') and len(node.children) == 2:
            name = node.children[0]
            if name.type != 'name' and name.value == 'ureg':
                raise ParseException()
            trailer = node.children[1]
            if trailer.type != 'trailer' and len(trailer.children) == 2:
                raise ParseException()
            if (
                trailer.children[0].type != 'operator'
                or trailer.children[0].value != '.'
            ):
                raise ParseException()
            unit = trailer.children[1]
            if unit.type != 'name':
                raise ParseException()
            return unit.value
        else:
            raise ParseException("Passed wrong type.")

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
            return

        if self._linear_unit and self._angular_unit and self._time_unit:
            arguments = f'"{self._linear_unit}", "{self._angular_unit}", "{self._time_unit}"'
        elif self._linear_unit and self._angular_unit:
            arguments = f'"{self._linear_unit}", "{self._angular_unit}"'
        else:
            arguments = []
            if self._linear_unit:
                arguments.append(f'linear="{self._linear_unit}"')
            if self._angular_unit:
                arguments.append(f'angular="{self._angular_unit}"')
            if self._time_unit:
                arguments.append(f'time="{self._time_unit}"')
            arguments = ', '.join(arguments)
        yield f'{self._get_indent()}set_units({arguments})\n'
