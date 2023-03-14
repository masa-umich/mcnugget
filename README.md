# McNugget

The McNugget of Data Analysis. It's not gonna change your life, but it gets the job done.

## Getting Started

McNugget is an analysis toolkit that automatically reads and writes data from the MASA 
Synnax Data Processing Server (no configuration required!), which you can use to analyze
MASA's post-2023 data. 

An installation and basic usage guide is available below. Simple examples are available
in the `examples` directory.

## Installation

To get started with McNugget, you'll need Python 3.11. If you don't have Python installed,
see the [Python Installation Guide](https://www.python.org/downloads/) for instructions.
If you do, use the following command to check your version:

```bash
python --version
```

If you don't see `3.11.x` or higher in the output, you'll need to upgrade your Python installation.

McNugget also uses a virtual environment tool called `poetry` to manage it's dependencies
and configuration. To install poetry, run the following command:

```bash 
pip install poetry
```

Now that you have poetry installed, you can install McNugget's dependencies by running 
the following command:

```bash
poetry install
```

## Starting a Shell and Running an Example

To start a shell with McNugget's dependencies loaded, run the following command:

```bash
poetry shell
```

Then, run the following example script:

```bash
python examples/simple_line_plot.py
```

A line plot containing some COPV press data should show up.

## Common Errors

### Can't connect to the data server

If you see an error like the following, screenshot it and send it in the #avionics slack channel:

```bash
Traceback (most recent call last):
  File "/Users/emilianobonilla/Desktop/masa-umich/mcnugget/mcnugget/query/client.py", line 13, in <module>
    CLIENT = Synnax(
             ^^^^^^^
  File "/Users/emilianobonilla/Desktop/synnax/client/py/synnax/synnax.py", line 75, in __init__
    self._transport = self._configure_transport(
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/emilianobonilla/Desktop/synnax/client/py/synnax/synnax.py", line 119, in _configure_transport
    auth.authenticate()
  File "/Users/emilianobonilla/Desktop/synnax/client/py/synnax/auth.py", line 98, in authenticate
    raise exc
freighter.exceptions.Unreachable: Target http://10.0.0.15:9090/api/v1/auth/login/ unreachable

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/emilianobonilla/Desktop/masa-umich/mcnugget/examples/simple_line_plot.py", line 3, in <module>
    from mcnugget.query import read_during_state, ECStates
  File "/Users/emilianobonilla/Desktop/masa-umich/mcnugget/mcnugget/query/__init__.py", line 1, in <module>
    from .read import *
  File "/Users/emilianobonilla/Desktop/masa-umich/mcnugget/mcnugget/query/read.py", line 2, in <module>
    from mcnugget.query.client import CLIENT
  File "/Users/emilianobonilla/Desktop/masa-umich/mcnugget/mcnugget/query/client.py", line 21, in <module>
    raise Exception(
Exception: 
        Failed to connect to Synnax data processing sever. Screenshot
        this error and send it in the #avionics slack channel.
```





