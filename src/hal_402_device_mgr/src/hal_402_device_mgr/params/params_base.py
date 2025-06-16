import os
import sys
import ruamel.yaml
import rospy
import rosgraph
import rospkg
from .ecat_types import EtherCATTypes
from .sdo import EtherCATSDO
from .xml_reader import EtherCATXMLReader
from .logging import Logging


class EtherCATParamsBase:
    param_top_level_key = 'ethercat_drive_params'

    def __init__(self, master=None, positions=None):
        self.master = master
        self.positions = positions
        self.logger = Logging.getLogger(__name__)

    @classmethod
    def sdos_from_model_id(cls, model_id):
        return EtherCATXMLReader.sdos(model_id)

    def setup(self, model_id):
        self.model_id = model_id
        # This hack passes enough context to parse SDOs in from_yaml
        self.yaml.constructor.model_id = self.model_id
        self._params = self.yaml.map()

    @classmethod
    def rosparams_xml_path(cls, group):
        """Find XML drive description file path from rosparams"""
        if not rosgraph.is_master_online():
            raise ConnectionRefusedError(
                "Unable to read ROS params:  Master offline"
            )
        rosparam_key = f"{cls.param_top_level_key}/{group}"
        file_data = rospy.get_param(rosparam_key, {})
        ros_pkg = file_data.get('ros_package', None)
        rel_fname = file_data.get('path', None)

        if None in (ros_pkg, rel_fname):
            return None
        fname = os.path.join(rospkg.RosPack().get_path(ros_pkg), rel_fname)
        return fname

    def read_xml(self, fname):
        if hasattr(self, 'sdos'):
            return
        self.xml_fname = fname
        self.xml_reader = EtherCATXMLReader()
        self.xml_reader.add_device_descriptions(fname)
        self.sdos = self.sdos_from_model_id(self.model_id)

    def read(self):
        # Subclasses implement this to build sdos attribute
        # Should call self.setup(name) and self.read_xml(fname)
        pass

    @classmethod
    def copy(cls, src, *newargs, **newkwargs):
        # Create new instance with usual args
        dst = cls(*newargs, **newkwargs)
        # Duplicate old instance data non-destructively
        newdict = dst.__dict__.copy()
        dst.__dict__.update(src.__dict__)
        dst.__dict__.update(newdict)
        # Duplicate old instance params
        dst._params.update(src._params)
        # Verify src and dst positions are same length
        if len(src.positions) != len(dst.positions):
            raise ValueError('Source and dest positions must have same number')
        return dst

    # ****************** Getters

    def get_sdo(self, *args):
        # Key may be EtherCATSDO object, (index, subindex), or 'XXXX-YYh' str
        if isinstance(args[0], EtherCATSDO):
            sdo = args[0]
        elif isinstance(args[0], str):
            sdo_ix = self.parse_sdo(args[0])
            sdo = self.sdos[sdo_ix]
        else:
            sdo = self.sdos[args]
        return sdo

    def get(self, *args, positions=None):
        sdo = self.get_sdo(*args)

        # Positions may be None (all drives), an int (one drive) or list of ints
        if positions is None:
            positions = self.positions
        elif isinstance(positions, int):
            positions = [positions]

        vals = self._params[sdo]
        if not isinstance(vals, list):
            vals = [vals] * len(self.positions)
        # Both self.positions and positions may be sparse
        val_map = dict(zip(self.positions, vals))
        return [val_map[k] for k in positions]

    # ****************** Setters

    def _compress_or_flow(self, sdo, vals):
        # For human readability, set flow for lists and condense
        # arrays of identical elements into a scalar
        for i in range(1, len(vals)):
            if vals[0] != vals[i]:
                seq = self.yaml.seq([sdo.data_type(i) for i in vals])
                seq.fa.set_flow_style()
                return seq
        else:
            return sdo.data_type(vals[0])

    def set(self, *args, positions=None):
        vals = args[-1]
        # Key may be EtherCATSDO object or index, subindex
        if isinstance(args[0], EtherCATSDO):
            sdo = args[0]
        else:
            sdo = self.sdos.from_index(*args[:-1])

        # Positions may be None (all drives), an int (one drive) or list of ints
        if positions is None:
            positions = self.positions
        elif isinstance(positions, int):
            positions = [positions]
        # Vals may be scalar (one drive) or list
        if not isinstance(vals, list):
            vals = [vals] * len(positions)

        # Current values may be sparse and/or missing
        val_map = dict(
            zip(
                self.positions,
                self._params.get(sdo, [None] * len(self.positions)),
            )
        )
        val_map.update(zip(positions, vals))
        self._params[sdo] = self._compress_or_flow(sdo, list(val_map.values()))

    # ****************** Dumpers

    def add_comments(self):
        prev_parent_comment = None
        for sdo in self._params:
            # Add param description before line
            prefix = '    ' if prev_parent_comment else ''
            if sdo.parent_comment != prev_parent_comment:
                prev_parent_comment = sdo.parent_comment
                if sdo.parent_comment:
                    prefix = '*** ' + sdo.parent_comment + ' ***\n    '
                else:
                    prefix = ''
            comment = prefix + (sdo.comment_name or '')
            self._params.yaml_set_comment_before_after_key(sdo, comment)

            # Add param type at end of line
            self._params.yaml_add_eol_comment(sdo.data_type.name, sdo, column=0)

    def dump(self, add_comments=True):
        if add_comments:
            self.add_comments()
        self.yaml.dump(self._params, sys.stdout)

    # ****************** YAML handling

    yaml_tag = 'tag:yaml.org,2002:ec_sdo'

    @property
    def yaml(self):
        if hasattr(self, '_yaml'):
            return self._yaml
        self._yaml = yaml = ruamel.yaml.YAML()
        yaml.default_flow_style = False
        self.register_yaml(yaml)
        EtherCATTypes.register_yaml(yaml)
        return yaml

    @classmethod
    def register_yaml(cls, yaml):
        yaml.register_class(EtherCATSDO)
        # The `style=''` is ignored
        yaml.representer.add_representer(
            EtherCATSDO,
            lambda representer, data: representer.represent_scalar(
                'tag:yaml.org,2002:str', str(data), style=''
            ),
        )
        ruamel.yaml.add_implicit_resolver(cls.yaml_tag, EtherCATSDO.sdo_re)

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_scalar(
            'tag:yaml.org,2002:ec_sdo', str(node)
        )

    @classmethod
    def from_yaml(cls, constructor, node):
        # Retrieve SDOs using context stashed in the YAML constructor object
        sdos = cls.sdos_from_model_id(constructor.model_id)
        index, subindex = EtherCATSDO.parse_sdo(node.value)
        print('value', node.value, 'sdo', sdos.from_index(index, subindex))
        return sdos.from_index(index, subindex)

    @classmethod
    def parse_sdo(cls, sdo_str):
        return tuple(EtherCATSDO.parse_sdo(sdo_str))
