import ast
import os

import pathlib
from robot_command.rpl import (
    rpl_main_program_start,
    rpl_main_program_end,
    rpl_program_start,
)
from .shared import INTERPRETER_PROCESS_NAME
from .internal_exceptions import ProgramExit


def _query_status_helper(process, line_number, filename):
    process.report_position((line_number, filename))
    process.spin_from_injected()


def _update_reload_required_helper(process):
    process.update_reload_required()


class ProgramLoader:
    """Loads and prepares Python RPL programs for execution with the interpreter."""

    HANDLER_METHOD_NAMES = ('on_abort', 'on_pause')

    def __init__(self, interpreter='simulation'):
        self._source_code = ''
        self._tree = None
        self._path = ''
        self._program_name = ''
        self._interpreter = interpreter

    def load_program(self, path):
        abs_path = os.path.abspath(path)
        self._path = abs_path
        self._program_name, _ = os.path.splitext(os.path.basename(self._path))

        self._source_code = pathlib.Path(abs_path).read_text()
        self._tree = self._prepare_program(self._source_code, self._path)

    @staticmethod
    def load_mdi_command(command):
        template = f'''def main():\n  {command}\n'''
        return ProgramLoader._prepare_program(template, '_mdi_command_')

    def unload_program(self):
        self._path = ''
        self._program_name = None
        self._tree = None

    @property
    def tree(self):
        return self._tree

    @property
    def path(self):
        return self._path

    @staticmethod
    def _extract_program_node(tree):
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'main':
                return node
        raise AttributeError('missing main program main()')

    @staticmethod
    def _prepare_program(source_code, path):
        tree = ast.parse(source_code, filename=path)
        program_node = ProgramLoader._extract_program_node(tree)
        ProgramLoader._insert_helper_function_calls(tree, program_node, path)
        ProgramLoader._ensure_raising_program_exit_from_try_except(tree)
        ProgramLoader._insert_start_and_end_program(tree, program_node)
        ProgramLoader._insert_register_on_abort_handler(tree, program_node)
        return tree

    @staticmethod
    def _recurse_tree(parent, method, level=0):
        iterables = [parent.body]
        if hasattr(parent, 'orelse'):  # if, try, try *, for, async for, while,
            iterables.append(parent.orelse)
        if hasattr(parent, 'finalbody'):  # try, try *
            iterables.append(parent.finalbody)
        for container in iterables:
            for node in list(container):
                if hasattr(node, 'body'):
                    ProgramLoader._recurse_tree(node, method, level=level + 1)
                if hasattr(node, 'handlers'):  # try, try *
                    for handler in node.handlers:
                        ProgramLoader._recurse_tree(
                            handler, method, level=level + 1
                        )
                method(node, container, level)

    @staticmethod
    def _ensure_raising_program_exit_from_try_except(tree):
        def recurse_method(node_, _container, level):
            if not isinstance(node_, ast.Try):
                return
            handler = ast.ExceptHandler(
                type=ast.Name(id=ProgramExit.__name__, ctx=ast.Load()),
                body=[ast.Raise()],
            )
            ast.copy_location(handler, node_)
            ast.fix_missing_locations(handler)
            node_.handlers.insert(0, handler)

        ProgramLoader._recurse_tree(tree, recurse_method)

    @staticmethod
    def _insert_start_and_end_program(tree, program_node):
        # robot program start
        program_start_call = ast.Call(
            func=ast.Name(id=rpl_program_start.__name__, ctx=ast.Load()),
            args=[],
            keywords=[],
        )
        newnode = ProgramLoader._insert_expr(program_start_call, tree.body[0])
        tree.body.insert(0, newnode)

        # main program start
        main_start_call = ast.Call(
            func=ast.Name(id=rpl_main_program_start.__name__, ctx=ast.Load()),
            args=[],
            keywords=[],
        )
        newnode = ProgramLoader._insert_expr(
            main_start_call, program_node.body[0]
        )
        program_node.body.insert(0, newnode)

        # main program end
        main_end_call = ast.Call(
            func=ast.Name(id=rpl_main_program_end.__name__, ctx=ast.Load()),
            args=[],
            keywords=[],
        )
        newnode = ProgramLoader._insert_expr(
            main_end_call, program_node.body[-1]
        )
        program_node.body.append(newnode)

        # main program end on exit
        def recurse_method(node_, container, level):
            if not (
                isinstance(node_, ast.Expr)
                and isinstance(node_.value, ast.Call)
                and isinstance(node_.value.func, ast.Name)
            ):
                return
            if node_.value.func.id != 'exit':
                return
            index = container.index(node_)
            newnode = ProgramLoader._insert_expr(main_end_call, node_)
            container.insert(index, newnode)

        ProgramLoader._recurse_tree(program_node, recurse_method)

    @staticmethod
    def _insert_expr(call, node):
        result = ast.Expr(value=call)
        ast.copy_location(result, node)
        ast.fix_missing_locations(result)
        return result

    @staticmethod
    def _insert_helper_function_calls(tree, program_node, path):
        import_from = ast.ImportFrom(
            module=__name__,
            names=[
                ast.alias(_query_status_helper.__name__, None),
                ast.alias(_update_reload_required_helper.__name__, None),
            ],
        )
        ast.copy_location(import_from, program_node)
        ast.fix_missing_locations(import_from)
        insert_pos = len(tree.body)
        # insert import on on first line which is not an import
        for i, node in enumerate(tree.body):
            if not isinstance(node, (ast.ImportFrom, ast.Import)):
                insert_pos = i
                break
        tree.body.insert(insert_pos, import_from)

        def insert_helper_call(node_, container, level):
            if level == 0 and not isinstance(
                node_, (ast.Assign, ast.Expr, ast.While, ast.For, ast.Pass)
            ):
                return
            call = ast.Call(
                func=ast.Name(id=_query_status_helper.__name__, ctx=ast.Load()),
                args=[
                    ast.Name(id=INTERPRETER_PROCESS_NAME, ctx=ast.Load()),
                    ast.Num(n=node_.lineno),
                    ast.Str(s=path),
                ],
                keywords=[],
            )
            newnode = ast.Expr(value=call)
            ast.copy_location(newnode, node_)
            ast.fix_missing_locations(newnode)
            index = container.index(node_)
            container.insert(index, newnode)

        ProgramLoader._recurse_tree(tree, insert_helper_call)

        # insert reload update call after last import
        insert_pos = -1
        for i, node in enumerate(tree.body):
            if isinstance(node, (ast.ImportFrom, ast.Import)):
                insert_pos = i
        if insert_pos >= 0:
            call = ast.Call(
                func=ast.Name(
                    id=_update_reload_required_helper.__name__, ctx=ast.Load()
                ),
                args=[ast.Name(id=INTERPRETER_PROCESS_NAME, ctx=ast.Load())],
                keywords=[],
            )
            newnode = ast.Expr(value=call)
            oldnode = tree.body[insert_pos]
            ast.copy_location(newnode, oldnode)
            ast.fix_missing_locations(newnode)
            tree.body.insert(insert_pos + 1, newnode)

    @staticmethod
    def _insert_register_on_abort_handler(tree, program_node):
        code = (
            'if "{name}" in globals().keys() and callable({name}):\n'
            '  {process}.{name}_handler = {name}\n'
            'else:'
            '  {process}.{name}_handler = lambda : None'
        )
        append_node = program_node
        for handler in ProgramLoader.HANDLER_METHOD_NAMES:
            if_node = ast.parse(
                code.format(process=INTERPRETER_PROCESS_NAME, name=handler)
            ).body[0]
            ast.copy_location(if_node, append_node)
            ast.fix_missing_locations(if_node)
            tree.body.append(if_node)
            append_node = if_node
