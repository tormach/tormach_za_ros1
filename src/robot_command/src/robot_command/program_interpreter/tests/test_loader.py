import os
import ast

import pytest

from robot_command.program_interpreter import ProgramLoader
import robot_command.program_interpreter.loader


def save_program(tmpdir, source):
    path = os.path.join(str(tmpdir), 'sample_program.py')
    with open(path, 'w') as f:
        f.write(source)
    return path


@pytest.fixture
def sample_program(tmpdir):
    source = '''\
from __future__ import print_function
import time
import os

def main():
    # some movement commands
    movel(p[0, 0, 0, 0, 0, 0])
    movel(p[0, 2.0, 0, 0, 0, 0])
    movel(p[10, 0, 0, 0, 0, 0])
'''
    return save_program(tmpdir, source)


@pytest.fixture
def empty_program(tmpdir):
    source = '''\
def main():
    pass
'''
    return save_program(tmpdir, source)


@pytest.fixture
def endless_program(tmpdir):
    source = '''\
def main():
    while True:
        continue
'''
    return save_program(tmpdir, source)


@pytest.fixture
def while_false_program(tmpdir):
    source = '''\
def main():
    while False:
        break
'''
    return save_program(tmpdir, source)


@pytest.fixture
def for_range_zero_program(tmpdir):
    source = '''\
def main():
    for _ in range(0):
        break
'''
    return save_program(tmpdir, source)


@pytest.fixture
def assignment_program(tmpdir):
    source = '''\
def main():
    x = 10
'''
    return save_program(tmpdir, source)


@pytest.fixture
def exit_program(tmpdir):
    source = '''\
def main():
    movel(p[0, 2.0, 0, 0, 0, 0])
    movel(p[10, 0, 0, 0, 0, 0])
    exit()
    '''
    return save_program(tmpdir, source)


@pytest.fixture
def exotic_program(tmpdir):
    source = '''\
def main():
    if True:
        pass
    else:
        pass
    try:
        pass
    except:
        pass
    else:
        pass
    finally:
        pass
    for _ in range(1):
        pass
    else:
        pass
    while True:
        pass
    else:
        pass
'''
    return save_program(tmpdir, source)


@pytest.fixture
def try_except_program(tmpdir):
    source = '''\
def main():
    try:
        pass
    except:
        pass
'''
    return save_program(tmpdir, source)


def find_helper_calls(parent, function_name):
    count = 0
    iterables = [parent.body]
    if hasattr(parent, 'orelse'):
        iterables.append(parent.orelse)
    if hasattr(parent, 'finalbody'):
        iterables.append(parent.finalbody)
    for container in iterables:
        for node in list(container):
            if hasattr(node, 'body'):
                count += find_helper_calls(node, function_name)
            if hasattr(node, 'handlers'):
                for handler in node.handlers:
                    count += find_helper_calls(handler, function_name)
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                func = node.value.func
                if func.id == function_name:
                    count += 1
    return count


def helper_calls_in_program(program, function_name='_query_status_helper'):
    loader = ProgramLoader(interpreter='test')
    loader.load_program(program)
    return find_helper_calls(loader.tree, function_name)


def find_main_node(parent):
    return next(
        (
            node
            for node in parent.body
            if isinstance(node, ast.FunctionDef) and node.name == 'main'
        ),
        None,
    )


def test_program_loader_inserts_helper_function_calls_before_expr(
    sample_program,
):
    assert helper_calls_in_program(sample_program) == 3


def test_program_loader_inserts_helper_function_call_before_pass(empty_program):
    assert helper_calls_in_program(empty_program) == 1


def test_program_loader_inserts_helper_function_calls_in_non_body_branches(
    exotic_program,
):
    assert helper_calls_in_program(exotic_program) == 14


def test_program_loader_inserts_helper_function_call_before_continue(
    endless_program,
):
    assert helper_calls_in_program(endless_program) == 2


def test_program_loader_inserts_helper_function_call_before_while_loop(
    while_false_program,
):
    assert helper_calls_in_program(while_false_program) == 2


def test_program_loader_inserts_helper_function_call_before_for_loop(
    for_range_zero_program,
):
    assert helper_calls_in_program(for_range_zero_program) == 2


def test_program_loader_inserts_helper_function_call_before_assignment(
    assignment_program,
):
    assert helper_calls_in_program(assignment_program) == 1


@pytest.mark.dependency()
def test_program_loader_inserts_single_reload_required_helper_function_call(
    sample_program,
):
    assert (
        helper_calls_in_program(
            sample_program, '_update_reload_required_helper'
        )
        == 1
    )


@pytest.mark.dependency(
    depends=[
        'test_program_loader_inserts_single_reload_required_helper_function_call'
    ]
)
def test_program_loader_inserts_reload_required_helper_function_call_after_other_imports(
    sample_program,
):
    loader = ProgramLoader(interpreter='test')

    loader.load_program(sample_program)

    node = loader.tree.body[5]
    assert isinstance(node, ast.Expr)
    assert node.value.func.id == '_update_reload_required_helper'


def test_program_loader_inserts_start_and_end_program_calls(sample_program):
    loader = ProgramLoader(interpreter='rich')

    loader.load_program(sample_program)

    assert isinstance(loader.tree.body[0], ast.Expr)
    assert loader.tree.body[0].value.func.id == 'rpl_program_start'

    main = find_main_node(loader.tree)
    assert main is not None
    assert isinstance(main.body[0], ast.Expr)
    assert main.body[0].value.func.id == 'rpl_main_program_start'
    assert isinstance(main.body[-1], ast.Expr)
    assert main.body[-1].value.func.id == 'rpl_main_program_end'


def test_program_loader_inserts_end_program_call_before_exit(exit_program):
    loader = ProgramLoader(interpreter='tempt')

    loader.load_program(exit_program)

    main = find_main_node(loader.tree)
    assert main is not None
    assert isinstance(main.body[-3], ast.Expr)
    assert main.body[-3].value.func.id == 'rpl_main_program_end'


def test_program_loader_inserts_helper_function_import_after_other_imports(
    sample_program,
):
    loader = ProgramLoader(interpreter='test')

    loader.load_program(sample_program)

    assert isinstance(loader.tree.body[4], ast.ImportFrom)
    assert (
        loader.tree.body[4].module
        == robot_command.program_interpreter.loader.__name__
    )


def test_program_loader_inserts_registering_methods_for_on_abort_handlers(
    sample_program,
):
    loader = ProgramLoader(interpreter='test')

    loader.load_program(sample_program)

    def find_if_and_check(index, name):
        result = loader.tree.body[index]
        assert isinstance(result, ast.If)
        assert result.test.values[0].left.s == name

    find_if_and_check(-1, 'on_pause')
    find_if_and_check(-2, 'on_abort')


def test_program_loader_fails_if_file_does_not_exist():
    loader = ProgramLoader(interpreter='test')
    with pytest.raises(IOError):
        loader.load_program('does_not_exist.py')


def test_program_loader_adds_exception_handler_to_try_except(
    try_except_program,
):
    loader = ProgramLoader(interpreter='test')

    loader.load_program(try_except_program)

    main = find_main_node(loader.tree)
    assert main is not None
    try_node = next(
        (node for node in main.body if isinstance(node, ast.Try)),
        None,
    )
    assert try_node is not None
    assert isinstance(try_node.handlers[0], ast.ExceptHandler)
