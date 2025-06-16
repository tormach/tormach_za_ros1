# Tormach ZA robot ROS 1 application stack

[This repository][1] contains the Tormach ZA robot application software
stack, including:
- Low-level EtherCAT driver and sim driver configuration
- `ros_control` configuration
- MoveIt configuration
- The Tormach TRPL robot program interpreter
- The Tormach PathPilot Robot Edition graphical user interface
- The Tormach robot launcher system
- Docker image build and run configuration

The repository is structured as a ROS 1 workspace.  This README shows
how to set up the ROS workspace, build the Docker image, build the ROS
workspace, and run the robot UI.

[1]:  https://github.com/tormach/tormach_za_ros1

## Host requirements

The sim hardware configuration can be run on any host machine with
[Docker Engine][2] installed.

The real hardware configuration, in addition to Docker Engine, also
requires a `RT_PREEMPT` Linux kernel and IgH EtherCAT master.  These
all come pre-installed on a Tormach robot controller, the only
controller hardware supported by Tormach.  It may be possible, but
unsupported, to install these requirements on a PC, most easily:

- OS:  Debian Bullseye
- RT kernel:  `linux-image-rt` and `linux-headers-rt` packages
- Docker:  [official packages][2]
- EtherCAT master:  [APT package repository][4]
  - The Tormach EtherCAT master contains some customizations; see also
    the [git repo][3]

[2]:  https://docs.docker.com/engine/install/
[3]:  https://github.com/zultron/etherlabmaster/
[4]:  https://cloudsmith.io/~zultron/repos/etherlabmaster/

## Build the Docker image

The ZA robot software stack has many external software dependencies.
To simplify a standard development environment, dependencies are built
into a Docker image.  The image and this git repo contain everything
needed to build and run the ZA software stack, either real or
simulated hardware, except for the minimal host requirements described
in the previous section.

To build the Docker image, first choose a directory to check out the
ROS workspace, e.g. `WS_DIR=~/ros`.

```
# Check out ROS workspace git repo and `cd` into it
git clone https://github.com/tormach/tormach_za_ros1 $WS_DIR
cd $WS_DIR

# Build the Docker image
./install_scripts/docker-dev.sh -b
```

When the `docker build` completes, `docker image ls` should show a new
image labeled something like e.g.
`tormach/ros:noetic-devel-focal-259.ecaad303`.  The
e.g. `259.ecaad303` is an image serial number and a hash that matches
the image to the source code.  If scripts ever complain the Docker
image can't be found, rerun `./install_scripts/docker-dev.sh -b` to
build a new image.

## Starting the Docker container, and starting new terminals

Start the Docker container as follows.

```
# From the ROS workspace directory,
cd $WS_DIR

# Run the Docker image
./install_scripts/docker-dev.sh
```

The `./install_scripts/docker-dev.sh` script will start the Docker
container and give you an interactive shell prompt.  Exiting this
initial shell will also exit the container.

Additional shells can be started in other terminals with the same
command.  The new shells will execute in the same Docker container.
Exiting these additional shells will NOT exit the container.

## Building the ROS workspace

From a shell inside the Docker container, build the ROS workspace as
follows.  The shell will already be in the top-level directory of this
git repo.

```
# Build the ROS workspace
./devel_scripts/build_workspace.sh
```

## Running PathPilot Robot Edition

Once the ROS workspace is built, from a shell inside the Docker
container, run the application.

```
# Source the ROS workspace environment
source devel/setup.bash

# Run the ZA6; add the `-h` flag for more options
devel_scripts/start_robot_ui.py za6
```
