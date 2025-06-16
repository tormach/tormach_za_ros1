import pytest


@pytest.fixture
def simple_robot_description():
    return '''\
<?xml version="1.0"?>
<robot name="simple_robot">
  <link name="base_link" />
  <link name="link_1" />
  <link name="link_2" />

  <joint name="joint_1" type="revolute">
    <limit lower="-472.56" upper="666.94" velocity="599.34"/>
    <parent link="base_link"/>
    <child link="link_1"/>
    <axis xyz="0 0 1"/>
  </joint>

  <joint name="joint_2" type="revolute">
    <limit lower="-851.17" upper="623.52" velocity="367.94"/>
    <parent link="link_1"/>
    <child link="link_2"/>
    <axis xyz="0 1 0"/>
  </joint>

</robot>
'''


@pytest.fixture
def multi_robot_description():
    return '''\
<?xml version="1.0"?>
<robot name="multi_robot">
  <link name="base_link" />
  <link name="cnc_base" />
  <link name="cnc_1" />
  <link name="cnc_2" />

  <joint name="cnc_joint_1" type="linear">
    <parent link="cnc_base" />
    <child link="cnc_1" />
  </joint>

  <joint name="cnc_joint_2" type="linear">
    <parent link="cnc_1" />
    <child link="cnc_2" />
  </joint>

  <link name="robot_base" />
  <link name="link_1" />
  <link name="link_2" />
  <link name="link_3" />

  <joint name="joint_1" type="revolute">
    <limit lower="-210.53" upper="453.07" velocity="138.44"/>
    <parent link="robot_base"/>
    <child link="link_1"/>
  </joint>

  <joint name="joint_2" type="revolute">
    <limit lower="-849.80" upper="473.67" velocity="658.57"/>
    <parent link="link_1"/>
    <child link="link_2"/>
  </joint>

</robot>
'''


@pytest.fixture
def multi_joint_description():
    return '''\
<?xml version="1.0"?>
<robot name="multi_joint">
  <link name="base_link" />
  <link name="link_1" />
  <link name="link_2" />

  <joint name="joint_1" type="revolute">
    <parent link="base_link" />
    <child link="link_1" />
  </joint>

  <joint name="joint_2" type="fixed">
    <parent link="base_link" />
    <child link="link_2" />
  </joint>
</robot>
'''
