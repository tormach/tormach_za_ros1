# Using

## Install manually:

```
DIR=install_scripts/docker/ros_d_common/pp_ros_versions
( cd $DIR; sudo python setup.py install -v )
```

## Running tests

There are a few ways to run tests:

- From `catkin` inside the container

        catkin run_tests pp_ros_launch

- From `setup.py`
  - Inside the container:
    - Add `ENV_COOKIE=bare-metal`
    - Run `sudo -H pip install -U requests coverage` to fix version
      conflict
    - Also can use `python3.6`

            ENV_COOKIE=bare-metal python setup.py pytest

- From `pytest`:

        pytest-3
