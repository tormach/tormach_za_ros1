from ..rpl import Command


class PathPilotAbort(Command):
    name = 'pathpilot_abort'

    def __init__(self, instance=''):
        super().__init__()

        self.instance = instance

    def execute(self):
        print(f'executing pathpilot_abort: instance={self.instance}')

    def __str__(self):
        return f'{self.name}: {self.instance}'
