import re


class EtherCATTypes:
    # Map ETG.1020 type name to object
    _name_registry = dict()
    _etg1020_re_registry = dict()
    _igh_type_registry = dict()

    def __init_subclass__(cls, /, **kwargs):
        cls._name_registry[cls.name] = cls
        re_compiled = re.compile(r'^' + cls.etg1020_re + r'$')
        cls._etg1020_re_registry[re_compiled] = cls
        cls._igh_type_registry[cls.igh_type] = cls

    def __new__(cls, raw_val, *args, **kwargs):
        if isinstance(raw_val, bytes):
            # Convert from IgH `ethercat upload` output
            val = cls.ethercat_util_to_py_conv(raw_val)
        else:
            val = raw_val
        # print(cls.name, 'val', val, 'raw_val', raw_val, 'args', args, 'kwargs', kwargs)
        return cls.base_type.__new__(cls, val, *args, **kwargs)

    @classmethod
    def get_etg1020_type(cls, name):
        for test_re, test_cls in cls._etg1020_re_registry.items():
            if test_re.match(name):
                return test_cls
        raise KeyError(f'Unknown ETG.1020 type "{name}"')

    @classmethod
    def is_etg1020_base_type(cls, name):
        for test_re, test_cls in cls._etg1020_re_registry.items():
            if test_re.match(name):
                return True
        return False

    @classmethod
    def get_igh_type(cls, name):
        if name not in cls._igh_type_registry:
            raise KeyError(f'Unknown IgH EtherCAT type "{name}"')
        return cls._igh_type_registry[name]

    @classmethod
    def all_types(cls):
        return cls._name_registry.values()

    def __str__(self):
        return str(self.base_type(self))

    @classmethod
    def register_yaml(cls, yaml):
        # FIXME It would be great to use `add_path_resolver` in
        # conjunction with `xml_reader.EtherCATXMLReader` to
        # automatically pick a representer based on SDO value
        for t in cls.all_types():
            yaml.register_class(t)
            yaml.representer.add_representer(
                t, yaml.representer.yaml_representers[t.base_type]
            )

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_scalar(cls.yaml_tag, str(node))


class EtherCATBOOL(EtherCATTypes, int):
    # 1 Boolean '0' or '1'
    # (Python bool can't be subclassed, so make it bool-like :P)
    name = 'BOOL'
    etg1020_re = r'BOOL|BIT'
    igh_type = 'bool'
    base_type = int
    num_bits = 1
    yaml_tag = 'tag:yaml.org,2002:ec_bool'
    dump_tag = 'tag:yaml.org,2002:bool'

    @staticmethod
    def ethercat_util_to_py_conv(x):
        return bool(int(x.split(b' ')[1]))

    def __bool__(self):
        return self != 0

    def __str__(self):
        # Print as boolean
        return str(bool(self))


class EtherCATINT(EtherCATTypes, int):
    # 16 Integer / Word
    name = 'INT'
    etg1020_re = r'INT'
    igh_type = 'int16'
    base_type = int
    num_bits = 16
    yaml_tag = 'tag:yaml.org,2002:ec_int16'
    dump_tag = 'tag:yaml.org,2002:int'

    def ethercat_util_to_py_conv(x):
        return int(x.split(b' ')[1])


class EtherCATSINT(EtherCATINT):
    # 8 Short Integer
    name = 'SINT'
    etg1020_re = r'SINT'
    igh_type = 'int8'
    num_bits = 8
    yaml_tag = 'tag:yaml.org,2002:ec_int8'


class EtherCATDINT(EtherCATINT):
    # 32 Double Integer
    name = 'DINT'
    etg1020_re = r'DINT'
    igh_type = 'int32'
    num_bits = 32
    yaml_tag = 'tag:yaml.org,2002:ec_int32'


class EtherCATLINT(EtherCATINT):
    # 64 Long Integer
    name = 'LINT'
    etg1020_re = r'LINT'
    igh_type = 'int64'
    num_bits = 64
    yaml_tag = 'tag:yaml.org,2002:ec_int64'


class EtherCATUINT(EtherCATINT):
    # 16 Unsigned Integer / Word
    name = 'UINT'
    etg1020_re = r'UINT'
    igh_type = 'uint16'
    num_bits = 16
    yaml_tag = 'tag:yaml.org,2002:ec_uint16'

    def __str__(self):
        # Print unsigned ints in hex representation
        fmt = '0x{0:0%dX}' % int(self.num_bits / 4)
        return fmt.format(self)


class EtherCATUSINT(EtherCATUINT):
    # 8 Unsigned Short Integer
    name = 'USINT'
    etg1020_re = r'USINT'
    igh_type = 'uint8'
    num_bits = 8
    yaml_tag = 'tag:yaml.org,2002:ec_uint8'


class EtherCATUDINT(EtherCATUINT):
    # 32 Unsigned Double Integer
    name = 'UDINT'
    etg1020_re = r'UDINT'
    igh_type = 'uint32'
    num_bits = 32
    yaml_tag = 'tag:yaml.org,2002:ec_uint32'


class EtherCATULINT(EtherCATUINT):
    # 64 Unsigned Long Integer
    name = 'ULINT'
    etg1020_re = r'ULINT'
    igh_type = 'uint64'
    num_bits = 64
    yaml_tag = 'tag:yaml.org,2002:ec_uint64'


class EtherCATREAL(EtherCATTypes, float):
    # 32 Floating point
    # Never seen in the wild
    name = 'REAL'
    etg1020_re = r'REAL'
    igh_type = 'float'
    base_type = float
    num_bits = 32
    yaml_tag = 'tag:yaml.org,2002:ec_float'
    dump_tag = 'tag:yaml.org,2002:float'

    def ethercat_util_to_py_conv(x):
        return float(x.split(b' ')[1])


class EtherCATLREAL(EtherCATREAL):
    # 64 Long float
    # Never seen in the wild
    name = 'LREAL'
    etg1020_re = r'LREAL'
    igh_type = 'double'
    num_bits = 64
    yaml_tag = 'tag:yaml.org,2002:ec_double'


# STRING TYPES
class EtherCATSTRING(EtherCATTypes, str):
    # Sequence of octets
    name = 'STRING'
    etg1020_re = r'STRING\([0-9]+\)'
    igh_type = 'string'
    base_type = str
    num_bits = None  # Variable length
    yaml_tag = 'tag:yaml.org,2002:ec_str'
    dump_tag = 'tag:yaml.org,2002:str'

    def ethercat_util_to_py_conv(x):
        return x.decode()

    def __str__(self):
        return self


# ETG.2000 defines other types
