# modified version of https://github.com/micheleantonazzi/python-stub-runtime-generator
import inspect
from io import StringIO
from typing import List, Callable, Any, Union

import typing


class StubGenerator:
    """
    This class takes a file as input and generates the corresponding stub file for each defined type
    (generic variables, functions, classes, etc.) at run time.
    This means that the file is not statically parsed, but it is executed and
    then the types are dynamically created and analyzed to produce the stub file.
    The only items to be analyzed are those defined in the input file, while whose imported from other modules are ignored.
    To include members defined in other modules, you have to specify their names in the constructor.
    """

    def __init__(
        self,
        module,
        members_from_other_modules: List[str] = [],
        ignore_members: List[str] = [],
    ):
        """
        Initializes the StubGenerator.
        :param file_path: the file path
        :type file_path: str
        :param members_from_other_modules: the names of the members defined in other module to be analyzed
        :type members_from_other_modules: List[str]
        """
        self._file_path: str = module.__file__
        # if not os.path.exists(self._file_path):
        #     raise FileNotFoundError
        # loader = importlib.machinery.SourceFileLoader(
        #     module_name, self._file_path
        # )
        # spec = importlib.util.spec_from_loader(loader.name, loader)
        # module = importlib.util.module_from_spec(spec)
        # loader.exec_module(module)
        self._module = module

        # Check of the members from other modules are contained in the given file
        self._members: List[str] = []
        for item in members_from_other_modules:
            if item not in module.__dict__.keys():
                print(
                    'The member {} is not contained in the input file: it is ignored'.format(
                        item
                    ),
                )

        # Remove members that are not defined in self._file_path: all fields with module == None are defined in this file
        self._members += [
            item
            for item in module.__dict__.keys()
            if not item.startswith('_') and item not in ignore_members
            # if item in members_from_other_modules
            # or (
            #     not item.startswith('__')
            #     and inspect.getmodule(getattr(module, item)) == None
            # )
        ]
        # self._modules: List[str] = [
        #     getattr(module, item).__name__
        #     for item in module.__dict__.keys()
        #     if inspect.ismodule(getattr(module, item))
        # ]
        self._modules = set()
        self._stubs_strings: List[str] = []

    def _get_element_name_with_module(
        self, element: Union[type, Any], type_=None
    ) -> str:
        """
        Returns the element name with the relative module and adds the module to the imports (if it is not yet present)
        :param element: the element
        :return:
        :rtype: str
        """
        # The element can be a string, for example "def f() -> 'SameClass':..."
        if isinstance(element, str):
            if type_:
                element = type_
            else:
                return element

        if isinstance(element, type):
            return self._get_element_name_with_module_type_or_class(element)
        elif inspect.getmodule(element) == inspect.getmodule(typing):
            return self._get_element_name_with_module_typing(element)
        elif element is None:
            return "None"

    def _get_element_name_with_module_typing(self, element):
        module_name = str(element).split('.')[0]
        element_name = str(element).split('[')[0]
        args = []
        for arg in typing.get_args(element):
            arg_name = self._get_element_name_with_module(arg)
            args.append(arg_name.replace('NoneType', 'None'))

        self._modules.add(module_name)

        return f"{element_name}[{', '.join(args)}]"

    def _get_element_name_with_module_type_or_class(self, element):
        module = inspect.getmodule(element)
        if (
            module is None
            or module.__name__ == 'builtins'
            or module.__name__ == '__main__'
        ):
            return element.__name__

        module_name = module.__name__
        if module_name.startswith(self._module.__name__):
            # assume correct import of local elements
            return element.__name__

        self._modules.add(module_name)
        return f'{module_name}.{element.__name__}'

    def _generate_class_stub(self, name: str, clazz: type) -> str:
        """
        Generates the stub string for the given class
        :param name: the class name
        :type name: str
        :param clazz: the class to generate stub
        :type clazz: type
        :return: the str which contains the stub
        :rtype: str
        """
        buff = StringIO()

        # Class prototype
        buff.write('class ' + name.split('.')[-1] + '(')

        # Add super classes
        for c in clazz.__bases__:
            name_with_module = self._get_element_name_with_module(c)
            buff.write(name_with_module + ', ')

        # Add metaclass
        name_with_module = self._get_element_name_with_module(clazz.__class__)
        buff.write('metaclass=' + name_with_module + '):\n')

        for key, element in clazz.__dict__.items():
            if inspect.isfunction(element):
                buff.write(
                    self._generate_function_stub(key, element, indentation='\t')
                )

        buff.write('\t...\n')

        return buff.getvalue()

    def _generate_function_stub(
        self, name: str, func: Callable, indentation: str = ''
    ) -> str:
        """
        Generates the stub string for the given function
        :param name: the function name
        :type name: str
        :param func: the function to generate stub
        :type func: Callable
        :param indentation: the string used to correctly align the function stub
        :return: the str which contains the stub
        :rtype: str
        """

        def exploit_annotation(
            annotation: Any, starting: str = ': ', type_=None
        ) -> str:
            annotation_string = ''
            if annotation != inspect._empty:
                annotation_string += (
                    starting
                    + self._get_element_name_with_module(annotation, type_)
                )
            return annotation_string

        buff = StringIO()
        sign = inspect.signature(func)
        types = typing.get_type_hints(func)

        buff.write(indentation + 'def ' + name + '(')
        for i, (par_name, parameter) in enumerate(sign.parameters.items()):
            annotation = exploit_annotation(
                parameter.annotation, type_=types.get(par_name)
            )
            default = ''
            if (
                parameter.default != parameter.empty
                and type(parameter.default).__module__ == 'builtins'
                and not str(parameter.default).startswith('<')
            ):
                default = (
                    ' = ' + str(parameter.default)
                    if not isinstance(parameter.default, str)
                    else ' = \'' + parameter.default + '\''
                )

            buff.write(par_name + annotation + default)

            if i < len(sign.parameters) - 1:
                buff.write(', ')
        ret_annotation = exploit_annotation(
            sign.return_annotation,
            starting=' -> ',
            type_=types.get('return', None),
        )
        buff.write(')' + ret_annotation + ':\n')

        if func.__doc__ is not None:
            buff.write(indentation + '\t"""\n')
            for line in func.__doc__.split('\n')[1:-1]:
                buff.write(indentation + '\t' + line.strip().rstrip() + '\n')
            buff.write(indentation + '\t\"\"\"\n')
        buff.write(indentation + '\t...\n')
        return buff.getvalue()

    def _generate_generic_stub(self, element_name: str, element: Any) -> str:
        """
        Generates the stub for a generic variable
        :param element_name: the name of the element
        :type element_name: str
        :param element: the element
        :type element: Any
        :return: the stub as a string
        :rtype: str
        """
        return '{}: {}\n'.format(
            element_name, self._get_element_name_with_module(type(element))
        )

    def get_stubs(self) -> List[str]:
        """
        Returns a list containing the generated stub strings
        :return: a list containing the generated stub strings
        :rtype: List[str]
        """
        return self._stubs_strings

    def generate_stubs(self) -> 'StubGenerator':
        """
        Generates the stubs for the types collected in the input file
        :return: the stub generator
        :rtype StubGenerator
        """
        for member_name in self._members:
            attr = getattr(self._module, member_name)
            if inspect.isclass(attr):
                self._stubs_strings.append(
                    self._generate_class_stub(member_name, attr)
                )
            elif inspect.isfunction(attr):
                self._stubs_strings.append(
                    self._generate_function_stub(member_name, attr)
                )
            elif not inspect.ismodule(attr):
                self._stubs_strings.append(
                    self._generate_generic_stub(member_name, attr)
                )

        return self

    def write_to_file(self, file_path=None):
        """
        Writes the stub files in the same location as the input file
        :return: None
        """
        file_path = file_path or self._file_path + 'i'
        with open(file_path, mode='w') as f:
            f.write(
                '#######################################################\n'
                '# This stub is autogenerated\n'
                '########################################################\n\n'
            )
            for module in self._modules:
                f.write('import ' + module + '\n')
            f.write('\n\n')
            for stub in self._stubs_strings:
                f.write(stub + '\n')
