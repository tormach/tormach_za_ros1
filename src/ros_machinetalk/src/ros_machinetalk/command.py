import inspect
import time

import actionlib
import rospy
from pymachinetalk.application import ApplicationCommand
from ros_machinetalk_msgs.msg import (
    CommandAction,
    CommandGoal,
    CommandFeedback,
    CommandResult,
)


class CommandBase:
    """Base class for translating Machinetalk commands to ROS actions and
    Machinetalk calls
    """

    _action_name = "command"

    # Scraped from pymachinetalk/application/command.py
    _cmds_by_name = dict(
        abort=dict(args='interpreter'),
        run_program=dict(args=('line_number', 'interpreter')),
        pause_program=dict(args='interpreter'),
        step_program=dict(args='interpreter'),
        resume_program=dict(args='interpreter'),
        set_task_mode=dict(args=('mode', 'interpreter')),
        set_task_state=dict(args=('state', 'interpreter')),
        open_program=dict(args=('file_name', 'interpreter')),
        reset_program=dict(args='interpreter'),
        execute_mdi=dict(args=('command', 'interpreter')),
        set_spindle_brake=dict(args='brake'),
        set_debug_level=dict(args='debug_level'),
        set_feed_override=dict(args='scale'),
        set_flood_enabled=dict(args='enable'),
        home_axis=dict(args='index'),
        jog=dict(args=('jog_type', 'axis', 'velocity', 'distance')),
        load_tool_table=dict(),
        update_tool_table=dict(args='tool_table'),
        set_maximum_velocity=dict(args='velocity'),
        set_mist_enabled=dict(args='enable'),
        override_limits=dict(),
        set_adaptive_feed_eanbled=dict(args='enable'),
        set_analog_output=dict(args=('index', 'value')),
        set_block_delete_enabled=dict(args='enable'),
        set_digital_output=dict(args=('index', 'enable')),
        set_feed_hold_enabled=dict(args='enable'),
        set_feed_override_enabled=dict(args='enable'),
        set_axis_max_position_limit=dict(args=('axis', 'value')),
        set_axis_min_position_limit=dict(args=('axis', 'value')),
        set_optional_stop_enabled=dict(args='enable'),
        set_spindle_override_enabled=dict(args='enable'),
        set_spindle=dict(args=('mode', 'velocity')),
        set_spindle_override=dict(args='scale'),
        set_teleop_enabled=dict(args='enable'),
        set_teleop_vector=dict(args=('a', 'b', 'c', 'u', 'v', 'w')),
        set_tool_offset=dict(
            args=(
                'index',
                'zoffset',
                'xoffset',
                'diameter',
                'frontangle',
                'backangle',
                'orientation',
            )
        ),
        set_trajectory_mode=dict(args='mode'),
        unhome_axis=dict(args='index'),
        shutdown=dict(),
    )
    _cmds_by_id = dict()

    _id = _key = _item = _msg_type_id = None
    for _id, _key in enumerate(sorted(_cmds_by_name.keys())):
        _item = _cmds_by_name[_key]
        # Put cmd name in data
        _item['cmd_name'] = _key
        # Normalize args
        if not isinstance(_item.setdefault('args', tuple()), tuple):
            _item['args'] = tuple([_item['args']])

        _msg_type_id = _item['msg_type_id'] = _id

        # Build up _cmds_by_id hash
        _cmds_by_id[_msg_type_id] = _item
    del _id, _key, _item, _msg_type_id

    def _cmd_id(self, cmd_name_or_id):
        if isinstance(cmd_name_or_id, str):
            return self._cmds_by_name[cmd_name_or_id]['msg_type_id']
        else:
            return cmd_name_or_id

    def _cmd_name(self, cmd_name_or_id):
        if isinstance(cmd_name_or_id, str):
            return cmd_name_or_id
        else:
            return self._cmds_by_id[cmd_name_or_id]['cmd_name']

    def _cmd_data(self, cmd_name_or_id):
        """Return command data given a command name or ID"""
        return self._cmds_by_id[self._cmd_id(cmd_name_or_id)]

    @staticmethod
    def _map_optional_args(cmd_name, kwargs):
        """If the API has optional arguments we try to map them."""
        a = inspect.getargspec(getattr(ApplicationCommand, cmd_name))
        a.args.pop(0)
        if not a.defaults:
            return len(kwargs) == len(a.args)
        non_kw_args = a.args[: -len(a.defaults)]
        passed_args = kwargs.copy()
        for arg in non_kw_args[:]:
            if arg in passed_args:
                non_kw_args.remove(arg)
                del passed_args[arg]
        if non_kw_args:
            return False
        defaults = dict(zip(a.args[-len(a.defaults) :], a.defaults))
        for key in defaults.keys():
            if key not in kwargs:
                kwargs[key] = defaults[key]
        return True

    def _args_to_kwargs(self, cmd, *args):
        """Translate positional args to kwargs for a particular command"""
        if len(args) == 0:
            return {}
        arg_keys = self._cmd_data(cmd)['args']
        kwargs = dict(zip(arg_keys, args))
        if len(args) != len(arg_keys):
            valid = self._map_optional_args(
                self._cmd_data(cmd)['cmd_name'], kwargs
            )
            if not valid:
                raise TypeError(
                    '%s() takes exactly %d arguments (%d given)'
                    % (cmd, len(arg_keys), len(args))
                )
        return kwargs


class CommandServer(CommandBase):
    DEFAULT_CMD_TIMEOUT_S = 6.0
    CMD_WAIT_INTERVAL_S = 0.2
    CMD_WAIT_NOTIFY_INTERVAL_S = 2.0

    def __init__(
        self,
        service_discovery,
        status_cb=None,
        debug=False,
        cmd_timeout=DEFAULT_CMD_TIMEOUT_S,
    ):
        self.sd = service_discovery
        self.status_cb = status_cb
        self.debug = debug
        self.cmd_timeout = cmd_timeout

        # Set up Machinetalk
        self.ac = ApplicationCommand(debug=self.debug)
        # self.ac = ApplicationCommand(debug=5)
        self.ac.on_state_changed.append(self._state_changed_cb)
        self.sd.register(self.ac)

        # ROS command server
        self.a_s = actionlib.SimpleActionServer(
            self._action_name,
            CommandAction,
            execute_cb=self._execute_cb,
            auto_start=False,
        )
        self.a_s.start()

    def _state_changed_cb(self, state):
        rospy.loginfo("Command channel state changed to %s" % state)
        rospy.loginfo(
            "Command channel connected=%s; uri=%s"
            % (self.ac.connected, self.ac.command_uri)
        )
        if self.status_cb:
            self.status_cb(self.ac.connected)

    def _execute_cb(self, goal):
        # Send goal command to command channel
        ticket = self.send_command_from_goal(goal)
        if ticket is None:
            text = "Sending command failed: received empty ticket"
            rospy.logerr(text)
            self.a_s.set_aborted(CommandResult(False, text))
            return
        rospy.loginfo("Sent command %d; ticket %s" % (goal.cmd_id, ticket))

        # Wait for command to complete
        start_time = notify_time = time.time()
        while not self.ac.wait_completed(
            ticket, timeout=self.CMD_WAIT_INTERVAL_S
        ):
            # Handle preemption
            if self.a_s.is_preempt_requested():
                rospy.loginfo(
                    f'{self._action_name}: Preempted command {goal.cmd}'
                )
                self.a_s.set_preempted(CommandResult(False, "Preempted"))
                # self._abort_and_wait() # FIXME
                return

            self.a_s.publish_feedback(
                CommandFeedback(self.ac.completed_ticket - ticket)
            )
            current_time = time.time()
            if (current_time - notify_time) >= self.CMD_WAIT_NOTIFY_INTERVAL_S:
                rospy.loginfo(
                    "Waiting on command; tickets:  completed %d; current %d"
                    % (self.ac.completed_ticket, ticket)
                )
                notify_time = current_time

            if (current_time - start_time) >= self.cmd_timeout:
                rospy.logerr("Command taking too long; aborting")
                self.a_s.set_aborted(
                    CommandResult(False, "Command took too long")
                )
                return

        self.a_s.set_succeeded(CommandResult(True, "succeeded"))
        rospy.loginfo('%s: Succeeded' % self._action_name)

    def send_command(self, cmd, *args, **kwargs):
        if not self.ac.connected:
            return None

        # Convert any positional args to kwargs
        kwargs.update(self._args_to_kwargs(cmd, *args))

        # Send message
        rospy.loginfo(f"Sending command '{cmd}' args '{kwargs}'")
        # Return ticket
        return getattr(self.ac, cmd)(**kwargs)

    def send_command_from_goal(self, goal):
        # Get command ID
        cmd_id = goal.cmd_id

        # Copy command args from message to dict
        cmd_data = self._cmds_by_id[cmd_id]
        kwargs = {k: getattr(goal, k) for k in cmd_data['args']}

        # Send command and return
        return self.send_command(cmd_data['cmd_name'], **kwargs)

    def stop(self):
        self.a_s.action_server.stop()


class CommandClient(CommandBase):
    def __init__(self, uuid):
        # Set up the command action client
        action_name = 'machinetalk/instance_{uuid}/{action}'.format(
            uuid=uuid.replace('-', '_'), action=self._action_name
        )
        self._client = actionlib.SimpleActionClient(action_name, CommandAction)

    def wait_for_server(self):
        self._client.wait_for_server()

    def stop(self):
        self._client.stop_tracking_goal()

    def _send_command_goal(self, name, *args, **kwargs):
        # Create goal message
        # - translate positional args
        kwargs.update(self._args_to_kwargs(name, *args))

        # - convert msg name to ID
        kwargs['cmd_id'] = self._cmd_id(name)
        # - generate message
        goal = CommandGoal(**kwargs)

        # Send goal to action server
        self._client.send_goal(goal)

        # Wait for server to finish
        self._client.wait_for_result()

        # Return command result
        return self._client.get_result()

    def __getattr__(self, name):
        if name not in self._cmds_by_name:
            raise AttributeError("No such method '%s'" % name)

        # Generate a closure for _send_command_goal with name set
        def send_method(*args, **kwargs):
            return self._send_command_goal(name, *args, **kwargs)

        return send_method

    def __dir__(self):
        return dir(self.__class__) + self._cmds_by_name.keys()
