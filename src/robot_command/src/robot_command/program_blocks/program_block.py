from .parse_helpers import ParseException
from .rpl_block import RPLBlock, mark_modified


class ProgramBlock(RPLBlock):
    type = 'program'

    def __init__(
        self,
        node,
        parent,
        name='subprogram',
        type_='mainprogram',
        parameters=None,
        defaults=None,
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)

        self._init_neighbor = self._has_neighbor(init=True)

        self.type = type_
        self._name = name
        self._parameters = [] if parameters is None else parameters
        self._defaults = [] if defaults is None else defaults

    @property
    def name(self):
        return self.program.name if self.type == 'mainprogram' else self._name

    @name.setter
    @mark_modified()
    def name(self, value):
        self._name = value

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    @mark_modified()
    def parameters(self, value):
        self._parameters = value

    @property
    def defaults(self):
        return self._defaults

    @defaults.setter
    @mark_modified()
    def defaults(self, value):
        self._defaults = value

    @staticmethod
    def read(node, parent):
        if node.type != 'funcdef':
            return
        if parent.level > 0:
            return
        type_ = 'mainprogram' if node.name.value == 'main' else 'subprogram'
        try:
            params, defaults = ProgramBlock._parse_parameters(node.children[2])
        except ParseException:
            return
        main = ProgramBlock(
            node,
            parent,
            name=node.name.value,
            type_=type_,
            parameters=params,
            defaults=defaults,
        )
        suite = node.get_suite()
        for node_child in suite.children:
            for child in main.program.read_block(node_child, main):
                main.add_child(child, modify=False)
        yield main

    @staticmethod
    def _parse_parameters(node):
        params = []
        defaults = []

        had_optional = False
        for param in node.children[1:-1]:
            params.append(param.name.value)
            if param.default is None:
                defaults.append(None)
                if had_optional:
                    raise ParseException(
                        'Optional parameters must bet declared after other parameters.'
                    )
            else:
                defaults.append(param.default.get_code())
                had_optional = True

        return params, defaults

    def _has_neighbor(self, init=False):
        """check if program block has a neighbor one line before the block"""
        if self.parent:
            if not init:
                if self.parent.children.index(self):
                    return True
            else:
                return bool(self.parent.children)
        else:
            return False

    def _needs_rewrite(self):
        result = super()._needs_rewrite()
        if not result and self._has_neighbor() is not self._init_neighbor:
            return True
        return result

    def write(self):
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
        else:
            if self._has_neighbor():
                yield '\n'
            params = []
            for i, param in enumerate(self._parameters):
                if self._defaults[i]:
                    params.append(f'{self._parameters[i]}={self._defaults[i]}')
                else:
                    params.append(self._parameters[i])
            yield 'def {}({}):\n'.format(
                'main' if self.type == 'mainprogram' else self._name,
                ', '.join(params),
            )
            for child in self.children:
                yield from child.write()
