from pyparsing import Word, nums, delimitedList


class IntRangeParser:
    # Cribbed from http://thoughtsbyclayg.blogspot.com/2008/10/parsing-list-of-numbers-in-python.html
    integer = Word(nums)
    integer.setParseAction(lambda t: int(t[0]))

    integer_range = integer + "-" + integer
    integer_range.setParseAction(
        lambda t: list(
            range(t[0], t[2] + 1) if t[0] < t[2] else range(t[2], t[0] + 1)
        )
    )

    integer_list = delimitedList(integer_range | integer, ",")
    integer_list.setParseAction(lambda t: sorted(set(t.asList())))

    @classmethod
    def parse_integer(cls, intstr):
        return cls.integer.parseString(intstr)

    @classmethod
    def parse_integer_range(cls, rangestr):
        return cls.integer_range.parseString(rangestr).asList()

    @classmethod
    def parse(cls, rangestr):
        return cls.integer_list.parseString(rangestr).asList()
