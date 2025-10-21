import colorama
import hashlib
import json

class Parameter:
    def __init__(self, key: str, value, param_type: type = None, explicit: bool = False, locked: bool = False):
        self.key = key
        self.value = value
        self.type = param_type
        self.explicit = explicit

    def __repr__(self):
        return f"{self.key}={self.value}"

    def update(self, value):
        if self.type is not None and not value.__class__ == self.type.__class__:
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
            if p.type is not None and not isinstance(p.value.__class__, p.type.__class__):
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
                OUT_DICT["parameters"][p.key] = f"{p.value}|{"." if p.type is None else p.type.__class__}|{"." if p.explicit else True}"
            OUT_DICT["parameters"] = json.dumps(OUT_DICT["parameters"], indent=4)
            f.write(json.dumps(OUT_DICT, indent=4))

    def load(self, filepath: str, override: bool = False):
        """
        Loads the config file (from filepath if specified, otherwise manually)
        """
        if self.parameters is not None and not override:
            raise ValueError(f"Pass in the override=True flag if you want to overwrite an existing configuration")
        if self.locked and not override:
            raise ValueError(f"Config is locked, please unlock before loading a new config file")

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
        self.checksum = hashlib.sha256(json.dumps(self.parameters).encode()).hexdigest()
        self.export(filepath)
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
