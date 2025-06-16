from ..rpl import Command


class GetActiveToolFrame(Command):
    name = 'get_active_tool_frame'

    def __init__(self):
        super().__init__()

    def execute(self):
        print(f'executing {self.name}')

    def __str__(self):
        return f'{self.name}'
