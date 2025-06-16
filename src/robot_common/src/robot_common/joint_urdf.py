from collections import namedtuple, defaultdict, OrderedDict
from math import pi

import rospy
import xml.dom.minidom

JointNode = namedtuple('JointNode', 'child data axis name')
JointEntry = namedtuple('JointEntry', 'minimum maximum zero type_')


def read_urdf(robot, base_link):
    robot = robot.getElementsByTagName('robot')[0]
    joint_map = defaultdict(list)
    joint_order = []

    # Find all non-fixed joints
    for child in robot.childNodes:
        if child.nodeType is child.TEXT_NODE:
            continue
        if child.localName != 'joint':
            continue

        parent_link = None
        child_link = None
        axis = None
        for sub_child in child.childNodes:
            if sub_child is sub_child.TEXT_NODE:
                continue
            if sub_child.localName == 'parent':
                parent_link = sub_child.getAttribute('link')
            elif sub_child.localName == 'child':
                child_link = sub_child.getAttribute('link')
            elif sub_child.localName == 'axis':
                axis = sub_child.getAttribute('xyz')

        if not (parent_link and child_link):
            rospy.logerr('Link without parent and child is not supported')
            continue

        name = child.getAttribute('name')
        node = JointNode(child=child_link, data=child, axis=axis, name=name)
        joint_map[parent_link].append(
            JointNode(child=child_link, data=child, axis=axis, name=name)
        )
        joint_order.append(node)

    if base_link:
        joint_order = []
        if base_link not in joint_map:
            rospy.logerr('Base link not found in URDF')
            return
        next_link = base_link

        def find_next(next_):
            if next_ not in joint_map:
                return
            for node_ in joint_map[next_]:
                joint_order.append(node_)
                next_link_ = node_.child
                find_next(next_link_)

        find_next(next_link)

    for node in joint_order:
        # read type and name
        jtype = node.data.getAttribute('type')
        if jtype == 'fixed' or jtype == 'floating':
            continue
        yield node


def read_robot_description(base_link):
    description = rospy.get_param('robot_description', None)
    if not description:
        rospy.logerr('No robot description found')
        return

    robot = xml.dom.minidom.parseString(description)
    if robot.getElementsByTagName('COLLADA'):
        rospy.logwarn('Collada not supported')
    else:
        yield from read_urdf(robot, base_link)


def read_robot_description_free_joints(
    base_link,
    joint_name_prefix,
    use_small=True,
    use_mimic=True,
    dependent_joints=None,
    zeros=None,
):
    if dependent_joints is None:
        dependent_joints = []
    free_joints = OrderedDict()

    for node in read_robot_description(base_link):
        child = node.data
        jtype = child.getAttribute('type')
        name = child.getAttribute('name')

        if joint_name_prefix and not name.startswith(joint_name_prefix):
            continue

        # read min/max value
        if jtype == 'continuous':
            minval = -pi
            maxval = pi
        else:
            try:
                limit = child.getElementsByTagName('limit')[0]
                minval = float(limit.getAttribute('lower'))
                maxval = float(limit.getAttribute('upper'))
            except AttributeError:
                rospy.logwarn(
                    f"{name} is not fixed, nor continuous, but limits are not specified!"
                )
                continue

        # read tags
        safety_tags = child.getElementsByTagName('safety_controller')
        if use_small and any(safety_tags):
            tag = safety_tags[0]
            if tag.hasAttribute('soft_lower_limit'):
                minval = max(
                    minval, float(tag.getAttribute('soft_lower_limit'))
                )
            if tag.hasAttribute('soft_upper_limit'):
                maxval = min(
                    maxval, float(tag.getAttribute('soft_upper_limit'))
                )

        mimic_tags = child.getElementsByTagName('mimic')
        if use_mimic and any(mimic_tags):
            tag = mimic_tags[0]
            entry = {'parent': tag.getAttribute('joint')}
            if tag.hasAttribute('multiplier'):
                entry['factor'] = float(tag.getAttribute('multiplier'))
            if tag.hasAttribute('offset'):
                entry['offset'] = float(tag.getAttribute('offset'))

            dependent_joints[name] = entry
            continue

        if name in dependent_joints:
            continue

        if zeros and name in zeros:
            zeroval = zeros[name]
        elif minval > 0.0 or maxval < 0.0:
            zeroval = (maxval + minval) / 2.0
        else:
            zeroval = 0.0

        free_joints[name] = JointEntry(
            minimum=minval,
            maximum=maxval,
            zero=zeroval,
            type_=jtype,
        )

    return free_joints
