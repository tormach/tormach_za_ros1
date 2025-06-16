from ..rpl import Command


class PathPilotCycleStart(Command):
    name = 'pathpilot_cycle_start'

    def __init__(self, instance=''):
        super().__init__()

        self.instance = instance

    def execute(self):
        print(f'executing pathpilot_cycle_start: instance={self.instance}')

    def __str__(self):
        return f'{self.name}: {self.instance}'
