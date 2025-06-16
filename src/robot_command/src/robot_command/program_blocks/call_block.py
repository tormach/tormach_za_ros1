from parso.python import tree

from .parse_helpers import ParseException
from .rpl_block import RPLBlock, mark_modified


class CallBlock(RPLBlock):
    type = 'call'

    def __init__(
        self,
        node,
        parent,
        name='',
        arguments=None,
        keyword_arguments=None,
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)

        self._name = name
        self._arguments = [] if arguments is None else arguments
        self._keyword_arguments = (
            {} if keyword_arguments is None else keyword_arguments
        )

    @property
    def name(self):
        return self._name

    @name.setter
    @mark_modified()
    def name(self, value):
        self._name = value

    @property
    def arguments(self):
        return self._arguments

    @arguments.setter
    @mark_modified()
    def arguments(self, value):
        self._arguments = value

    @property
    def keyword_arguments(self):
        return self._keyword_arguments

    @keyword_arguments.setter
    @mark_modified()
    def keyword_arguments(self, value):
        self._keyword_arguments = value

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt':
            return
        if not (
            node.children and node.children[0].type in ('power', 'atom_expr')
        ):
            return
        power = node.children[0]
        if not (
            len(power.children) == 2
            and isinstance(power.children[0], tree.Name)
            and power.children[1].type == 'trailer'
        ):
            return
        name = power.children[0].value

        trailer = power.children[1]
        try:
            args, kwargs = CallBlock._parse_arguments(trailer)
        except ParseException:
            return

        yield CallBlock(
            node, parent, name=name, arguments=args, keyword_arguments=kwargs
        )

    @staticmethod
    def _parse_arguments(trailer):
        argspec = trailer.children[1]
        data_nodes = []
        if argspec.type == 'arglist':
            data_nodes = argspec.children[::2]
        elif argspec.type == 'operator':
            return [], {}
        else:
            data_nodes.append(argspec)

        had_argument = False
        args = []
        kwargs = {}
        for i, node in enumerate(data_nodes):
            if node.type == 'argument':
                try:
                    name, _, data = node.children
                except ValueError:  # unpack operator not supported
                    raise ParseException
                kwargs[name.value] = data.get_code().strip()
                had_argument = True
            else:
                if had_argument:
                    raise ParseException(
                        'Positional argument after keyword argument not allowed.'
                    )
                args.append(node.get_code().strip())

        return args, kwargs

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
        else:
            arguments = self.arguments[:]
            arguments += [f'{k}={v}' for k, v in self.keyword_arguments.items()]
            yield '{}{}({})\n'.format(
                self._get_indent(), self.name, ', '.join(arguments)
            )
