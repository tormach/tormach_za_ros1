# Robot Command Interpreter

This ROS packages provides a robot command language interpreter and ways to manipulate programs programmatically.

The interpreter use the Python programming language and the Python interpreter as basis.
To inspect the program during execution and to manipulate the program structure, the Python `ast` module is used.

Additionally, for inspecting the program structure, this package uses the `parso` library.

## Starting the interpreter node

Starting the interpreter node can be done with:

```bash
roslaunch robot_command interpreter_node.launch interpreter:="execution"
```

At the moment the interpreter support 2 language sets:
* execution
* simulation

## Building and deploying the docs

The docs can be built inside the `/doc` folder by issuing the following command:

```bash
make html
```

Alternatively, we can build and upload the docs to Confluence.
The CLI will aks you for your Confluence cloud username and a password. The password
should be an [Atlassion API Token](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/).

This command will publish the docs to https://tormach.atlassian.net/wiki/spaces/ROB/pages/3248914435/Tormach+Robot+Programming+Language

```bash
make confluence
```

To release the docs to the public space https://tormach.atlassian.net/wiki/spaces/ROBO/pages/1930690719/Tormach+Robot+Programming+Language use:

```bash
make confluence release
```
