import docker
import datetime
import sys
import yaml
import signal
import logging
import argparse
from pp_ros_launch.config import PPROSContainerConfig
from pp_ros_launch.system import SystemChecks


class Launcher(PPROSContainerConfig):
    name = 'launcher.docker'

    # By default, wait 30 seconds for container to exit, then kill
    shutdown_timeout = 30

    sig_to_signame = {
        getattr(signal, a): a
        for a in dir(signal)
        if a.startswith('SIG') and a not in ('SIG_DFL', 'SIG_IGN')
    }

    def get_docker_client(self, name, timeout=60):
        if not hasattr(self, name):
            setattr(self, name, docker.from_env(timeout=timeout))
        return getattr(self, name)

    @property
    def docker_client(self):
        return self.get_docker_client('_docker_client', timeout=60)

    @property
    def docker_log_client(self):
        return self.get_docker_client('_docker_log_client', timeout=None)

    def register_run(self) -> None:
        run_image = self.args.get('image', None)
        run_history = self.get_config('version_run_history', dict())
        run_item = {'date': datetime.datetime.now().isoformat()}
        run_history[run_image] = run_item
        self.set_config('version_run_history', run_history)
        # Actually, DO NOT write the config to the file as this should be outside the
        #           ¨¨¨¨¨¨
        # purview of this stage
        # self.write_config()

    def container_status(self):
        """Read and log Docker container status"""
        if not hasattr(self, 'prev_status'):
            self.prev_status = None
        try:
            self.container.reload()
            status = self.container.status
        except docker.errors.NotFound:
            status = "nonexistant"
        except docker.errors.APIError:
            status = "not running"
        if status != self.prev_status:
            self.logger.info(
                "Container %s status changed to '%s'"
                % (self.container.name, status)
            )
            self.prev_status = status

    def _cleanup_old_container(self):
        """Check if an old container is still around

        If an old container is still around, either clean it up or
        else error out.
        """
        containers = self.docker_client.containers.list(all=True)
        for c in containers:
            # Container already exists
            if c.name == self.args['name']:
                break
        else:
            # No matching container
            return True

        if c.status != "exited":
            # Be safe and error out
            self.logger.critical(
                f'Container "{c.name}" status "{c.status}" already exists'
            )
            return False
        else:
            # Exited container from previous run; clear it out
            self.logger.warning('Cleaning up exited container "%s"' % c.name)
            c.remove()
            return True

    def sanity_checks(self):
        """Pre-run sanity checks"""
        # Check no other container is running
        if not self._cleanup_old_container():
            return False
        return True

    def start_container(self):
        """Start the Docker container and signal handler"""
        self.logger.info('Starting container "%s"' % self.args['name'])
        self.logger.info('Command:  "%s"' % self.args['command'])
        # Translate pp_ros_launch objects into docker-py ones
        if self.args.get('mounts', None):
            new_mounts = [
                docker.types.Mount(
                    target=m['Target'],
                    source=m['Source'],
                    type=m['Type'],
                    propagation=m['BindOptions']['Propagation'],
                )
                for m in self.args['mounts']
            ]
            self.args['mounts'] = new_mounts
        self.container = self.docker_client.containers.run(**self.args)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def watch_container(self):
        """Attach to container, reading status and handling stdout/stderr
        log messages

        This blocks until the container has exited.
        """
        self.container_status()
        docker_logger = logging.getLogger("docker")
        container_for_logs = self.docker_log_client.containers.get(
            self.container.id
        )
        logs = container_for_logs.logs(
            stdout=True, stderr=True, stream=True, follow=True
        )
        for msg in logs:
            docker_logger.info(msg.rstrip())
            self.container_status()
        # Container has exited
        self.container_status()
        res = self.container.wait()
        errmsg = f", error {res['Error']}" if "Error" in res else ""
        self.logger.info(f"Container exited status {res['StatusCode']}{errmsg}")
        return res['StatusCode']

    def run(self):
        """Configure and run Docker container"""
        # Set up command-line argument parser and figure out what mode
        # to run in
        parser = argparse.ArgumentParser(
            description="""
            Run PathPilot Robot Container
            """
        )

        docker_run_arguments_group = parser.add_mutually_exclusive_group()

        docker_run_arguments_group.add_argument(
            '--skip-checks',
            help='Do not run system environment checks',
            action='store_true',
        )
        docker_run_arguments_group.add_argument(
            '--store-checks',
            help='Store system environment checks for next run',
            action='store_true',
        )
        SystemChecks.add_cl_args(parser)
        cl_args = parser.parse_args()

        config = self.read_config()

        # Get container run arguments
        if not cl_args.skip_checks:
            # Remove stale Docker arguments from config if exists
            if config.get('docker_run_args', None) is not None:
                self.remove_config_key('docker_run_args')

            self.checks = SystemChecks(cl_args)
            self.checks.clear_cache()
            self.check_results = self.checks.check_results_nonfatal
            if not self.check_results:
                for log in self.checks.logs():
                    self.logger.critical(log)
                return 99
            args = self.checks.docker_run_args().copy()
            # self.image = args.pop('image')
            # self.command = args.popu('command')
            # self.args = args
        else:
            args = config.get('docker_run_args', None)
            if not args:
                self.logger.critical(
                    'Unable to read container run args from configuration file'
                )
                return 100
            # self.image = args.pop('image')
            # self.command = args.pop('command', None) or sys.argv[1:]
            # self.args = args.copy()
        self.args = args.copy()

        self.logger.info(
            'Docker run parameters:\n%s'
            % yaml.safe_dump(self.args, default_flow_style=False)
        )

        # Run sanity checks
        if not self.sanity_checks():
            return 101

        self.register_run()

        # Start container and watch logs and status
        self.start_container()
        return self.watch_container()

    def signal_handler(self, signalnum=None, stack_frame=None):
        """Interrupt handler callback.

        Send interrupt signal to Docker container, set an alarm, and
        continue on (perhaps in ``watch_container()``.

        If the container fails to exit gracefully, the alarm will
        return control here.  Kill the container forcibly.
        """
        signalname = self.sig_to_signame[signalnum]
        if signalnum in (signal.SIGINT, signal.SIGTERM):
            # On first interrupt, set alarm
            if signal.getitimer(signal.ITIMER_REAL)[0] == 0.0:
                self.logger.warning(
                    "Received signal %s '%s'; relaying to container"
                    % (signalnum, signalname)
                )
                self.container.kill(signal=signalnum)
                self.logger.info(
                    "Waiting up to %s seconds for graceful exit"
                    % self.shutdown_timeout
                )
                signal.setitimer(signal.ITIMER_REAL, self.shutdown_timeout)
                signal.signal(signal.SIGALRM, self.signal_handler)
            else:
                self.logger.warning("Received additional interrupt; ignoring")
        elif signalnum == signal.SIGALRM:
            self.logger.warning("Container exit grace period exceeded; killing")
            self.container.kill()
        else:
            self.logger.warning(
                f"Received unhandled signal {signalnum} '{signalname}'"
            )


def run():
    PPROSContainerConfig.init_logging()
    launcher = Launcher()
    # launcher.logger.level=logging.DEBUG
    res = launcher.run()
    sys.exit(res)
