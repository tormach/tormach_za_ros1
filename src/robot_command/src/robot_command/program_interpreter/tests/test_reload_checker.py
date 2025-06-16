import pytest
import os
import sys
import importlib
from robot_command.program_interpreter.reload_checker import ReloadChecker


@pytest.fixture
def checker():
    return ReloadChecker()


def test_when_modules_havent_changed_check_for_changes_return_false(checker):
    checker.update()

    assert checker.modified is False


@pytest.fixture
def file_baked_module(tmpdir):
    # Create a new temporary module
    module_file = tmpdir.join("temp_module.py")
    module_file.write("def temp_function():\n    return 'temporary'")
    sys.path.insert(0, str(tmpdir))

    module_name = "temp_module"
    yield module_name, str(module_file)

    # Cleanup
    sys.path.remove(str(tmpdir))
    del sys.modules[module_name]


@pytest.mark.xfail(reason="known unreliable test")
def test_importing_file_baked_module_does_not_trigger_modified(
    file_baked_module, checker
):
    module_name, _ = file_baked_module
    checker.update()

    # Import a new module and update again
    importlib.import_module(module_name)
    checker.update()

    assert not checker.modified


def test_modifying_imported_file_baked_module_triggers_modified(
    file_baked_module, checker
):
    module_name, module_file = file_baked_module
    importlib.import_module(module_name)
    checker.update()

    # Modify the module file and update again
    with open(module_file, "w") as f:
        f.write("def temp_function():\n    return 'modified'")
    checker.update()

    assert checker.modified


def test_reset_after_imported_module_was_modified_resets_modified(
    file_baked_module, checker
):
    module_name, module_file = file_baked_module
    importlib.import_module(module_name)
    checker.update()

    # change timestamp to simulate a modification
    os.utime(module_file, None)
    checker.update()

    assert checker.modified

    # Reset the checker and update again
    checker.reset()
    checker.update()

    assert not checker.modified


@pytest.fixture
def folder_baked_module(tmpdir):
    # Create a new temporary module
    module_dir = tmpdir.mkdir("temp_module")
    module_file = module_dir.join("__init__.py")
    module_file.write("from .foo import temp_function")
    module_file = module_dir.join("foo.py")
    module_file.write("def temp_function():\n    return 'temporary'")
    sys.path.insert(0, str(tmpdir))

    module_name = "temp_module"
    yield module_name, str(module_dir)

    # Cleanup
    sys.path.remove(str(tmpdir))
    del sys.modules[module_name]


def test_importing_folder_baked_module_does_not_trigger_modified(
    folder_baked_module, checker
):
    module_name, _ = folder_baked_module
    checker.update()

    # Import a new module and update again
    importlib.import_module(module_name)
    checker.update()

    assert not checker.modified


def test_modifying_imported_folder_baked_module_triggers_modified(
    folder_baked_module, checker
):
    module_name, module_dir = folder_baked_module
    importlib.import_module(module_name)
    checker.update()

    # Modify the module file and update again
    module_file = os.path.join(module_dir, "foo.py")
    with open(module_file, "w") as f:
        f.write("def temp_function():\n    return 'modified'")
    checker.update()

    assert checker.modified
