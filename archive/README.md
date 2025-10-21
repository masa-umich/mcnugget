# McNugget

The McChicken of Data Analysis. It's not gonna change your life, but it gets the job done.

## 0 - Overview

McNugget is an analysis toolkit that automatically reads and writes data from the MASA
Synnax Data Processing Server (no configuration required!), which you can use to analyze
MASA's 2023 and later data.

## 1 - Installation

### 1.0 - Connect to MWireless or the UofM VPN

To work with McNugget, **you'll need to be connected to the UofM VPN or MWireless.** Instructions for installing
and using the VPN can be found [here](https://its.umich.edu/enterprise/wifi-networks/vpn/getting-started).

### 1.1 - Install the Synnax CA Certificates

The next step is to install the Synnax encryption certificates. These allow you to communicate with the database in a
secure manner. To install them, run the corresponding command for your operating system:

#### MacOS

```bash
curl -sfL https://raw.githubusercontent.com/masa-umich/mcnugget/main/scripts/install_certs_macos.sh | sh -
```

Note that you will be prompted for your password.

#### Windows

```powershell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/masa-umich/mcnugget/main/scripts/install_certs_windows.ps1 -OutFile install_certs_windows.ps1
```

Then, run the following command in **powershell**:

```powershell
.\install_certs_windows.ps1
```

### 1.2 - Install the Synnax Console

The Synnax Console is the tool we use for test ops and data visualization. It's also very useful for analysis. 
To install it, follow the instructions [here](https://docs.synnaxlabs.com/console/get-started?). Then, follow the 
instructions [here](https://docs.synnaxlabs.com/console/connect-a-cluster?) to connect to the MASA server. Use the 
following connection parameters: 

- **Name**: `MASA Remote`
- **Host**: `synnax.masa.engin.umich.edu`
- **Port**: `80`
- **Username**: `synnax`
- **Password**: `seldon`
- **Secure**: `true`

**Please note that the console ONLY works on the latest versions of MacOS (Sonoma), Windows 10, and Windows 11**

If you find that plots don't display, you may need to udate your version of MacOS **or** your version of Microsoft Edge
on Windows.

### 1.3 -  Install McNugget

#### Clone the Repository

To kick things off, you'll need to clone this repository using `git`. If you don't have `git` installed, you can find
instructions [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git). Once you have `git` installed,
create a new project/folder in your [editor](#what-editor-should-i-use). We recommend the
directory `~/Desktop/masa-umich/`. Then, run the following command:

```bash
git clone https://github.com/masa-umich/mcnugget.git
```

This will download the mcnugget source code into the directory `~/Desktop/masa-umich/mcnugget/`.

#### Install Python

After downloading the source, the next step is to install and set up Python. You'll need version 3.11. If you don't have
Python installed, see the [Synnax Python Guide](https://docs.synnaxlabs.com/python-client/troubleshooting?). If you're
still having trouble, send a message in the `#software` Slack channel.

McNugget uses a virtual environment tool called `poetry` to manage its dependencies and configuration. To install poetry, 
run the following command:

```bash
pip install poetry
```

Then, we need to make sure the virtual environment we use is created in the same directory as our project (if you don't
know what a virtual environment is, don't worry).

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
from mcnugget.client import client

```

If you're interested in what each import does, here's a brief description:

- `import matplotlib.pyplot as plt` is a plotting library that we use to plot data. It's a 1-1 port of the MATLAB
  plotting library.
- `import synnax as sy` is a library that we use to define time ranges. We'll use this to define the range of data we
  want to read.

### Finding the data you're interested in

The best way to find the list of ranges you're interested in is by using the console and following this [guide](https://docs.synnaxlabs.com/console/querying-data).
Once you've found it, you can bring in the range and plot some data on it like so:

```py
import matplotlib.pyplot as plt
import synnax as sy
from mcnugget.client import client

rng = client.ranges.retrieve("My Cool Range")

plt.plot(sy.elapsed_seconds(rng.gse_time), rng.gse_ai_1)
plt.show()
```

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

## What Editor should I use?

## The Dictionary Answer

If you're moving from MATLAB or haven't used an IDE before, you may be wondering what editor to use. For the most MATLAB like experience we recommend using [DataSpell](https://www.jetbrains.com/dataspell/). The free version is fine for all of our use cases, but you can also get the pro version for free if you're a student.

If you're looking for a lightweight editor, we recommend [VSCode](https://code.visualstudio.com/). It's the most widely used editor by far.

## Emiliano's Opinion

### 1 - Sign up for GitHub pro for students

GitHub pro for students gives you access to copilot AI autocompletion and JetBrains IDEs 
for free. You can sign up [here](https://education.github.com/pack). 

### 2 - Install DataSpell

While VSCode is lightweight and multi-purpose, DataSpell has much better Python syntax
highlighting and error checking out of the box. It also gives you really nice debug
and run buttons like MATLAB. 

If you have github pro, you can get DataSpell and ALL of the JetBrains IDEs for free [here](https://www.jetbrains.com/community/education/#students).

### 3 - Sign up for github copilot

If you're new to Python or coming from MATLAB, github copilot is a godsend. It's an AI
that autocompletes your code for you. You can sign up [here](https://copilot.github.com/)
for free with your github pro account.

### 4 - Install the copilot plugin for DataSpell

The copilot plugin for DataSpell allows you to use copilot directly in DataSpell. You can
install it by going to `File > Settings > Plugins` and searching for `copilot`.


### Why is it called McNugget?

I saw someone eating a chicken nugget while I was trying to come up with a name.
