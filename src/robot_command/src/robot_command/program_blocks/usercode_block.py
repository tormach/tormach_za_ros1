from .rpl_block import RPLBlock


class UserCodeBlock(RPLBlock):
    type = 'usercode'

    def __init__(self, node, parent, **kwargs):
        super().__init__(node, parent, **kwargs)

    @staticmethod
    def read(node, parent):
        if node.type not in ('newline', 'endmarker'):
            yield UserCodeBlock(node, parent)
