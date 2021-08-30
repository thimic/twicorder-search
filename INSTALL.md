# Installation using Python 3 virtual environments
Create a virtual environment and run Twicorder Search through it to ensure a minimum of compatibility issues and problems. This guide assumes Twicorder will be run in a Bash shell.

## 1. Decide on Python interpreter and install directory
In case there are more than one Python interpreters on the system, decide which one to use. Depending on the installation, the executable might be called `python` , `python3`, `python3.7` etc.

To see which Python version an executable is set to launch, run the following command for the chosen executable:

```bash
$ python3 -V
```

This will print the Python version:

```bash
Python 3.7.2
```

Next, decide where to create the virtual environment. Twicorder will be installed to this directory.

When ready, run the following command, using the chosen Python interpreter and install directory:
   
```bash
$ python3 -m venv ~/twicorder_env
```

## 2. Activate the virtual environment
Once the virtual environment has been set up with the chosen Python interpreter, it must be activated. In the newly created environment, there’s a script in the `bin` directory, called `activate`. Source this script:

```bash
$ source ~/twicorder_env/bin/activate
```

> **NOTE**  This must be done for every new shell instance.  

The virtual environment is now ready. In The activated environment, there is a new Python executable, always named `python` and a corresponding PIP executable always named `pip`. Only these should be used from now on. They represent a clean Python environment with only the standard library installed.

## 3. Install Twicorder Search
In the newly activated environment, install Twicorder Search using PIP:

```bash
$ pip install twicorder-search
```

This installs Twicorder Search and all its dependencies to the new virtual environment. 

When done, try running Twicorder Search:

```bash
$ twicorder --help
```

Twicorder should output its help message:

```bash
Usage: twicorder [OPTIONS] COMMAND [ARGS]...

  Twicorder Search

Options:
  --project-dir TEXT  Root directory for project
  --help              Show this message and exit.

Commands:
  run    Start crawler
  utils  Utility functions
```

For more information on Python 3 virtual environments and how to install them on different platforms, see [Creation of virtual environments](https://docs.python.org/3/library/venv.html).
