from ..rpl import Command


class PathPilotMdi(Command):
    name = 'pathpilot_mdi'

    def __init__(self, command, instance=''):
        super().__init__()
        self.command = command
        self.instance = instance

    def execute(self):
        print(
            'executing pathpilot_mdi: cmd={}, instance={}'.format(
                self.command, self.instance
            )
        )

    def __str__(self):
        return f'{self.name}: {self.command} {self.instance}'
