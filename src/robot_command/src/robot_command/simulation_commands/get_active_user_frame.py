from ..rpl import Command


class GetActiveUserFrame(Command):
    name = 'get_active_user_frame'

    def __init__(self):
        super().__init__()

    def execute(self):
        print(f'executing {self.name}')

    def __str__(self):
        return f'{self.name}'
