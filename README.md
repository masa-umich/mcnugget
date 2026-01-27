# McNugget
"The McChicken of Data Analysis."

README last updated: 1-27-2026

## Overview
McNugget is a collection of Python (and a few MatLab) scripts which interact with our data visualization, system control, and telemetry database server, [Synnax](https://www.synnaxlabs.com/). This repository was originally made by [Emiliano Bonilla](https://www.linkedin.com/in/emiliano-bonilla-8a0a95187/) in March 2023, then maintained by the 'Software' subteam until August 2025, and is now managed by Avionics.

## Disclaimer with Windows

> ### Running McNugget scripts natively inside of Windows may have unexpected behavior, including potentially being unable to use `Ctrl+C` for aborting!

While Python is an interpreted language which lets you run these scripts on any operating system, there can be some differences with how your operating system may interact with script including different Keyboard Interupt signals (`Ctrl+C`) and file path formatting.

This may not be an issue most of the time, but just in case I highly reccomend using [`WSL`](https://learn.microsoft.com/en-us/windows/wsl/install) (Windows sub-system for Linux), which will allow you to run a virtual machine of Ubuntu (or most other Linux distributions) locally on your computer with fairly low overhead. Click on the link above for instructions on how to do that.

## Usage
### Step 0: Authenticate with Git for Development (Optional)
If you are doing development, you probably want to push to this repository eventually, however to do this you will need to authenticate yourself and be added to this project. Assuming you have a GitHub account with your Umich email added to this repository, there are a few ways of doing this:

1. Simply use the [GitHub CLI](https://cli.github.com/) ***(reccomended)***

    This is by far the easiest method, simply follow the download and install prompts on the link above and then run:
    ```sh
    gh auth login
    ```
    Follow the in-terminal prompts and authenticate through your browser. As long as it completes with no errors you're good!
2. Setup SSH keys with your GitHub account

    This is a sort of painful setup process but if you can't or don't want to use the GitHub CLI for some reason, instead of writing a couple paragraphs of instructions [these ones](https://eecs280staff.github.io/tutorials/setup_git.html#github-authentication) from the EECS 280 Git setup guide should work well.

### 1. Download / Clone this Repository
```sh
git clone https://github.com/masa-umich/mcnugget.git
cd mcnugget
```
### 2. Download & Install `uv`
[`uv`](https://docs.astral.sh/uv/) is a Python package manager and project manager which all (current) McNugget projects *should* use. Install it with:
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```
### 3. Run your Program!
Hopefully what you're looking for is named as you would expect, and you can find it in either `autosequences/`, `utilities/`, or `avionics/`. Most Python scripts that are in this repository *should* be setup as [uv scripts](https://docs.astral.sh/uv/guides/scripts/), meaning they have a ["shebang"](https://en.wikipedia.org/wiki/Shebang_(Unix)) at the top of the file which tells the operating system how to run it. If so, you can simply run them as if they were executables, for instance:
```sh
./auto-channels.py
```
or, if you're outside of a POSIX system you can also type out the full command:
```sh
uv run auto-channels.py
```

## Development
Assuming you've already gone through the usage instructions (you have [`uv`](https://docs.astral.sh/uv/) installed and this repository cloned)
### Step 0: Make your project (Optional)
If you're make a new script from scratch rather than modifying an existing one, follow this guide so that it fits in with the others. First, go to the right directory (`autosequences/`, `utilities/`, or `avionics/`) and make a new project directory with `uv`:
```sh
uv init <new project name>
```
Enter it, if you want you can rename `main.py` to the name of the project which is usually nice, and then I also suggest you make the primary file of the script into a `uv` script so that it's easier for others to execute without activating the venv:
```sh
uv init --script <primary file name>
```
I also suggest that you add this line to the very top of the script. This is the 'shebang' that allows you to run the script as if it were an executable file (using the `./` syntax in your terminal) 
```
#!/usr/bin/env -S uv run --script
```
And if you've added a shebang, also modify the file metadata so that the operating system knows to look for it.
```sh
chmod +x <primary file name> # tells the OS that this should be run as an executable
```
### Step 1: Activate & Sync Virtual Environment
Once you are in the directory for the project you want to work on in your terminal, I reccomend re-focusing your (I assume) VScode window by typing:
```sh
code .
```
This will open a new VScode session inside of the directory you're in. This lets extension like the [Official VScode Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) do it's job and correctly do intellisense and stuff.

If you are editing an existing project or have just cloned the repo, you probably want to make & sync a virtual environment with:
```sh
uv sync
```

In the bottom right of your screen when you are editing a Python file, if you do not see the correct Python version, intellisense active, or if certain imports do not resolve correctly, you probably need to manually set your Python intepreter to the `.venv` directory in your project directory.

Also, activate the virtual environment in your terminal. In VS code, most terminals will do this automatically if you close them with `Ctrl-D` and re-open them, but if they don't you can also manually acitvate the virtual environment with:
```sh
./.venv/bin/activate
```

### Step 2: Start Writing Code!
If you're making a script that talks with Synnax, [their guides](https://docs.synnaxlabs.com/reference/python-client/get-started) are a good place to start. Note that instead of using `pip install synnax` you should correctly add it to your `uv` project:
```sh
uv add synnax
```
As well as any other external modules or libraries you want to use. Also make sure to add them to the 'script' version of the primary file as well with:
```sh
uv add --script <file_name> synnax
```
or specify a version like this:
```sh
uv add --script <file_name> 'synnax==0.49.8'
```
And run your project with:
```sh
uv run <file_name>
```
Or as a file like shown in the 'usage' instructions in this document.

When developing, remember to make a new branch of this repo, make & push commits often, and make pull-requests when you're done! 

### Step 3: Install and Setup a Synnax Cluster for Testing (Optional)
If you want to test your script with a real Synnax cluster before you push it (a GREAT idea), you can do so by following the instructions on their website [found here](https://docs.synnaxlabs.com/reference/cluster/quick-start). Make sure to change your connection settings to use `localhost` as the host in your Synnax connection settings.
### Step 4: Install and Setup a Synnax Console (Optional)
Install the [Synnax Console](https://docs.synnaxlabs.com/reference/console/get-started) for your operating system to view what your script is doing in real-time!

- **Host:** `localhost` or sometimes `synnax.masa.engin.umich.edu`
- **Port:** `9090`
- **Username:** `synnax`
- **Password:** `seldon`
- **Secure:** `FALSE`

### Step 5: Install and use Ruff (Optional)
Ruff is a great, fast, Python Linter and code formatter made by the same folk who make `uv`. I suggest most projects use it to make code in this repository consistent. You can find it [here](https://github.com/astral-sh/ruff).


## FAQ and Common Problems
Q: What is Synnax?\
A: Synnax is our data visualization, system control, and telemetry database server. Basically, it takes in all of the sensor readings from our rocket or engine in real-time, stores them into a database so we can look at them later, and lets us control things on our system in real-time like valves. Synnax used to be made by MASA for MASA, but has since become a [succesful Colorado-based startup](https://www.synnaxlabs.com/company).

Q: WHERE ARE MY FILES?!\
A: I (Jack) did a re-organization on October 20th, 2025 -- around when Avionics took over this repository. All old files (that haven't been replaced/updated) are in `mcnugget/archive` and for even older files, look in `mcnugget/archive/old` (a fantastic name, I know)

Q: How do I connect to the real DAQ PC during a test to use a script?\
A: All scripts will prioritize the current Synnax cluster last connected to in the terminal with:
```sh
sy login
```
When run in a project with the virtual environment activated. When connecting, these are the default connection settings for the DAQ PC:
- **Host:** `synnax.masa.engin.umich.edu`
- **Port:** `9090`
- **Username:** `synnax`
- **Password:** `seldon`
- **Secure:** `FALSE`

Q: How do I make it so I can run my script with the `./` again?\
A: Add this line to the top of the file above your UV script header:
```sh
#!/usr/bin/env -S uv run --script
```
And also modify the file metadata so the OS sees it as an executable with this:
```sh
sudo chmod +x <filname>
``` 

Q: When I run a Synnax server on Windows but try to access it with my script in WSL, I can't connect\
A: The IP of your Windows computer that is exposed to WSL is not `localhost` be default, but you can find it by running this command in WSL:
```sh
ip route show | grep -i default | awk '{ print $3}'
```
You should be able to set that as the host in your Synnax scripts to be able to connect.

Q: Why is it called McNugget?\
A: To quote the famous Emiliano Bonilla: "I saw someone eating a chicken nugget while I was trying to come up with a name."