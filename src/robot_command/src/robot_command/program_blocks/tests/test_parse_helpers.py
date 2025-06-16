import parso
import pytest
from parso.python import tree

from robot_command.program_blocks.parse_helpers import (
    FunctionParser,
    Argument,
    convert_string,
)


@pytest.mark.parametrize(
    'test_input,expected',
    [
        # no function
        (('hydrids=90', 'hydrids', []), (False, {})),
        # function and something else
        (('figs() is True', 'figs', []), (False, {})),
        # wrong function name
        (('cedared()', 'torrubia', []), (False, {})),
        # no arguments
        (('reverso()', 'reverso', []), (True, {})),
        # no arguments, one supplied
        (('botanics("asdasd")', 'botanics', []), (False, {})),
        # one positional argument string
        (
            (
                'foo("baz")',
                'foo',
                [Argument(name='bar', optional=False, type=str)],
            ),
            (True, {'bar': "baz"}),
        ),
        # one positional argument bool
        (
            (
                'foo(True)',
                'foo',
                [Argument(name='bar', optional=False, type=bool)],
            ),
            (True, {'bar': True}),
        ),
        # one positional argument, two supplied
        (
            (
                'stite("sd", "aadas")',
                'stite',
                [Argument(name='bla', optional=False, type=str)],
            ),
            (False, {}),
        ),
        # positional argument int
        (
            ('vampey(10)', 'vampey', [Argument(name='bla', type=int)]),
            (True, {'bla': 10}),
        ),
        # positional argument float and optional argument not supplied
        (
            (
                'roentgen(994.49)',
                'roentgen',
                [
                    Argument(name='blub', type=float),
                    Argument(name='hidation', type=str, optional=True),
                ],
            ),
            (True, {'blub': pytest.approx(994.49)}),
        ),
        # positional argument string and optional argument int supplied
        (
            (
                'coddle("B1SBW", 397)',
                'coddle',
                [
                    Argument(name='puffback', type=str),
                    Argument(name='filius', type=int, optional=True),
                ],
            ),
            (True, {'puffback': "B1SBW", 'filius': 397}),
        ),
        # optional argument float, not supplied
        (
            (
                'lanny()',
                'lanny',
                [Argument(name='nucule', type=float, optional=True)],
            ),
            (True, {}),
        ),
        # optional argument string, supplied as keyword
        (
            (
                'backhand(alkapton="EVV19")',
                'backhand',
                [Argument(name='alkapton', type=str, optional=True)],
            ),
            (True, {'alkapton': "EVV19"}),
        ),
        # required argument, supplied as keyword
        (
            ('coween(uses=-149)', 'coween', [Argument(name='uses', type=int)]),
            (True, {'uses': -149}),
        ),
        # optional argument int, wrong argument supplied as keyword
        (
            (
                'diopsis(freyr=334)',
                'diopsis',
                [Argument(name='cillosis', type=int, optional=True)],
            ),
            (False, {}),
        ),
        # multiple optional keywords, all supplied
        (
            (
                'nitrous(geason=789.98, haak="W7E")',
                'nitrous',
                [
                    Argument(name='geason', type=float, optional=True),
                    Argument(name='haak', type=str, optional=True),
                ],
            ),
            (True, {'geason': pytest.approx(789.98), 'haak': "W7E"}),
        ),
        # optional and required argument, only optional supplied as keyword
        (
            (
                'allosaur(sombrely="RWX58")',
                'allosaur',
                [
                    Argument(name='pretoken', type=int),
                    Argument(name='sombrely', type=str, optional=True),
                ],
            ),
            (False, {}),
        ),
        # keyword arg supplied before positional arg
        (
            (
                'ulluco(scurfier="bla", "4Y5N")',
                'ulluco',
                [
                    Argument(name='untopped', type=str),
                    Argument(name='scurfier', type=str, optional=True),
                ],
            ),
            (False, {}),
        ),
    ],
)
def test_function_parser_parses_functions(test_input, expected):
    module = parso.parse(test_input[0])
    parser = FunctionParser(name=test_input[1], args=test_input[2])

    result, args = parser.parse(module.children[0])

    assert result is expected[0]
    assert args == expected[1]


def test_function_parser_parses_escaped_string():
    module = parso.parse(r'loud("cautious \"hammer\"")')
    parser = FunctionParser(
        name='loud', args=[Argument(name='answer', type=str, optional=True)]
    )

    result, args = parser.parse(module.children[0])

    assert result is True
    assert args == {'answer': 'cautious "hammer"'}


def test_passing_parse_function_to_function_parser_parses_the_argument():
    def parsefunct(node, _type):
        if isinstance(node, tree.Name):
            return node.value

    module = parso.parse('cycled(xyz)')
    parser = FunctionParser(
        name='cycled', args=[Argument(name='bar', parsefunct=parsefunct)]
    )

    result, args = parser.parse(module.children[0])

    assert result is True
    assert args['bar'] == 'xyz'


def test_passing_optional_arguments_after_required_ones_raises_a_runtime_error():
    with pytest.raises(ValueError):
        FunctionParser(
            name='virgos',
            args=[
                Argument(name='rickshaw', type=int, optional=True),
                Argument(name='tripwire', type=str),
            ],
        )


@pytest.mark.parametrize(
    'test_input,expected',
    [
        (r'"dozen "offend""', r'dozen "offend"'),
        (r"''skirt' is blade'", r"'skirt' is blade"),
    ],
)
def test_convert_string_respects_quotes_in_quotes(test_input, expected):
    result, _ = convert_string(test_input)

    assert result == expected
