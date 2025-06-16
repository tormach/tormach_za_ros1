#!/usr/bin/python
import logging
import os
import sys
import json
import traceback
import signal
from supervisor.states import SupervisorStates
from supervisor.childutils import getRPCInterface, xmlrpclib


class Launcher:
    _cache = {}

    def __init__(self, supervisord):
        self.supervisord = supervisord
        self._cache['launcher'] = self
        self.logger.info('Initialized PathPilot launcher manager')
        # self.mgr = LaunchManager()

    @property
    def logger(self):
        return self.supervisord.options.logger

    def _get_processes(self, name):
        group = self.supervisord.process_groups.get(name)

        if group is None:
            self.logger.error("Bad process group name '%s'" % name)
            # FIXME how to handle this?
            return

        return sorted(group.processes.values())

    def start_process_group(self, name):
        processes = self._get_processes(name)
        if processes is None:
            self.logger.error('Unknown process "%s"' % name)
            return False
        for p in processes:
            result = p.spawn()
            if result is None:
                self.logger.error(f'Starting process {p.name}:  {p.spawnerr}')
                return False
        return True

    def handle_supervisor_state_change_running(self, headers):
        if os.environ.get('VIRTUAL_PATHPILOT') == "1":
            # Run UIs in VNC
            virtual_programs = ('xorg', 'x11vnc')
        else:
            virtual_programs = tuple()

        if os.environ.get('LAUNCHER') == "1":
            # Run launcher UI
            programs = virtual_programs + ('launcher_ui',)
        else:
            # Run robot UI
            programs = virtual_programs + ('robot_ui',)

        for pgname in programs:
            self.logger.info(
                f'PathPilot Robot:  Starting {pgname} for{" Virtual" if os.environ.get("VIRTUAL_PATHPILOT") else ""} Pathpilot Robot'
            )
            if not self.start_process_group(pgname):
                return False
        return True

    def handle_process_state(self, headers):
        # Remove "PROCESS_STATE_" prefix & set lowercase
        state = headers['eventname'][14:].lower()
        data = dict([x.split(':') for x in headers['data'].split()])
        gname = data['groupname']
        if gname in ('launcher_ui', 'robot_ui'):
            if state == 'exited':
                self.logger.warn(
                    f'PathPilot Robot:  {gname} exited; shutting down'
                )
                self.supervisord.options.mood = SupervisorStates.SHUTDOWN
                return
            elif state == 'fatal':
                self.logger.critical(
                    f'PathPilot Robot: {gname} fatal; shutting down'
                )
                self.supervisord.options.mood = SupervisorStates.SHUTDOWN
                return

        self.logger.info(f'Program "{gname}" entered state {state}')

    def dispatch_event(self, event, response):
        headers = json.loads(response)
        if hasattr(event, 'supervisord'):
            headers['supervisord'] = event.supervisord
        eventname = headers['eventname'].lower()
        if eventname.startswith('process_state_'):
            handler = self.handle_process_state
        else:
            handler = getattr(self, 'handle_%s' % eventname, None)
        if handler is None:
            self.logger.critical(f'Unhandled event: {headers["eventname"]}')
            return
        try:
            handler(headers)
        except Exception:
            self.logger.critical('Exception handling event:')
            self.logger.critical(traceback.format_exc())

    @classmethod
    def event_listener(cls):
        """Loop all received events back to the event handler"""
        while 1:
            # Transition from ACKNOWLEDGED to READY
            sys.stdout.write('READY\n')
            sys.stdout.flush()

            # Split up header into a dict, add data as a key and
            # convert to JSON for shipping back to the event handler
            line = sys.stdin.readline()
            headers = dict([x.split(':') for x in line.split()])
            headers['data'] = sys.stdin.read(int(headers['len']))
            payload = json.dumps(headers) + '\n'

            # Transition from READY to ACKNOWLEDGED
            sys.stdout.write('RESULT %d\n%s' % (len(payload), payload))
            sys.stdout.flush()

    @classmethod
    def get_launcher(cls):
        '''Singleton factory'''
        return cls._cache['launcher']


class SupervisorClientError(RuntimeError):
    pass


class SupervisorClient:
    """Supervisor client interface

    This class may be used from external code
    """

    _cache = {}

    logger = logging.getLogger('launcher.rpcinterface')

    def __init__(self, process_name=None):
        self.process_name = process_name

    @classmethod
    def get_run_dir(cls, fname=None):
        run_dir = os.environ.get('RUN_DIR')
        if fname is not None:
            run_dir = os.path.join(run_dir, fname)
        return run_dir

    @classmethod
    def _get_rpc_client(cls, make_new=False):
        if 'client' not in cls._cache or make_new:
            sock = 'unix://' + cls.get_run_dir('supervisor.sock')
            cls._cache['client'] = getRPCInterface(
                dict(SUPERVISOR_SERVER_URL=sock)
            )
        return cls._cache['client'].supervisor

    @property
    def _supervisor(self):
        return self._get_rpc_client()

    def start_process(self):
        '''Launch a process'''
        try:
            return self._supervisor.startProcess(self.process_name)
        except xmlrpclib.Fault as e:
            raise SupervisorClientError(
                f"Docker error {e.faultCode}:  {e.faultString}"
            )

    @property
    def process_info(self):
        '''Get process info'''
        return self._supervisor.getProcessInfo(self.process_name)

    @property
    def process_state(self):
        '''Process state'''
        # http://supervisord.org/subprocess.html#process-states
        return self.process_info['statename']

    @property
    def spawnerr(self):
        return self.process_info['spawnerr']

    @property
    def exitstatus(self):
        return self.process_info['exitstatus']

    @classmethod
    def shutdown(cls):
        '''Shut down the supervisor'''
        # Force new client in case the previous was interrupted
        supervisor = cls._get_rpc_client(make_new=True)
        try:
            shutdown_res = supervisor.shutdown()
        except xmlrpclib.Fault:
            shutdown_res = False
        except FileNotFoundError:
            cls.logger.warning("Can't establish connection to supervisord")
            return
        if not shutdown_res:
            with open(cls.get_run_dir('supervisord.pid')) as f:
                pid = int(f.readline())
            os.kill(pid, signal.SIGQUIT)


def make_rpcinterface(supervisord, **config):
    """At supervisord start, this interface sets up the initial Launcher
    singleton in order later on to provide later object access to the
    event handler
    """
    return Launcher(supervisord)


def handle_event(event, response):
    """This interface receives and dispatches looped-back event data from
    eventlisteners
    """
    launcher = Launcher.get_launcher()
    launcher.dispatch_event(event, response)


def run_listener():
    """This interface is the external event listener, forked as a script,
    that receives event data from supervisord and re-encodes it to
    pass back into the event handler
    """
    Launcher.event_listener()


if __name__ == '__main__':
    run_listener()
