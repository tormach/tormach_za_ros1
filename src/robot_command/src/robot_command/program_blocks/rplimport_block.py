from .rpl_block import RPLBlock


class RPLImportBlock(RPLBlock):
    type = 'rplimport'

    def __init__(self, node, parent, **kwargs):
        super().__init__(node, parent, **kwargs)

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt':
            return
        if not (any(node.children) and node.children[0].type == 'import_from'):
            return
        import_node = node.children[0]
        values = [n.value for n in import_node.get_from_names()]
        if values != ['robot_command', 'rpl']:
            return
        if not import_node.is_star_import():
            return

        yield RPLImportBlock(node, parent)

    def write(self):
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
            return

        yield f'{self._get_indent()}from robot_command.rpl import *\n'
