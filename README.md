# Niryo Ned2

Example scripts to control a Niryo Ned2 robot arm:

* The script `examples/example-move.py` is a simple example how to use the package `pyniryo2` to move the robot arm using Python.
* The script `ned2cli.py` is a simple CLI application where you can interactively control the robot use the terminal.

### example-move.py

You can run the script as:
```shell
python ./example-move.py
```

By default, the robot arm will try to pick up something from left front of the robot arm and place it in
front of the robot arm. You can replace the function `run_actions()` with your own actions.

### ned2cli.py

```shell
./ned2cli.py
```
There are a number of positions pre-defined that you can use to address the positions
A1 - C3 on the paper in front of the robot arm. To move the robot arm to position A1:
```shell
move A1
```
To pick up something from position B2:
```shell
pick B2
```

To place something the robot arm is holding at position C3:
```shell
place C3
```

List saved positions:
```shell
list
```
To list all commands:
```shell
help
```

Exit the application:
```shell
exit
```

## Installation

Python 3.8 is recommended for the `pyniryo2` package.
You can use, for example, [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation)
to handle installation of multiple Python versions.

```shell
# Create a virtual environment
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
