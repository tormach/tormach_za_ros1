from typing import Union, Callable

from ..rpl import Command, InterruptSource


class RegisterInterrupt(Command):
    name = 'register_interrupt'

    def __init__(
        self,
        source: InterruptSource,
        nr_or_name: Union[int, str],
        fct: Callable,
    ):
        super().__init__()
        self.source = source
        self.nr = nr_or_name
        self.fct = fct

    def execute(self) -> None:
        print(f"executing {self.name}: {self.source} {self.nr}")

    def __str__(self):
        return f'{self.name}: {self.source} {self.nr}'
