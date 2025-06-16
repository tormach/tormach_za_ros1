import attr


@attr.s
class Argument:
    name = attr.ib(type=str)
    type = attr.ib(default=None)
    optional = attr.ib(type=bool, default=False)
    parsefunct = attr.ib(default=None)


def convert_string(string):
    string = string.encode('utf-8').decode('unicode_escape')

    is_block = False
    if len(string) > 2 and string[-3:] in (r'"""', r"'''"):
        string = string[:-3]
        is_block = True
    elif len(string) > 0 and string[-1] in (r'"', r"'"):
        string = string[:-1]
    if len(string) > 2 and string[:3] in (r'"""', r"'''"):
        string = string[3:]
        is_block = True
    elif len(string) > 0 and string[0] in (r'"', r"'"):
        string = string[1:]
    return string, is_block


def prepare_string(string, block=False):
    return '{quotes}{text}{quotes}'.format(
        text=string.replace('"', r'\"'), quotes=r'"""' if block else r'"'
    )


class ParseException(Exception):
    pass


class FunctionParser:
    def __init__(self, name, args=None):
        if args is None:
            args = []

        self._check_args(args)

        self._args_by_name = {}
        self._required_args = []
        self.args = args
        self.name = name

    @staticmethod
    def _check_args(args):
        had_optional = False
        for arg in args:
            if arg.optional:
                had_optional = True
            elif had_optional:
                raise ValueError(
                    'Must specify required arguments before optional'
                )

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        self._args = value
        self._args_by_name = {arg.name: arg for arg in value}
        self._required_args = [arg for arg in self.args if not arg.optional]
        self._required_args_by_name = {
            arg.name: arg for arg in self._required_args
        }

    def parse(self, node):
        try:
            return True, self._do_parse(node)
        except ParseException:
            return False, {}

    def _do_parse(self, node):
        parsed_args = {}

        if node.type not in ('power', 'atom_expr'):
            raise ParseException('Node is not a function.')

        if node.children[0].value != self.name:
            raise ParseException('Function name does not match.')

        trailer = node.children[1]

        if len(trailer.children) == 2:
            if len(self._required_args) > 0:
                raise ParseException('Passed 0 args, but requires more than 0.')
            return {}
        elif len(self.args) == 0:
            raise ParseException('Passed more than 0 args, but requires none.')
        argspec = trailer.children[1]
        data_nodes = []
        if argspec.type == 'arglist':
            data_nodes = argspec.children[::2]
        else:
            data_nodes.append(argspec)

        if len(data_nodes) > len(self.args):
            raise ParseException('More arguments than expected.')

        had_argument = False
        for i, node in enumerate(data_nodes):
            if node.type == 'argument':
                name, _, data = node.children
                name = name.value
                if name not in self._args_by_name:
                    raise ParseException('Wrong argument supplied.')
                type_ = self._args_by_name[name].type
                parsefunct = self._args_by_name[name].parsefunct
                had_argument = True
            else:
                if had_argument:
                    raise ParseException(
                        'Positional argument after keyword argument not allowed.'
                    )
                name = self.args[i].name
                type_ = self.args[i].type
                parsefunct = self.args[i].parsefunct
                data = node

            value = self._parse_type(data, type_=type_, parsefunct=parsefunct)
            parsed_args[name] = value

        if not set(self._required_args_by_name.keys()).issubset(
            set(parsed_args.keys())
        ):
            raise ParseException('Not all required arguments supplied.')

        return parsed_args

    @staticmethod
    def _parse_type(node, type_, parsefunct):
        if type_ == str:
            return FunctionParser._parse_string(node)
        elif type_ in (int, float):
            return FunctionParser._parse_number(node, type_=type_)
        elif type_ == bool:
            return FunctionParser._parse_bool(node)
        else:
            if not parsefunct:
                raise ParseException(
                    'Type unknown, but no parse function defined.'
                )
            return parsefunct(node, type_)

    @staticmethod
    def _parse_bool(node):
        if node.type not in ('name', 'keyword'):
            raise ParseException('Type does not match')
        if node.value == 'True':
            return True
        elif node.value == 'False':
            return False
        else:
            raise ParseException('Argument is not bool.')

    @staticmethod
    def _parse_string(node):
        if node.type != 'string':
            raise ParseException('Type does not match.')
        string, _ = convert_string(node.value)
        return string

    @staticmethod
    def _parse_number(node, type_):
        if node.type == 'factor':
            value_string = ''.join(c.value for c in node.children)
        elif node.type == 'number':
            value_string = node.value
        else:
            raise ParseException('Type does not match.')
        try:
            return type_(value_string)
        except ValueError:
            raise ParseException('Error parsing number.')
