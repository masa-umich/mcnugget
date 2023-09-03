# McNugget

The McChicken of Data Analysis. It's not gonna change your life, but it gets the job done.

## Get Started

McNugget is an analysis toolkit that automatically reads and writes data from the MASA
Synnax Data Processing Server (no configuration required!), which you can use to analyze
MASA's 2023 and later data.

## A Typical Workflow

A typical workflow with McNugget involves the following steps:

1. Finding the range (time range) of data you're interested in getting access to. The ideal
   way to do this is to use the [Synnax Visualization UI](https://docs.synnaxlabs.com/visualize/get-started)
   to plot different areas of data. Once you've found the range you're interested in, copy it to your clipboard.

2. Create a new script describing the analysis you intend on doing (for example, `cda.py`).

3. In your script import the `mcnugget.query.read` method to read the data for the channel's you're interested in.

4. Perform analysis.

5. Print out the results or plot the data.

6. Push your changes!

## Install the Visualization UI

To get started with McNugget, you'll need to install the Synnax Visualization UI. To do this, simply follow the instructions [here](https://docs.synnaxlabs.com/visualize/get-started?).

The next step is to connect to the MASA cluster. Instructions for this can be found [here
](https://docs.synnaxlabs.com/visualize/connect-a-cluster).

The MASA server connection parameters are as follows:

- **Name**: `MASA Remote`
- **Host**: `masa.synnaxlabs.com`
- **Port**: `80`
- **Username**: `synnax`
- **Password**: `seldon`

## Install McNugget

To kick things off, you'll need to clone this repository using `git`. If you don't have `git` installed, you can find instructions [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git). Once you have `git` installed, create a new project/folder in your [editor](#what-editor-should-i-use). We recommend the
directory `~/Desktop/masa-umich/`. Then, run the following command:

```bash
git clone https://github.com/masa-umich/mcnugget.git
```

This will download the mcnugget source code into the directory `~/Desktop/masa-umich/mcnugget/`.

After downloading the source, the next step is to install and set up Python. You'll need vesrion 3.11. If you don't have
Python installed, see the [Python Installation Guide](https://www.python.org/downloads/) for instructions.
If you're not sure what version you're running, use the following command:

```bash
python --version
```

If you don't see `3.11.x` or higher in the output, you'll need to upgrade your Python installation. If you see
the output `command not found`, your python installation use the `python3` or `python3.11` command instead of `python`.
If you get an error saying `command not found`, try using `python3` or `python3.11` instead. The same goes for
the commands involving `pip` (try `pip3` or `pip3.11` instead). If you're still having trouble, ask for help in the
`#software` slack channel.

McNugget uses a virtual environment tool called `poetry` to manage it's dependencies
and configuration. To install poetry, run the following command:

```bash
pip install poetry
```

Then, we need to make sure the virtual environment we use is created in the same directory as our project (if you don't know what a virtual environment is, don't worry).

```
poetry config virtualenvs.in-project true
```

Now that you have poetry installed, you can install McNugget's dependencies by running
the following command:

```bash
poetry install
```

## Starting a Shell and Running an Example

To verify everything installed correctly, you'll want to run an example. The first step is to
start a shell. To do this, run the following command:

```bash
poetry shell
```

You'll want to be in a shell whenever you're running mcnugget scripts. Run the following example script:

```bash
python examples/simple_line_plot.py
```

A line plot containing some TPC data should show up.

## How to Analysis: A detailed guide for the enlightened

### Create a new script

The first step is to create a new script in the `mcnugget` directory. Choose the name of this script
to match the type of analysis you're performing. For example, if you're performing a CDA analysis,
name the script `cda.py`.

### Import a few useful tools

There are a few tools we'll need for reading, cleaning, processing, and plotting data. Import them
at the top of your file as follows (feel free to copy and paste):

```python
import matplotlib.pyplot as plt
import synnax as sy
from mcnugget.query import read
from mcnugget.time import elapsed_seconds
```

If you're interested in what each import does, here's a brief description:

- `import matplotlib.pyplot as plt` is a plotting library that we use to plot data. It's a 1-1 port of the MATLAB plotting library.
- `import synnax as sy` is a library that we use to define time ranges. We'll use this to define the range of data we want to read.
- `from mcnugget.query import read` is a method that we use to read data from the data server. We'll use this to read the data we want to analyze.
- `from mcnugget.time import elapsed_seconds` is a handy utility to conver tthe values in a time channel to elapsed seconds.

### Finding the data you're interested in

There are two ways to find the data you're interested in. The first is to use one of the pre-chosen
tests. The list of tests can be found in (`mcnugget/tests.py`). The tests are categorized by type,
then sorted by date and test number. For example, the first test in the `TPC` category is `02-19-23-02`.

If you find the test you're looking for, import the test type and extract the test as follows:

```python
# After all the other imports
from mcnugget.tests import TPC

TEST = TPC["02-19-23-02"]
```

If you can't find the test you're looking for, you can add it yourself!

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
        this error and send it in the #software slack channel.
```

## Updating McNugget Dependencies

Sometimes we add new dependences to McNugget, to make sure all of your dependencies are up to date, run:

```
poetry install
```

in the root directory of the repository.

## Frequently Asked Questions

### What editor should I use?

If you're moving from MATLAB or haven't used an IDE before, you may be wondering what editor to use. For the most
MATLAB like experience we recommend using [PyCharm](https://www.jetbrains.com/pycharm/). The free version is fine for
all of our use cases, but you can also get the pro version for free if you're a student.

If you're lookin for a lightweight editor, we recommend [VSCode](https://code.visualstudio.com/). It's the most widely
used editor by far.

**TLDR: Use VSCode**

### Why is it called McNugget?

I saw someone eating a chicken nugget while I was trying to come up with a name.
