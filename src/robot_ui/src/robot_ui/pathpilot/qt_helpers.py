import itertools

from PySide6.QtCore import Slot as QtSlot, qWarning
from PySide6.QtCore import QObject, QCoreApplication, QMetaMethod


def snake_case_to_camel_case(name):
    words = name.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])


class MultiSlot:
    """
    Makes creating Qt Slots with multiple different signatures easier.
    Additionally this decorator registers a camelCase alias for the slot.
    Needs to be combined with the QtObject decorator for
    camelCasing to work.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, func):
        new_args = list(
            itertools.product(
                *[arg if isinstance(arg, list) else [arg] for arg in self.args]
            )
        )
        filtered_new_args = [
            [arg for arg in new_arg if arg is not None] for new_arg in new_args
        ]
        camel_name = (
            func.__name__
            if func.__name__.startswith("_")
            else snake_case_to_camel_case(func.__name__)
        )
        for new_arg in filtered_new_args:
            func = QtSlot(*new_arg, **self.kwargs)(func)
            if camel_name != func.__name__:
                func = QtSlot(*new_arg, *self.kwargs, name=camel_name)(func)

        func.__is_slot__ = True
        return func


def QtObject(cls):
    """
    Class decorator to add camelCase aliases for
    Qt slots which have been prepared for camelCasing.
    """
    for name, method in list(cls.__dict__.items()):  # Use list() to make a copy
        if getattr(method, "__is_slot__", False):
            camel_name = snake_case_to_camel_case(name)
            setattr(cls, camel_name, method)
    return cls


def ensure_cleanup(slot):
    """
    Ensures cleanup by connecting a slot function to the `destroyed` signal of a
    QObject and the `aboutToQuit` signal of the QCoreApplication instance.

    @param qobject: The QObject to connect the `destroyed` signal to. @param
    slot: The slot to be called when the `destroyed` or `aboutToQuit` signal is
    emitted.
    """
    bound = slot.__self__
    name = slot.__name__
    if not isinstance(bound, QObject):
        raise ValueError(f"slot {name} must be bound to a QObject")
    is_slot = False
    for i in range(bound.metaObject().methodCount()):
        method = bound.metaObject().method(i)
        if method.name() == name and method.methodType() == QMetaMethod.Slot:
            is_slot = True
            break
    if not is_slot:
        raise ValueError(f"slot {name} of {type(bound)} must be a Qt slot")
    bound.destroyed.connect(lambda: slot())
    if qapp := QCoreApplication.instance():
        qapp.aboutToQuit.connect(slot)
    else:
        qWarning(
            "No QCoreApplication instance found when trying to ensure cleanup"
        )
