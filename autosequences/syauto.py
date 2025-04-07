from synnax.control.controller import Controller
from typing import Tuple
import time
import colorama
import json
import hashlib
import os

"""
syauto is a library intended to abstract away confusing parts of how we interface with the system.

Some brief background on valves, commands, and this library:
Valves are basically 'gates for pressure'. They can be open (allowing pressure to flow through) or closed.
Note that pressure always goes from the higher pressure to the lower pressure.

A valve can be 'normally open' or 'normally closed'. Usually we want this property to be 
    specified based on what the 'fail state' of the component is (whether we want it open/closed if things go wrong).
    Vents are generally 'normally open', so if we lose power, the system will automatically depressurize.
A valve can be 'energized' or 'deenergized'. 
    If a valve is deenergized, it is in its default state.
    If a valve is energized, it is in the opposite of its default state.
In Synnax, valves have a command channel and an acknowledgement channel. 
    The command channel is where we send commands to open or close, and the acknowledgement channel sends the 
    'state' of the system (from the source where we physically implement the commands we send).

Pulling this all together, suppose we have a valve with the following specifications:
    command channel 'valve_1_cmd'
    state channel 'valve_1_state'
    normally_open = false (it is not a vent)
If we want to open the valve, we need to send a command to energize the valve. We do this with
    `auto['valve_1_cmd'] = True`
Since `auto` is a controller which gives us access to the state of the Synnax cluster (and, by extension, the physical system),
sending this command results in energizing valve_1, after which we will receive a `1` or `True` value on the acknowledgement channel.

"""

class Valve:
    # this defines a class that can be used for both regular valves and vents
    def __init__(
            self,                               # python thing
            auto: Controller,                   # the controller this valve uses to talk with system
            cmd: str,                           # command channel name
            state: str,                         # acknowledgement channel name
            normally_open: bool = False,        # whether the valve's default state is 'open'
            wait_for_ack: bool = False
    ):
        self.cmd_chan = cmd
        self.ack = state
        self.normally_open = normally_open
        self.auto = auto
        self.wait_for_ack = wait_for_ack

    def open(self):
        # for reg. valve, normally_open is false so cmd is set to True
        # for vent valve, normally_open is true so cmd is set to False
        # sanity check ^
        self.auto[self.cmd_chan] = not self.normally_open
        if self.wait_for_ack:
            self.auto.wait_until(self.ack_chan != self.normally_open)

    def close(self):
        # for reg. valve, normally_open is false so cmd is set to False
        # for vent valve, normally_open is true so cmd is set to True
        # sanity check ^
        self.auto[self.cmd_chan] = self.normally_open
        if self.wait_for_ack:
            self.auto.wait_until(self.ack_chan == self.normally_open)

class Parameter:
    def __init__(self, key: str, value, param_type: type = None, explicit: bool = False, locked: bool = False):
        self.key = key
        self.value = value
        self.type = param_type
        self.explicit = explicit
        self.locked = locked
        self.validated = False

    def __repr__(self):
        return f"{self.key}={self.value}"

    def validate(self) -> bool:
        if self.type is not None and not isinstance(self.value, self.type):
            print(_yellow(f"Parameter {self.key} is not of type {self.type}"))
        input(f"Press enter to verify that {_green(self.key)} is set to {_green(self.value)} ")
        self.validated = True
        return True
        
    def update(self, value):
        if self.locked:
            raise ValueError(f"Parameter {self.key} is locked and cannot be updated")
        if self.type is not None and not isinstance(value, self.type):
            raise ValueError(f"Parameter {self.key} is not of type {self.type}")
        self.value = value
        self.validated = False

class Config:
    def __init__(self):
        self.parameter_list = []
        self.parameters = {}
        self.locked = False
        self.validated = False

    def __getitem__(self, key):
        p = self.parameters.get(key)
        if p is None:
            raise ValueError(f"Parameter {key} not found in config file")
        return p.value
    
    def __setitem__(self, key, value):
        if self.locked:
            raise ValueError(f"Parameter {key} is locked and cannot be updated")
        if key not in self.parameters:
            raise ValueError(f"Parameter {key} not found in config file")
        self.parameters[key].update(value)
        self.validated = False

    def _load_maybe_checksum(self, config_file: str) -> Tuple[dict, str]:
        with open(config_file, 'r') as f:
            checksum = ""
            readlines = f.readlines()
            if readlines[-1].split(":")[0] == "# Checksum":
                checksum = readlines[-1].split(":")[-1].strip()
                readlines = readlines[:-1]
            parameters = json.load(f.readlines())
        return parameters, checksum
    
    def _check_param_list(self, enforce_types: bool = False):
        for p in self.parameter_list:
            if p.key not in self.parameters:
                raise ValueError(f"Parameter {p.key} not found in config file")
            if enforce_types and p.type is not None and not isinstance(self.parameters[p.key], p.type):
                raise ValueError(f"Parameter {p.key} is not of type {p.type}")

    def load(self, config_file: str = ""):
        if config_file == "":
            for p in self.parameter_list:
                if self.parameters.get(p.key) is None:
                    val = input(f"Enter value for {_red(p.key)}: ")
                else:
                    val = input(f"Enter new value for {_red(p.key)} - {_yellow(f'current value: {self.parameters[p.key]}')}: ")
                self.parameters[p.key] = val
        else:
            with open(config_file, 'r') as f:
                # extract checksum
                checksum = f.readlines()[-1].split(":")[-1].strip()
                self.parameters = json.load(f.readlines()[:-1])
                # check checksum
                if hashlib.sha256(json.dumps(self.parameters).encode('utf-8')).hexdigest() != checksum:
                    raise ValueError(_red(f"Checksum does not match for {config_file}"))

        for p in self.parameter_list:
            if p.key not in self.parameters:
                raise ValueError(f"Parameter {p.key} not found in config file")
    
    def view(self):
        print(_blue("Parameters:"))
        for param in self.parameter_list:
            if param.key in self.parameters:
                print(f"{param.key} = {self.parameters[param.key]}")
            else:
                print(f"{param.key} = None")
        print(_blue("End of parameters"))

    def validate(self, manual: bool = False):
        missing = False
        for param in self.parameter_list:
            if self.parameters.get(param) is None:
                print(f"Missing parameter {param} in config file")
                missing = True
        if missing:
            return False

        if manual:
            sre = input(_magenta("Type `SRE` to verify there is an SRE present ")).lower()
            tc = input(_magenta("Type `TC` to verify there is a TC present ")).lower()
            cop = input(_magenta("Type `COP` to verify there is a COP present ")).lower()
            if sre != "SRE" or tc != "TC" or cop != "COP":
                print(_red("SRE, TC, and COP must all be present to validate a configuration file"))
                return False
            
            for param in self.parameter_list:
                value = self.parameters[param]
                input(f"Press enter to verify that {_green(param)} is set to {_green(value)} ")
            
            print(_green(f"Parameters have been verified"))

    def lock(self, filepath: str):
        # check if something exists at filepath
        if not self.validated:
            input(_red("Press enter to confirm you want to lock parameters that have not been validated"))
        if os.path.exists(filepath):
            input(_red(f"{filepath} already exists, press enter to overwrite: "))
        checksum = hashlib.sha256(self.parameters.encode('utf-8')).hexdigest()
        with open(filepath, 'w') as f:
            json.dump(self.parameters, f, indent=4)
            f.write(f"\n# Checksum: {checksum}")
        self.locked = True

    def clear(self):
        self.parameters = {}
        self.locked = False
        self.validated = False
        self.parameter_list = []

def _red(text: str):
    return colorama.Fore.RED + text + colorama.Style.RESET_ALL

def _green(text: str):
    return colorama.Fore.GREEN + text + colorama.Style.RESET_ALL

def _yellow(text: str):
    return colorama.Fore.YELLOW + text + colorama.Style.RESET_ALL

def _blue(text: str):
    return colorama.Fore.BLUE + text + colorama.Style.RESET_ALL

def _magenta(text: str):
    return colorama.Fore.MAGENTA + text + colorama.Style.RESET_ALL

def open_close_many_valves(auto: Controller, valves_to_open: list[Valve], valves_to_close: list[Valve]):
    commands = {}
    # Open valves to open
    for valve in valves_to_open:
        if valve.normally_open:
            commands[valve.cmd_chan] = 0
        else:
            commands[valve.cmd_chan] = 1
    # Close valves to close
    for valve in valves_to_close:
        if valve.normally_open:
            commands[valve.cmd_chan] = 1
        else:
            commands[valve.cmd_chan] = 0

    auto.set(commands)


def close_all(auto: Controller, valves: list[Valve]):
    commands = {}
    # Open valves to open
    for valve in valves:
        if valve.normally_open:
            commands[valve.cmd_chan] = 1
        else:
            commands[valve.cmd_chan] = 0
    auto.set(commands)


def open_all(auto: Controller, valves: list[Valve]):
    commands = {}
    for valve in valves:
        if valve.normally_open:
            commands[valve.cmd_chan] = 0
        else:
            commands[valve.cmd_chan] = 1
    auto.set(commands)

def wait(duration: float, increment: float = 1, offset: float = 0, precision: float = 0, message: str = None, color = None):
    """
    Prints the time remaining in the wait.
        - duration: how long to wait in seconds
        - increment: how long to wait between prints
        - offset: added to each print statement
        - precision: how many decimal points to print
        - message: printed at the end
    Will not print any increments less than `increment`
    """
    if color is not None:
        prestring = color
        poststring = colorama.Style.RESET_ALL
    else:
        prestring = ""
        poststring = ""
    while duration >= increment:
        print(prestring + f"{round(offset + duration, precision)}" + poststring)
        time.sleep(increment)
        duration -= increment
    if duration > 0:
        time.sleep(duration)
    if message is not None:
        print(message)
