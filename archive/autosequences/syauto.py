from synnax.control.controller import Controller
import time
import colorama
import json
import hashlib

"""
# VALVES
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

# COLORS
- red: errors or abort cases
- green: success and nominal behavior
- yellow: warnings and off-nominal behavior
- magenta: user input and feedback
- blue: meta-information about the system
- gray: debugging information
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

    def __repr__(self):
        return f"{self.key}={self.value}"

    def update(self, value):
        if self.type is not None and not isinstance(value, self.type):
            raise ValueError(f"Parameter {self.key} is not of type {self.type}")
        self.value = value
        self.validated = False

class Config:
    """
    A class to manage a group of Parameters and enforce good practices for loading and validating them. Four levels of validation are possible:
        1. List checking: checks that the the whole list of parameters is present
        2. Type checking: checks that each parameter is of the correct type
        3. Checksum checking: checks that the checksum of the file matches the checksum of the loaded parameters
        4. Manual checking: explicitly validates each parameter with SRE, COP, TC
    Default is 1 and 2 only
    """
    def __init__(self):
        self.parameter_list = None
        self.parameters = None
        self.locked = False
        self.validated = False

    ### editing parameters below here ###
    def __getitem__(self, key):
        p = self.parameters.get(key)
        if p is None:
            raise ValueError(f"Parameter {key} not found in config file")
        return p.value

    def __setitem__(self, key, value, override: bool = False):
        if self.locked and not override:
            raise ValueError(f"Config is locked and cannot be updated")
        if key not in self.parameters:
            if override:
                self.parameters[key] = Parameter(key, value)
            else:
                raise ValueError(f"Parameter {key} not found in config file")
        self.parameters[key].update(value)
        self.validated = False
    ### editing parameters above here ###

    def _list_check(self):
        """
        Checks that every parameter in the parameter list is present in the parameters dictionary
        """
        for p in self.parameter_list:
            if p not in self.parameters.keys():
                raise ValueError(f"Parameter {p} is missing")

    def _type_check(self):
        """
        Checks that every parameter in the parameter list is of the correct type
        """
        for p in self.parameters.values():
            if p.type is not None and not isinstance(p.value, eval(p.type)):
                raise ValueError(f"Parameter {p.key} is not of type {p.type}")

    def _checksum_check(self):
        """
        Asserts the correct checksum for the given parameter dictionary
        """
        _checksum = hashlib.sha256(json.dumps(str(self.parameters)).encode()).hexdigest()
        if self.checksum != _checksum:
            raise ValueError(f"Checksum mismatch: {self.checksum} != {_checksum}")

    def _manual_check(self):
        try:
            sre = input(f"{_gray('Type ')}{_magenta('sre')}{_gray(' to verify there is a Software Responsible Engineer present: ')}" + colorama.Fore.MAGENTA).strip().lower()
            cop = input(f"{_gray('Type ')}{_magenta('cop')}{_gray(' to verify there is a Console Operator present: ')}" + colorama.Fore.MAGENTA).strip().lower()
            tc = input(f"{_gray('Type ')}{_magenta('tc')}{_gray(' to verify there is a Test Conductor present: ')}" + colorama.Fore.MAGENTA).strip().lower()
            if sre != "sre" or cop != "cop" or tc != "tc":
                raise ValueError(f"Manual check failed - SRE, COP, and TC must all be present")
            for p in self.parameters.values():
                input(f"{_gray('Press ')}{_magenta('enter')}{_gray(' to verify that ')}{_green(p.key)}{_gray(' is set to ')}{_green(p.value)} ")
            return True
        except Exception as e:
            print(_red(f"Manual check failed: {e}"))
            return False

    def export(self, filepath):
        with open(filepath, 'w') as f:
            OUT_DICT = {}
            OUT_DICT["checksum"] = self.checksum
            OUT_DICT["validated"] = self.validated
            OUT_DICT["parameter_list"] = self.parameter_list
            OUT_DICT["parameters"] = {}
            for p in self.parameters.values():
                OUT_DICT["parameters"][p.key] = f"{p.value}|{"." if p.type is None else p.type.__name__}|{"." if p.explicit else True}"
            OUT_DICT["parameters"] = json.dumps(OUT_DICT["parameters"], indent=4)
            f.write(json.dumps(OUT_DICT, indent=4))

    def load(self, filepath: str, override: bool = False):
        """
        Loads the config file (from filepath if specified, otherwise manually)
        """
        if self.parameters is not None and not override:
            raise ValueError(f"Pass in the override=True flag if you want to overwrite an existing configuration")
        
        self.parameter_list = []
        self.parameters = {}
        self.validated = False
        self.checksum = None

        with open(filepath, 'r') as f:
            IN_DICT = json.load(f)
            self.checksum = IN_DICT["checksum"]
            self.validated = IN_DICT["validated"]
            self.parameter_list = list(IN_DICT["parameter_list"])
            for _key, _info in IN_DICT["parameters"].items():
                _value, _type, _explicit = _info.split("|")
                if _type == None or _type == "None" or _type == "" or _type == ".":
                    _type = None
                if _explicit == False or _explicit == "False" or _explicit == "" or _explicit == ".":
                    _explicit = False
                self.parameters[_key] = Parameter(_key, _value, _type, _explicit)

    def validate(self, type_check: bool = True, list_check: bool = True, checksum_check: bool = False, manual_check: bool = False):
        """
        Validates the loaded config
        type_check: whether to check the types of the parameters
        list_check: whether to check the parameter list
        lock_check: whether to check the checksum of the config file
        manual_check: whether to check the parameters manually
        """
        if type_check:
            self._type_check()
        if list_check:
            self._list_check()
        if checksum_check:
            self._checksum_check()
        if manual_check:
            self._manual_check()
        self.validated = True

    def lock(self, filepath: str, override: bool = False):
        """
        Generates a checksum for the config file and saves it to the file
        """
        if not self.validated and not override:
            raise ValueError(f"Cannot save a non-validated config file")
        checksum = hashlib.sha256(json.dumps(self.parameters).encode()).hexdigest()
        with open(filepath, 'w') as f:
            f.write(json.dumps(self.parameters, indent=4))
            f.write(f"# Checksum: {checksum}\n")
        self.locked = True

    def view(self):
        print(f"{_gray('Config is ')}{_red('locked') if self.locked else _green('unlocked')}")
        print(f"{_gray("Config is ")}{_green('validated') if self.validated else _red('not validated')}")
        print(_gray("Parameters:"))
        for p in self.parameters.values():
            print(f"{_green(p.key)}{_gray(": ")}{_green(p.value)}")

    def clear(self):
        self.parameter_list = []
        self.parameters = {}
        self.validated = False
        self.locked = False

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

def _gray(text: str):
    return colorama.Fore.LIGHTBLACK_EX + text + colorama.Style.RESET_ALL

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
