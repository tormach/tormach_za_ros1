import os
import rospkg
from .params_base import EtherCATParamsBase


class EtherCATYAMLParams(EtherCATParamsBase):
    def __init__(self, yaml_fname, group, *args, **kwargs):
        self.yaml_fname = yaml_fname
        self.group = group
        super().__init__(*args, **kwargs)

    def load_all_params(self):
        with open(self.yaml_fname) as f:
            data = self.yaml.load(f)
        return data[self.param_top_level_key]

    yaml_attributes = (
        'device_id',
        'device_description_xml',
        'master',
        'positions',
        'param_values',
    )

    def read(self):
        all_params = self.load_all_params()
        group_params = all_params.get(self.group, None)

        # Extract some attributes from the YAML
        if group_params is None:
            raise RuntimeError(
                f"No {self.param_top_level_key}/{self.group} params found"
            )
        for attr in self.yaml_attributes:
            if attr not in group_params:
                raise RuntimeError(
                    f"No '{attr}' key in drive group {self.group}"
                )
            setattr(self, attr, group_params[attr])

        model_id = (self.device_id["vendor_id"], self.device_id["product_code"])
        self.setup(model_id)

        # Read XML
        ros_pkg = self.device_description_xml['ros_package']
        rel_fname = self.device_description_xml['path']
        fname = os.path.join(rospkg.RosPack().get_path(ros_pkg), rel_fname)
        self.read_xml(fname)

        # Read params
        for key, val in self.param_values.items():
            sdo = self.sdos[self.parse_sdo(key)]
            self.set(sdo, val)
