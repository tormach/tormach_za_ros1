from collections import namedtuple

import rospy

from .hal_io_interface import HalIoInterfaceSingleton
from ..program_interpreter import InterpreterProcess
from ..rpl import InterruptSource

Interrupt = namedtuple('Interrupt', 'source number')


class InterruptInterface:
    def __init__(self):
        self._interrupt_functions = {}
        self._hal_io = HalIoInterfaceSingleton()
        self._hal_io.on_digital_input_update_received.append(
            self._on_digital_input_update_received
        )
        self._hal_io.on_user_io_update_received.append(
            self._on_user_io_update_received
        )
        InterpreterProcess.interp_process().handle_interrupt = (
            self._handle_interrupt
        )
        InterpreterProcess.interp_process().reset_interrupts = (
            self.unregister_all_interrupts
        )

    def _handle_interrupt(self, source_id, number, value):
        interrupt = Interrupt(InterruptSource(source_id), number)
        if interrupt in self._interrupt_functions:
            self._interrupt_functions[interrupt](value)

    def trigger_program_interrupt(self, nr, value):
        if Interrupt(InterruptSource.Program, nr) in self._interrupt_functions:
            rospy.loginfo(f"Program interrupt triggered nr={nr} value={value}")
            InterpreterProcess.trigger_interrupt(
                InterruptSource.Program, nr, value
            )
            return True
        else:
            return False

    def register_interrupt(self, source, number, fct):
        interrupt = Interrupt(source, number)
        self._interrupt_functions[interrupt] = fct
        rospy.loginfo(f"Interrupt registered source={source.name} nr={number}")

    def unregister_interrupt(self, source, number):
        interrupt = Interrupt(source, number)
        if interrupt in self._interrupt_functions:
            del self._interrupt_functions[interrupt]
            rospy.loginfo(
                f"Interrupt unregistered source={source.name} nr={number}"
            )

    def unregister_all_interrupts(self):
        self._interrupt_functions.clear()

    def _on_digital_input_update_received(self, nr, value):
        interrupt = Interrupt(InterruptSource.DigitalInput, nr)
        if interrupt in self._interrupt_functions:
            rospy.loginfo(
                f"Digital input interrupt triggered nr={nr} value={value}"
            )
            InterpreterProcess.trigger_interrupt(
                InterruptSource.DigitalInput, nr, value
            )

    def _on_user_io_update_received(self, nr, value):
        interrupt = Interrupt(InterruptSource.UserIo, nr)
        if interrupt in self._interrupt_functions:
            rospy.loginfo(f"User IO interrupt triggered nr={nr} value={value}")
            InterpreterProcess.trigger_interrupt(
                InterruptSource.UserIo, nr, value
            )


class InterruptInterfaceSingleton:
    """
    Singleton interface class to robot program Interrupts
    """

    _instance = None

    def __init__(self):
        if not InterruptInterfaceSingleton._instance:
            InterruptInterfaceSingleton._instance = InterruptInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)
