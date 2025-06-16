import sys
import os
from typing import Dict


class ReloadChecker:
    def __init__(self):
        self._module_timestamps = {}
        self._modified = False

    @property
    def modified(self):
        return self._modified

    def _get_module_timestamp(self, module):
        try:
            file_path = module.__file__
            if not file_path.endswith("__init__.py"):
                # For a single file module, return its timestamp.
                return os.path.getmtime(file_path)
            # If it's a package, get the newest timestamp in the folder.
            folder_path = os.path.dirname(file_path)
            return max(
                os.path.getmtime(os.path.join(folder_path, f))
                for f in os.listdir(folder_path)
            )
        except AttributeError:
            # If the module doesn't have a __file__ attribute, return None.
            return None

    def _query_modules(self):
        timestamps = {}
        for module in sys.modules.values():
            if timestamp := self._get_module_timestamp(module):
                timestamps[module.__name__] = timestamp
        return timestamps

    def _compare_module_runs(
        self, timestamps: Dict[str, float], other_timestamps: Dict[str, float]
    ):
        return [
            module_name
            for module_name, timestamp in timestamps.items()
            if (
                module_name in other_timestamps
                and other_timestamps[module_name] != timestamp
            )
        ]

    def _update_module_timestamps(self, new_timestamps: Dict[str, float]):
        for module_name, timestamp in new_timestamps.items():
            if module_name in self._module_timestamps:
                # Keep the oldest timestamp.
                self._module_timestamps[module_name] = min(
                    self._module_timestamps[module_name], timestamp
                )
            else:
                self._module_timestamps[module_name] = timestamp

    def update(self):
        if self._modified:
            return  # no need to update if already modified
        timestamps = self._query_modules()
        modified_modules = self._compare_module_runs(
            self._module_timestamps, timestamps
        )
        self._update_module_timestamps(timestamps)
        self._modified = len(modified_modules) > 0

    def reset(self):
        self._module_timestamps = {}
        self._modified = False
