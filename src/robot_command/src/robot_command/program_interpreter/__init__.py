import time

from .interpreter import (  # noqa: F401
    ProgramInterpreter,
    InterpreterProcess,
    InterpreterState,
)
from .internal_exceptions import ProgramExit  # noqa: F401
from .loader import ProgramLoader  # noqa: F401
from .types import *  # noqa: F401, F403


if __name__ == '__main__':
    interp = ProgramInterpreter()
    interp.start()
    interp.load_program('../../playground/hello_world.py')
    interp.start_program()
    print('giving program 2 seconds to work')
    time.sleep(2.0)
    print('pause for 2 seconds')
    interp.pause_program()
    time.sleep(2.0)
    print('continue for 2 seconds')
    interp.continue_program()
    time.sleep(2.0)
    print('terminating')
    interp.stop_program()
    print('done')
    interp.stop()
