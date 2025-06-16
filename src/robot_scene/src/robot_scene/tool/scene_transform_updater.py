from ..scene_transform_updater_base import (
    SceneTransformUpdaterBase,
)


class SceneTransformUpdater(SceneTransformUpdaterBase):
    def __init__(self, tool_attach_link, tool_touch_links, ns=''):
        # cache_tfs == workaround for timestamp in the past warnings in move_group
        # when a transform attached to a planning frame is removed
        # see https://github.com/ros-planning/moveit/issues/1398
        super().__init__(ns, cache_tfs=True)

        self._tool_attach_link = tool_attach_link
        self._tool_touch_links = tool_touch_links

    def add_robot(self, description):
        self._update_finger_joints(description)
        self._publish_transforms(description)
        self._add_meshes(
            description,
            attached=True,
            link_name=self._tool_attach_link,
            touch_links=self._tool_touch_links,
        )

    def update_robot(self, description):
        self._update_finger_joints(description)
        self._publish_transforms(description)
        # self._update_meshes(description, attached=True, link_name="flange")

    def remove_robot(self, description):
        # note: removing individual tool meshes causes planning scene errors
        self._remove_all_attached_meshes(self._tool_attach_link)
        self._remove_meshes(description, attached=False)

    def stop(self):
        pass

    def _update_finger_joints(self, description):
        pass
