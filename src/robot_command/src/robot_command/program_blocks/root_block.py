from .rpl_block import RPLBlock


class RootBlock(RPLBlock):
    type = 'root'

    def __init__(self, node, program, **kwargs):
        super().__init__(node, None, program, **kwargs)

    @staticmethod
    def read(node, parent):
        raise NotImplementedError('Not applicable for root block')

    def write(self):
        for child in self.children:
            yield from child.write()

    def read_program(self):
        for node in self.node.children:
            for child in self.program.read_block(node, self):
                self.add_child(child, modify=False)
