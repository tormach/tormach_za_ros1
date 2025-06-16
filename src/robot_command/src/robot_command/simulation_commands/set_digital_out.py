from ..rpl import Command


class SetDigitalOut(Command):
    name = 'set_digital_out'

    def __init__(self, n, state):
        super().__init__()
        self.n = n
        self.state = state

    def execute(self):
        print(f'executing set_digital_out: {self.n} {self.state}')

    def __str__(self):
        return f'{self.name}: {self.n} {self.state}'
