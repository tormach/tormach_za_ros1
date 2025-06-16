"""Common classes and functions used to provide
functionalities for 'pp_account.storage' package.
Members of this module should be in no way
considered public, the opposite in fact, only as
an internal codebase.
"""


class _Singleton(type):
    # Should really be a loop-local storage
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]
