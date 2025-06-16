import pytest
from hal_402_device_mgr.params.int_range import IntRangeParser


class TestIntRangeParser:
    @pytest.fixture
    def parser(self):
        yield IntRangeParser()

    def test_integer_parser(self, parser):
        test_cases = [0, 1, 2, 42, 12]
        for argint in test_cases:
            argstr = str(argint)
            print(
                repr(argstr), repr(argint), repr(parser.parse_integer(argstr))
            )

    def test_integer_range(self, parser):
        test_cases = {
            '0-5': [0, 1, 2, 3, 4, 5],
            '1-2': [1, 2],
        }

        for argstr, expected in test_cases.items():
            print(
                repr(argstr),
                repr(expected),
                repr(parser.parse_integer_range(argstr)),
            )
            assert parser.parse_integer_range(argstr) == expected

    def test_range_parser(self, parser):
        test_cases = {
            '0': [0],
            '0-5': [0, 1, 2, 3, 4, 5],
            '0,1,2': [0, 1, 2],
            '0,3-5,2': [0, 2, 3, 4, 5],
        }

        for argstr, expected in test_cases.items():
            print(repr(argstr), repr(expected), repr(parser.parse(argstr)))
            assert parser.parse(argstr) == expected
