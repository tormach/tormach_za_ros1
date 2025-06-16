import pytest
from ._waiter import waiter
from .qtquick import QtQuickTestWindow  # noqa: F401

waiter = pytest.fixture(waiter)
