from ..rpl import Command


class ChangeToolFrame(Command):
    name = 'change_tool_frame'

    def __init__(self, name):
        super().__init__()
        if not (name is None or isinstance(name, str)):
            raise TypeError(
                "Tool frame name must be specified as first argument."
            )
        self.tool_name = name

    def execute(self):
        print(f'executing {self.name}: {self.tool_name}')

    def __str__(self):
        return f'{self.name}: {self.tool_name}'
