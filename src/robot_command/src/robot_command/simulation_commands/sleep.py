from ..rpl import Command


class Sleep(Command):
    name = 'sleep'

    def __init__(self, secs):
        super().__init__()

        if not isinstance(secs, (float, int)) or secs < 0:
            raise TypeError(
                'Sleep requires a positive number as secs argument.'
            )

        self.secs = secs

    def execute(self):
        print(f'sleeping for {self.secs}s')

    def __str__(self):
        return f'{self.name}: {self.secs}'
