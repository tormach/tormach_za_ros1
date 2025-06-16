from .rpl_block import RPLBlock


class EndOfProgramBlock(RPLBlock):
    type = 'endofprogram'

    def __init__(self, node, parent, **kwargs):
        super().__init__(node, parent, **kwargs)

    @staticmethod
    def read(node, parent):
        if node.type != 'endmarker':
            return
        yield EndOfProgramBlock(node, parent)
