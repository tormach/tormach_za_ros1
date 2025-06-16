from typing import Any

from ..rpl import Command


class TriggerInterrupt(Command):
    name = 'trigger_interrupt'

    def __init__(self, nr: int, value: Any):
        super().__init__()

        self.nr = nr
        self.value = value

    def execute(self) -> None:
        print(f"executing {self.name}: {self.nr} {self.value}")

    def __str__(self):
        return f'{self.name}: {self.nr} {self.value}'
