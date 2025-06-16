Tormach Robot Programming Language
==================================

The TRPL is based on Python. All commands interpreted by the TRPL interpreter
are Python code, which means you can use any Python code to control the robot.
However, the graphical conversational programming utility only supports
re-interpretation of a subset of commands as defined here.

.. contents:: Contents
    :local:
    :depth: 2

Program structure
-----------------

A TRPL program is a simple Python file with a single ``main`` function
containing the program code. The support RPL commands are imported per default;
any additional external libraries can be imported if required.

Note that the program interpreter only can track code execution in the main
program file. Blocking commands in external libraries might, therefore, lock up
the program execution

The main function is executed in a loop. If you want to break this behavior, use
the exit statement.

.. code-block:: python
   :linenos:

      from robot_command.rpl import *  # import all robot commands
      set_units("mm", "deg")  # set the linear and angular unit types for the program

      # waypoints are defined in the header of the program
      waypoint_1 = j[0.764, 1.64, 0.741, 0.433, 0.140, 2.74]
      waypoint_2 = p[361.53,947.19, 937.11, 45, 0, 0]

      # the main function contains the program code
      def main():
          movel(waypoint_1)  # a linear move command
          sleep(0.5)  # wait for 0.5 seconds
          movej(waypoint_2) # a joint move command
          sleep(0.5)  # wait for 0.5 seconds

Special Python Method Names
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following Python method names have a special meaning in the TRPL interpreter:

* **main**: The robot programs main loop. Required in every program.
* **on_abort**: Called when the program is aborted as a result of an error or controlled exit by the operator.
* **on_pause**: Called when the program is paused.

The **on_abort** and **on_pause** methods are useful for disabling digital outputs
or cleaning up initialized resources. If an error occurs in the **on_pause** method
**on_abort** will be called as a fallback. If an error occurs in the **on_abort** method
the program will exit instantly.

Python Stubs
^^^^^^^^^^^^^^^^^^^
Below you can find Python stub files, supported in most modern IDEs.

To use them, install the `robot_command-stubs` package by issuing
the `python3 setup.py install` command.

:download:`robot_command-stubs.zip <robot_command-stubs.zip>`

Linear and Angular Units
------------------------

The TRPL supports multiple linear and angular measurement units. It is advised
to define the units used in a program as the first line of the program. Changing
units at runtime is supported, but highly discouraged.

**Supported linear unit types:**

* “m” - Meters
* “mm” - Millimeters
* “in” - Inches

**Supported angular unit types:**

* “deg” - Degrees
* “rad” - Radians

.. autofunction:: robot_command.rpl.set_units
.. autofunction:: robot_command.rpl.get_units

Waypoints
---------

Waypoints are defined either as joint configuration, as list of joint positions,
or as a robot pose with location in Cartesian coordinates XYZ and orientation in
Euler angles ABC. Robot poses furthermore relate to a frame from the world
origin, usually located at the robot base. If no frame is active or specified
with the waypoint, reference to the world origin is assumed.

Global and Local Waypoints
^^^^^^^^^^^^^^^^^^^^^^^^^^

Global waypoints are waypoints that can be reused between programs. These
waypoints are referenced by name inside the TRPL. Contrary, local waypoints are
defined in the beginning of a robot program as Python variables.

Joints - Waypoint Defined as Joint Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Joint positions can be defined by using the :class:`~robot_command.rpl.Joints`
object or the :class:`~robot_command.rpl.JointsFactory` using the ``j[]``
shortcut. The values of **j1 to j6 are the six joint positions** of the robot
arm.

.. autoclass:: robot_command.rpl.Joints
   :members:
.. autoclass:: robot_command.rpl.JointsFactory
.. autofunction:: robot_command.rpl.get_joint_values

Pose - Waypoint Defined as Pose
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Poses can be defined using the :class:`~robot_command.rpl.Pose` object or the
:class:`~robot_command.rpl.PoseFactory` using the ``p[]`` shortcut. **x, y, z
are the Cartesian coordinates** of the robot position. **a, b, c is the
orientation defined in Euler angles (static XYZ)**.

Optionally, poses can be defined with a reference frame defined as frame in the
robot UI. When no frame is defined, it is assumed that the waypoint is defined
in world coordinates.

User frames are not enforced at runtime. You still need to use a
:func:`~robot_command.rpl.change_user_frame` statement before an frame becomes
active.

.. autoclass:: robot_command.rpl.Pose
   :members:
   :special-members: __mul__
.. autoclass:: robot_command.rpl.PoseFactory
.. autofunction:: robot_command.rpl.get_pose
.. autofunction:: robot_command.rpl.to_local_pose

Setting and getting global waypoints from robot programs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robot programs can *set* or *get* a global waypoint as part of its execution.
Setting of a new global waypoint is achieved by calling
:func:`robot_command.rpl.set_global_waypoint`. Getting of existing
global waypoints is accomplished by calling
:func:`robot_command.rpl.get_global_waypoint`.

.. autoclass:: robot_command.rpl.set_global_waypoint
.. autoclass:: robot_command.rpl.get_global_waypoint

Movement
---------

The robot can be moved using the following move types:

movej - Joint Move
^^^^^^^^^^^^^^^^^^
.. autofunction:: robot_command.rpl.movej

movel - Linear Move
^^^^^^^^^^^^^^^^^^^
.. autofunction:: robot_command.rpl.movel

movec - Circular Move
^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: robot_command.rpl.movec

movef - Free-form Move
^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: robot_command.rpl.movef

Trajectory Execution
^^^^^^^^^^^^^^^^^^^^
In same cases it is beneficial to execute a raw trajectory pre-planned in
another program, for example Maya Mimic. The robot program supports loading,
saving and executing such trajectories.

.. autofunction:: robot_command.rpl.load_trajectory
.. autofunction:: robot_command.rpl.save_trajectory
.. autofunction:: robot_command.rpl.execute_trajectory


**Examples**

.. code-block:: python

    trajectory = load_trajectory('test.csv')
    execute_trajectory(trajectory)
    save_trajectory('test2.csv', trajectory)

Glossary of Move Errors
^^^^^^^^^^^^^^^^^^^^^^^
Move commands typically fails due to two major reasons, either during planning
or during execution. You can catch those errors and retry a move inside the
robot program.

.. autoexception:: robot_command.rpl.MovePlanningError
.. autoexception:: robot_command.rpl.MoveExecutionError

**Examples**

.. code-block:: python

    try:
        movel(waypoint)
    except MovePlanningError:  # is raised in case of a planning error
        notify("Move planning failed", warning=True)

Path Blending
^^^^^^^^^^^^^

Joint moves as well as linear and circular moves can be blended together into
one continuous motion. This behavior can be enabled using the
:func:`~robot_command.rpl.set_path_blending` method. Note that the motion will
be executed before the next non-motion command. To force the execution of
blended commands, use the the :func:`~robot_command.rpl.sync` method.

.. autofunction:: robot_command.rpl.set_path_blending
.. autofunction:: robot_command.rpl.sync

User and Tool Frames
---------------------

The TRPL supports an arbitrary number of named user and tool frames. These
frames are usually defined in the robot UI, however, can also be set inside a
program.

User Frames
^^^^^^^^^^^^
.. autofunction:: robot_command.rpl.change_user_frame
.. autofunction:: robot_command.rpl.set_user_frame
.. autofunction:: robot_command.rpl.get_user_frame
.. autofunction:: robot_command.rpl.user_frame

Tool Frames
^^^^^^^^^^^^
.. autofunction:: robot_command.rpl.change_tool_frame
.. autofunction:: robot_command.rpl.set_tool_frame
.. autofunction:: robot_command.rpl.get_tool_frame

Digital I/O
-----------

Digital input/output pins can be accessed via their name or by their number.

.. autofunction:: robot_command.rpl.set_digital_out
.. autofunction:: robot_command.rpl.get_digital_in

PathPilot Remote
----------------

The PathPilot remote interface can be used to remotely control a PathPilot instance.

.. autofunction:: robot_command.rpl.pathpilot_cycle_start
.. autofunction:: robot_command.rpl.pathpilot_mdi
.. autofunction:: robot_command.rpl.get_pathpilot_state
.. autofunction:: robot_command.rpl.set_machine_frame

Notifications
-------------

The TRPL supports interactive user notifications displayed in the robot UI.

.. autofunction:: robot_command.rpl.notify
.. autofunction:: robot_command.rpl.input

Program Flow
------------

.. autofunction:: robot_command.rpl.sleep
.. autofunction:: robot_command.rpl.pause
.. function:: exit

    The Python builtin ``exit`` command instantly aborts the program execution.

    **Examples**

    .. code-block:: python

        exit()

Loops
^^^^^

The TRPL supports all Python statements, including loops.

**Examples**

.. code-block:: python

    # move through 4 points
    for i range(5):
        movel(Pose(x=i*0.1))
    # wait for a condition
    while get_digital_in("start") == False:
        sync()


Conditions
^^^^^^^^^^

Similarly, conditions are also supported.

**Examples**

.. code-block:: python

    if get_pathpilot_state() != "ready":
        notify("PathPilot is not ready", warning=True)


Subprograms
^^^^^^^^^^^

The TRPL supports subprograms / reusable Python functions.

**Examples**

.. code-block:: python

    def subprogram():
        movel(p[0, 100, 0, 0, 0, 0])

    def main():
        subprogram()


Persistent Parameter Storage
----------------------------

The TRPL supports storing and retrieving Python objects to the persistent
parameter store. This is useful if you want to store data between program runs.

.. autofunction:: robot_command.rpl.set_param
.. autofunction:: robot_command.rpl.get_param
.. autofunction:: robot_command.rpl.delete_param

Probing
-------
.. warning:: Under development

The ``probel`` command is a simple probing cycle:

.. autofunction:: robot_command.rpl.probel

When called, :func:`~robot_command.rpl.probel` executes two motions:

:func:`~robot_command.rpl.movel` towards a target position at specified
accelerations scale a (default 0.5), and velocity scale v (default 0.01),
stopping when the probe makes contact.

:func:`~robot_command.rpl.movel` to retract to the original position (at
velocity v_retract, default 0.1)

It’s also possible to create custom probing cycles by adding a “probe” keyword
to any of the following move commands:

* :func:`~robot_command.rpl.movej`
* :func:`~robot_command.rpl.movel`
* :func:`~robot_command.rpl.movec`

For example, a linear move that expects probe contact would look like this:

.. code-block:: python

    contact_type, contact_time, contact_joint_positions, contact_pose = movel(probe_goal_pose, probe=2)

The numerical value of the "probe" argument has the following meaning:

probe=2 means look for contact (rising edge), or raise a
:exc:`~robot_command.rpl.ProbeFailedError` if it reaches the end without making
contact, or if the probe is active at the start of the move.

probe=3 is like (2), but reaching the end of the motion is not an error.

probe=4 means look for the probe to break contact (falling edge). It raises a
:exc:`~robot_command.rpl.ProbeFailedError` if it reaches the end without
breaking contact, or if the probe is not active at the start.

probe=5 is like (4), but reaching the end of the motion is not an error.

probe=6 is for retraction. The motion will execute normally with the probe on or
off, but if the probe signal gets a rising edge (i.e. retracting from a surface
too far and hitting another surface), then it will raise a
:exc:`~robot_command.rpl.ProbeUnexpectedContactError`

.. note::

    if the probe fails to make contact in mode 3 (or leave contact in mode 5),
    movel will return “None” instead of a result tuple.

Glossary of Probe Errors
^^^^^^^^^^^^^^^^^^^^^^^^

There are several probing-specific errors that are reported as python
exceptions. All of them are derived from the
:exc:`~robot_command.rpl.ProbeError` exception class.


.. autoexception:: robot_command.rpl.ProbeUnexpectedContactError
.. autoexception:: robot_command.rpl.ProbeContactAtStartError
.. autoexception:: robot_command.rpl.ProbeFailedError

Interrupts
----------

The TRPL supports interrupts from external sources. This is useful for example
to abort a program when a button connected to a digital input pin is pressed
or to react to a message received from a ROS topic.

.. autoclass:: robot_command.rpl.InterruptSource
   :members:

.. autofunction:: robot_command.rpl.register_interrupt
.. autofunction:: robot_command.rpl.trigger_interrupt

Calibration
-----------

The :mod:`robot_command.calibration` module contains a few useful functions to
write custom calibration programs. Note that these functions must be imported
manually.

.. automodule:: robot_command.calibration
   :members:

List of Supported and Deprecated Commands
-----------------------------------------

* :func:`~robot_command.rpl.set_units`
* :func:`~robot_command.rpl.movel`
* :func:`~robot_command.rpl.movej`
* :func:`~robot_command.rpl.movec`
* :func:`~robot_command.rpl.movef`
* :func:`~robot_command.rpl.set_path_blending`
* :func:`~robot_command.rpl.get_pose`
* :func:`~robot_command.rpl.get_joint_values`
* :func:`~robot_command.rpl.get_digital_in`
* :func:`~robot_command.rpl.get_pathpilot_state`
* :func:`~robot_command.rpl.set_digital_out`
* :func:`~robot_command.rpl.sleep`
* :func:`~robot_command.rpl.pause`
* :func:`exit`
* :func:`~robot_command.rpl.pathpilot_mdi`
* :func:`~robot_command.rpl.pathpilot_cycle_start`
* :func:`~robot_command.rpl.notify`
* :func:`~robot_command.rpl.input`
* :func:`~robot_command.rpl.sync`

.. versionadded:: 0.1.3

* :func:`~robot_command.rpl.get_global_waypoint`
* :func:`~robot_command.rpl.set_global_waypoint`

.. versionadded:: 0.1.4

* :func:`~robot_command.rpl.get_param`
* :func:`~robot_command.rpl.set_param`
* :func:`~robot_command.rpl.get_pathpilot_state`
* :func:`~robot_command.rpl.get_units`

.. versionadded:: 0.2.2

* :func:`~robot_command.rpl.load_trajectory`
* :func:`~robot_command.rpl.save_trajectory`
* :func:`~robot_command.rpl.execute_trajectory`

.. versionadded:: 3.0.0

* :func:`~robot_command.rpl.to_local_pose`

.. versionadded:: 3.0.2

* :func:`~robot_command.rpl.change_user_frame`
* :func:`~robot_command.rpl.set_user_frame`
* :func:`~robot_command.rpl.get_user_frame`
* :func:`~robot_command.rpl.user_frame`
* :func:`~robot_command.rpl.change_tool_frame`
* :func:`~robot_command.rpl.set_tool_frame`
* :func:`~robot_command.rpl.get_tool_frame`
* :func:`~robot_command.rpl.set_machine_frame`
* :func:`~robot_command.rpl.register_interrupt`
* :func:`~robot_command.rpl.trigger_interrupt`

.. versionadded:: 3.0.5

* :func:`~robot_command.rpl.delete_param`

.. versionadded:: 3.1.1

* :func:`~robot_command.rpl.probel`

.. deprecated:: 3.0.2

* :func:`~robot_command.rpl.set_work_offset`
* :func:`~robot_command.rpl.set_tool_offset`
* :func:`~robot_command.rpl.get_work_offset`
* :func:`~robot_command.rpl.get_tool_offset`
* :func:`~robot_command.rpl.change_work_offset`
* :func:`~robot_command.rpl.change_tool_offset`
* :func:`~robot_command.rpl.set_machine_offset`
* :func:`~robot_command.rpl.work_offset`
