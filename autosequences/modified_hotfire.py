import syauto
import time
import synnax
import statistics
import sys
import threading
import colorama
import os

"""
Change these parameters by running the autosequence and choosing `config` mode.
- will attempt to load appropriate (sim/real/checkout)_config.json
The real_config_json file which is used for tests has a corresponding real_config.json.lock file. When
attempting to run a `real` test, if the files do not match, the program will require validation/override.
Validation requires SRE/COP/TC to be present and confirm each test parameters.
"""

def determine_config(mode: str) -> syauto.Config:
    """
    Determines the config file to load based on the mode. Will not return the config file unless
    - config file is valid
    - matching lock file is valid (for mode==real)
    """
    c = syauto.Config()
    if mode == "real":
        c.load("hotfire_config.json")
        c.validate(checksum=True)
    elif mode == "checkout":
        c.load("checkout_config.json")
        c.validate()
    elif mode == "sim":
        c.load("sim_config.json")
        c.validate()
    else:
        print(red(f"ERROR: Invalid mode {mode}"))
        exit(1)
    return c

def edit_config():
    def find_configs() -> list[str]:
        confs = []
        for file in os.listdir("./config/"):
            if file.endswith(".json") and file != "lock":
                confs.append(file)
        return confs
    def filepath(config: str) -> str:
        return os.path.join(os.path.dirname(__file__), "config", config)
    try:
        print(green("Entering config editor..."))
        c = syauto.Config()
        config_list = find_configs()
        print(green("commands: (exit, list, view, edit, validate, lock, help)"))
        print(green(f"available configs: {config_list}"))
        usr = ""
        while usr != "exit":
            usr = input(blue("$ ")).strip().lower().split(" ")
            print(usr)
            command = usr[0]
            if len(usr) > 1:
                config = usr[1]

            if command == "help":
                print("combine a command with a config name to perform an action - example:")
                print(blue("edit sim"))
                print("^ will allow you to edit the sim.json config file")
                print("exit - exit the config editor")
                print("list - list all available configs")
                print("view - view a config")
                print("edit - edit config values manually")
                print("validate - validate a config (requires SRE/COP/TC)")
                print("lock - lock a config so it cannot be edited")
            
            if command == "list":
                config_list = find_configs()
                print(green("available configs: " + str(config_list)))

            elif command == "view":
                c.clear()
                c.load(filepath(config))
                c.view()
            
            elif command == "edit":
                c.clear()
                c.load(filepath(config))
                c.view()
                while _input != "done":
                    _input = input(blue("enter <parameter>:<value> to set <parameter> to <value>, or done to finish editing: ")).strip().lower()
                    if _input == "done":
                        break
                    try:
                        param, value = _input.split(":")
                        c[param] = value
                    except ValueError as ve:
                        print(red(f"Invalid input: {ve}"))
                        continue

            elif command == "validate":
                if config == "real" or config == "hotfire":
                    c.clear()
                    c.load(filepath(config))
                    c.validate(checksum=True, manual=True)
                    

            elif command == "lock":
                pass
            elif command == "exit":
                print(green("Exiting config editor..."))
            else:
                print(red(f"Unknown command: {command}"))
    except KeyboardInterrupt:
        print(red("\nTerminating config editor..."))

FIRST_MPV = "first_mpv"
OX_PREPRESS_TARGET = "ox_prepress_target"
OX_PREPRESS_MARGIN = "ox_prepress_margin"
OX_PREPRESS_ABORT_PRESSURE = "ox_prepress_abort_pressure"
FUEL_PREPRESS_TARGET = "fuel_prepress_target"
FUEL_PREPRESS_MARGIN = "fuel_prepress_margin"
FUEL_PREPRESS_ABORT_PRESSURE = "fuel_prepress_abort_pressure"
BURN_DURATION = "burn_duration"
PURGE_DURATION = "purge_duration"
IGNITER_LEAD = "igniter_lead"
END_PREPRESS_LEAD = "end_prepress_lead"
OX_MPV_TIME = "ox_mpv_time"
FUEL_MPV_TIME = "fuel_mpv_time"
MPV_DELAY = "mpv_delay"
FUEL_DOME_LEAD = "fuel_dome_lead"
OX_DOME_LEAD = "ox_dome_lead"
RETURN_LINE_LEAD = "return_line_lead"

TEST_PARAMS_LIST = [
    FIRST_MPV,                      # which MPV opens first
    OX_PREPRESS_TARGET,             # target pressure for ox prepress
    OX_PREPRESS_MARGIN,             # +/- to determine bang-bang bounds
    OX_PREPRESS_ABORT_PRESSURE,     # auto-abort pressure
    FUEL_PREPRESS_TARGET,           # target pressure for fuel prepress
    FUEL_PREPRESS_MARGIN,           # +/- to determine bang-bang bounds
    FUEL_PREPRESS_ABORT_PRESSURE,   # auto-abort pressure
    BURN_DURATION,                  # how long MPVs stay open
    PURGE_DURATION,                 # how long MPV purge stays open
    IGNITER_LEAD,                   # T-[] to energize igniter
    END_PREPRESS_LEAD,              # T-[] to end prepress
    OX_MPV_TIME,                    # time between opening Ox MPV and Ox reaching the chamber
    FUEL_MPV_TIME,                  # time between opening Fuel MPV and Fuel reaching the chamber
    MPV_DELAY,                      # extra time between opening MPVs so one propellant reaches chamber first
    FUEL_DOME_LEAD,                 # T-[] to open fuel dome iso
    OX_DOME_LEAD,                   # T-[] to open ox dome iso
    RETURN_LINE_LEAD,               # T-[] to open ox return line
]

# channels - confirm ICD is up to date and check against the ICD
# these are also stored/checked in the config but are referenced from here (will warn if different)
OX_DOME_ISO = "ox_dome_iso"
OX_MPV = "ox_mpv"
OX_PREVALVE = "ox_prevalve"
OX_VENT = "ox_vent"
FUEL_MPV = "fuel_mpv"
FUEL_PREVALVE = "fuel_prevalve"
FUEL_DOME_ISO = "fuel_dome_iso"
FUEL_VENT = "fuel_vent"
FUEL_PREPRESS = "fuel_prepress"
PRESS_ISO = "press_iso"
IGNITER = "igniter"
MPV_PURGE = "mpv_purge"
OX_RETURN_LINE = "ox_return_line"

VALVES = [
    OX_DOME_ISO,
    OX_MPV,
    OX_PREVALVE,
    OX_VENT,
    FUEL_MPV,
    FUEL_PREVALVE,
    FUEL_DOME_ISO,
    FUEL_VENT,
    FUEL_PREPRESS,
    PRESS_ISO,
    IGNITER,
    MPV_PURGE,
    OX_RETURN_LINE,
]

OX_TANK_1 = "ox_tank_1"
OX_TANK_2 = "ox_tank_2"
OX_TANK_3 = "ox_tank_3"
FUEL_TANK_1 = "fuel_tank_1"
FUEL_TANK_2 = "fuel_tank_2"
FUEL_TANK_3 = "fuel_tank_3"

PTS = [
    OX_TANK_1,
    OX_TANK_2,
    OX_TANK_3,
    FUEL_TANK_1,
    FUEL_TANK_2,
    FUEL_TANK_3,
]

NORMALLY_OPEN_VALVES = [
    OX_MPV,
    FUEL_MPV,
    OX_VENT,
    FUEL_VENT,
]

def PT(channel: str | int) -> str:
    if type(channel) == str:
        return f"gse_pt_{PTS[channel]}_avg"
    return f"gse_pt_{str(channel)}_avg"

def VALVE(channel: str | int) -> str:
    if type(channel) == str:
        return f"gse_vlv_{VALVES[channel]}"
    return f"gse_vlv_{str(channel)}"


def STATE(channel: str | int) -> str:
    if type(channel) == str:
        return f"gse_state_{VALVES[channel]}"
    return f"gse_state_{str(channel)}"

# characters aint free
red = syauto._red
green = syauto._green
yellow = syauto._yellow
blue = syauto._blue
magenta = syauto._magenta

class Autosequence():
    def __init__(self):
        """
        The following block runs on initialization, and handles the cluster connection
        and initialization of Valve objects. All actual behavior is handled by other functions.
        """
        try:
            self.mode = input(colorama.Fore.BLUE + "Enter mode (sim/real/checkout/config): " + colorama.Fore.MAGENTA).strip().lower()
            if self.mode == "config":
                edit_config()
                exit(0)
            elif self.mode == "coldflow" or self.mode == "hotfire" or self.mode == "real":
                self.mode = "real"
                address = "141.212.192.160"
            elif self.mode == "checkout":
                self.mode = "checkout"
                address = "141.212.192.160"
            elif self.mode == "sim" or self.mode == "":
                self.mode = "sim"
                address = "localhost"
            else:
                print(red("Bestie what are you trying to do? If it's a typo, just try again, we're gonna close to program for now though <3"))
                # courtesy of ramona ^
                exit()
            
            self.client = synnax.Synnax(
                host=address,
                port=9090,
                username="synnax",
                password="seldon",
                secure=False,
            )
            print(green("Connected to cluster at " + address))

            self.config = determine_config()

            if len(sys.argv) == 1:
                self._using_ox = True
                self._using_fuel = True
            elif len(sys.argv) == 2:
                self._using_ox = sys.argv[1].lower() == "ox"
                self._using_fuel = sys.argv[1].lower() == "fuel"

            if self._using_fuel:
                print(green("USING FUEL"))
            else:
                print(red("NOT USING FUEL"))
            if self._using_ox:
                print(green("USING OX"))
            else:
                print(red("NOT USING OX"))

            if FIRST_MPV == "ox":
                print(green("FIRST MPV: OX"))
            elif FIRST_MPV == "fuel":
                print(green("FIRST MPV: FUEL"))

            self.read_channels = []
            self.write_channels = []
            for channel in VALVE_INDICES.values():
                self.read_channels.append(STATE(channel))
                self.write_channels.append(VALVE(channel))
            for channel in PT_INDICES.values():
                self.read_channels.append(PT(channel))

            self.controller = self.client.control.acquire("Hotfire Autosequence", self.read_channels, self.write_channels, 232)
        
        except KeyboardInterrupt:
            print(red("\nTerminating autosequence..."))
            self.shutdown()

    def initialize(self) -> bool:
        """
        This function exists to make sure things aren't messed up.
            - no negative wait times
            - no invalid channels
            - confirm test specs
            - checks starting state
        Also sets up the Autosequence to run with the specified Controller
        """
        print(yellow("Initializing..."))
        print(yellow("Checking for negative wait times..."))
        self.times = [
            ("igniter_open", IGNITER_LEAD),
            ("igniter_close", IGNITER_LEAD - 1),
            ("end_prepress", END_PREPRESS_LEAD),
            ("ox_dome", OX_DOME_LEAD),
            ("fuel_dome", FUEL_DOME_LEAD),
            ("return_line", RETURN_LINE_LEAD),
            ("first_mpv", FIRST_MPV_LEAD),
            ("second_mpv", 0),
            ("start_ignition_detection", IGNITER_LEAD - 0.01),
            ("check_ignition_detection", max(OX_DOME_LEAD, FUEL_DOME_LEAD)),
        ]
        self.times = list(reversed(sorted(self.times, key=lambda x: x[1])))
        self.firing_sequence = []
        # calculate order + delays for events, sum should be 10 seconds
        for i, (cmd, t_minus) in enumerate(self.times):
            if i == 0:
                self.firing_sequence.append((cmd, 10 - t_minus, t_minus))
            else:
                self.firing_sequence.append((cmd, self.times[i-1][1] - t_minus, t_minus))
        
        print(f"TIMES: {self.times}")
        print(f"FIRING SEQUENCE: {self.firing_sequence}")

        sequence_time = sum(event[1] for event in self.firing_sequence)
        print(f"Total time for firing sequence is {sequence_time} seconds")
        if not (abs(sequence_time - 10) < 0.0001):
            print(red(f"ERROR: Firing sequence should be 10 seconds total, not {sequence_time} seconds"))
            exit(1)

        print(yellow("Checking valves..."))
        self.ox_dome_iso = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("ox_dome_iso"),
            ack=STATE("ox_dome_iso"),
            normally_open="ox_dome_iso" in NORMALLY_OPEN_VALVES,
        )
        self.ox_mpv = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("ox_mpv"),
            ack=STATE("ox_mpv"),
            normally_open="ox_mpv" in NORMALLY_OPEN_VALVES,
        )
        self.ox_prevalve = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("ox_prevalve"),
            ack=STATE("ox_prevalve"),
            normally_open="ox_prevalve" in NORMALLY_OPEN_VALVES,
        )
        self.ox_vent = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("ox_vent"),
            ack=STATE("ox_vent"),
            normally_open="ox_vent" in NORMALLY_OPEN_VALVES,
        )

        self.fuel_mpv = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("fuel_mpv"),
            ack=STATE("fuel_mpv"),
            normally_open="fuel_mpv" in NORMALLY_OPEN_VALVES,
        )
        self.fuel_prevalve = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("fuel_prevalve"),
            ack=STATE("fuel_prevalve"),
            normally_open="fuel_prevalve" in NORMALLY_OPEN_VALVES,
        )
        self.fuel_dome_iso = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("fuel_dome_iso"),
            ack=STATE("fuel_dome_iso"),
            normally_open="fuel_dome_iso" in NORMALLY_OPEN_VALVES,
        )
        self.fuel_vent = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("fuel_vent"),
            ack=STATE("fuel_vent"),
            normally_open="fuel_vent" in NORMALLY_OPEN_VALVES,
        )
        self.fuel_prepress = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("fuel_prepress"),
            ack=STATE("fuel_prepress"),
            normally_open="fuel_prepress" in NORMALLY_OPEN_VALVES,
        )

        self.press_iso = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("press_iso"),
            ack=STATE("press_iso"),
            normally_open="press_iso" in NORMALLY_OPEN_VALVES,
        )
        self.igniter = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("igniter"),
            ack=STATE("igniter"),
            normally_open="igniter" in NORMALLY_OPEN_VALVES,
        )
        self.mpv_purge = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("mpv_purge"),
            ack=STATE("mpv_purge"),
            normally_open="mpv_purge" in NORMALLY_OPEN_VALVES,
        )
        self.ox_return_line = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("ox_return_line"),
            ack=STATE("ox_return_line"),
            normally_open="ox_return_line" in NORMALLY_OPEN_VALVES,
        )

        if FIRST_MPV == "ox":
            self.first_mpv = self.ox_mpv
            self.second_mpv = self.fuel_mpv
        elif FIRST_MPV == "fuel":
            self.first_mpv = self.fuel_mpv
            self.second_mpv = self.ox_mpv
        else:
            print(red(f"ERROR: FIRST_MPV must be either 'ox' or 'fuel', not {FIRST_MPV}"))

        valves = [
            self.ox_dome_iso,
            self.ox_mpv,
            self.ox_prevalve,
            self.ox_vent,
            self.fuel_mpv,
            self.fuel_prevalve,
            self.fuel_dome_iso,
            self.fuel_vent,
            self.fuel_prepress,
            self.press_iso,
            self.igniter,
            self.mpv_purge,
        ]
        if len([valve for valve in valves if valve.normally_open]) != len(NORMALLY_OPEN_VALVES):
            print(red("ERROR: Unable to find some normally open valves, please fix."))
            exit(1)
        
        print(yellow("Checking for invalid channels..."))
        for channel in self.read_channels + self.write_channels:
            try:
                self.client.channels.retrieve(channel)
            except synnax.exceptions.NotFoundError:
                print(red(f"ERROR: Unable to find channel {channel}"))
                exit(1)

        time.sleep(0.25)  # for controller to wake up
        print(yellow("Checking starting state..."))
        # check valves which should be open
        if self.controller[STATE("ox_prevalve")] == 0:
            input(f"{red('Ox prevalve')} {yellow('is not open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("fuel_prevalve")] == 0:
            input(f"{red('Fuel prevalve')} {yellow('is not open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("press_iso")] == 0:
            input(f"{red('Press Iso')} {yellow('is not open, press enter to manually override or ctrl-c to stop.')}")

        # check valves which should be closed
        if self.controller[STATE("ox_mpv")] == 0: # normally open
            input(f"{red('Ox MPV')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("fuel_mpv")] == 0: # normally open
            input(f"{red('Fuel MPV')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("ox_dome_iso")] == 1:
            input(f"{red('Ox Dome Iso')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("fuel_dome_iso")] == 1:
            input(f"{red('Fuel Dome Iso')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("ox_vent")] == 0: # normally open
            input(f"{red('Ox vent')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("fuel_vent")] == 0: # normally open
            input(f"{red('Fuel vent')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("fuel_prepress")] == 1:
            input(f"{red('Fuel prepress')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("mpv_purge")] == 1:
            input(f"{red('MPV purge')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("ox_return_line")] == 0:
            input(f"{red('Ox return line')} {yellow('is closed, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("igniter")] == 1:
            input(red(f"wtf man why you got the igniter on? just abort bro just abort "))

        self.fuel_upper_bound = FUEL_PREPRESS_TARGET + FUEL_PREPRESS_MARGIN
        self.fuel_lower_bound = FUEL_PREPRESS_TARGET - FUEL_PREPRESS_MARGIN
        self.fuel_abort_pressure = FUEL_PREPRESS_ABORT_PRESSURE
        self.ox_upper_bound = OX_PREPRESS_TARGET + OX_PREPRESS_MARGIN
        self.ox_lower_bound = OX_PREPRESS_TARGET - OX_PREPRESS_MARGIN
        self.ox_abort_pressure = OX_PREPRESS_ABORT_PRESSURE

        self.fuel_prepress_running = threading.Event()
        self.ox_prepress_running = threading.Event()
        self.igniter_verified = threading.Event()

        self.fuel_prepress_thread = threading.Thread()
        self.ox_prepress_thread = threading.Thread()

        print(yellow("Checking test parameters..."))
        self.load_config()
        # firing sequence

        FIRST_MPV = self.config["FIRST_MPV"]  # set as either "ox" or "fuel"
        OX_MPV_TIME = self.config["OX_MPV_TIME"]
        FUEL_MPV_TIME = self.config["FUEL_MPV_TIME"]
        MPV_DELAY = self.config["MPV_DELAY"]
        BURN_DURATION = self.config["BURN_DURATION"]
        PURGE_DURATION = self.config["PURGE_DURATION"]
        FUEL_DOME_LEAD = self.config["FUEL_DOME_LEAD"]
        OX_DOME_LEAD = self.config["OX_DOME_LEAD"]
        RETURN_LINE_LEAD = self.config["RETURN_LINE_LEAD"]

        # All of these delays should be in seconds backwards from T=0
        IGNITER_LEAD = self.config["IGNITER_LEAD"]
        END_PREPRESS_LEAD = self.config["END_PREPRESS_LEAD"]

        # prepress
        OX_PREPRESS_TARGET = self.config["OX_PREPRESS_TARGET"]
        OX_PREPRESS_MARGIN = self.config["OX_PREPRESS_MARGIN"]  # +/- from the target
        OX_PREPRESS_ABORT_PRESSURE = self.config["OX_PREPRESS_ABORT_PRESSURE"]
        FUEL_PREPRESS_TARGET = self.config["FUEL_PREPRESS_TARGET"]
        FUEL_PREPRESS_MARGIN = self.config["FUEL_PREPRESS_MARGIN"]  # +/- from the target
        FUEL_PREPRESS_ABORT_PRESSURE = self.config["FUEL_PREPRESS_ABORT_PRESSURE"]
        FIRST_MPV_LEAD = max(FUEL_MPV_TIME, OX_MPV_TIME) - min(FUEL_MPV_TIME, OX_MPV_TIME) + MPV_DELAY

        invalid = False
        for p in [FIRST_MPV, OX_PREPRESS_TARGET, OX_PREPRESS_MARGIN, OX_PREPRESS_ABORT_PRESSURE,
                  FUEL_PREPRESS_TARGET, FUEL_PREPRESS_MARGIN, FUEL_PREPRESS_ABORT_PRESSURE,
                  BURN_DURATION, PURGE_DURATION, IGNITER_LEAD, END_PREPRESS_LEAD,
                  OX_MPV_TIME, FUEL_MPV_TIME, MPV_DELAY, FUEL_DOME_LEAD, OX_DOME_LEAD,
                  RETURN_LINE_LEAD]:
            if p is None:
                print(red(f"ERROR: {p} was not loaded by the config file."))
                invalid = True
        if invalid:
            exit(1)

        if self.mode == "real" or self.mode == "sim":
            print(green(f"BURN_DURATION: ") + magenta(str(BURN_DURATION)))
            print(green(f"OX_PREPRESS_TARGET: ") + magenta(str(OX_PREPRESS_TARGET)))
            print(green(f"FUEL_PREPRESS_TARGET: ") + magenta(str(FUEL_PREPRESS_TARGET)))
            print(green(f"FIRST_MPV: ") + magenta(str(FIRST_MPV)))
            input(magenta("Press enter to confirm the test parameters listed above: "))

        print(green("All checks passed - initialization complete.\n"))
        return True

    def configure(self):
        """
        Walks through the configuration file and locks once everything is confirmed.
        """
        print("not implemented yet")
        exit(1)

    def prepress_wrapper(self, prepress, flag):
        while flag.is_set():
            prepress()
            time.sleep(0.1)

    def prepress_fuel(self) -> bool:
        fuel_tank_pressure = statistics.median([
            self.controller[PT("fuel_tank_1")],
            self.controller[PT("fuel_tank_2")],
            self.controller[PT("fuel_tank_3")]
        ])
        fuel_prepress_open = self.controller[STATE("fuel_prepress")]

        if fuel_prepress_open and (fuel_tank_pressure >= self.fuel_upper_bound):
            self.fuel_prepress.close()

        elif (not fuel_prepress_open) and (fuel_tank_pressure <= self.fuel_lower_bound):
            self.fuel_prepress.open()

        elif fuel_tank_pressure >= self.fuel_abort_pressure:
            self.prepress_abort()

    def prepress_ox(self) -> bool:
        ox_tank_pressure = statistics.median([
            self.controller[PT("ox_tank_1")],
            self.controller[PT("ox_tank_2")],
            self.controller[PT("ox_tank_3")]
        ])
        ox_dome_iso_open = self.controller[STATE("ox_dome_iso")]

        if ox_dome_iso_open and (ox_tank_pressure >= self.ox_upper_bound):
            self.ox_dome_iso.close()

        elif (not ox_dome_iso_open) and (ox_tank_pressure <= self.ox_lower_bound):
            self.ox_dome_iso.open()

        elif ox_tank_pressure >= self.ox_abort_pressure:
            self.prepress_abort()

    def main(self):
        """
        This function is the main thread which manages all the other
        parts of the autosequence. Minimal logic should be here.
        """
        try:
            self.initialize()
            prepress_delay = 3
            input(colorama.Fore.BLUE + f"Press enter to begin fuel prepress ({prepress_delay} second countdown) " + colorama.Style.RESET_ALL)
            syauto.wait(prepress_delay, color=colorama.Fore.BLUE)
            try:
                self.fuel_prepress_running.clear()
                self.fuel_prepress_running.set()
                self.fuel_prepress_thread = threading.Thread(name="prepress_fuel_thread", target=self.prepress_wrapper, args=(self.prepress_fuel,self.fuel_prepress_running,))
                print(green("Starting fuel prepress..."))
                self.fuel_prepress_thread.start()

                input(colorama.Fore.BLUE + f"Press enter to begin ox prepress ({prepress_delay} second countdown) " + colorama.Style.RESET_ALL)
                syauto.wait(prepress_delay, color=colorama.Fore.BLUE)

                self.ox_prepress_running.clear()
                self.ox_prepress_running.set()
                self.ox_prepress_thread = threading.Thread(name="prepress_ox_thread", target=self.prepress_wrapper, args=(self.prepress_ox,self.ox_prepress_running,))
                print(green("Starting ox prepress..."))
                self.ox_prepress_thread.start()

                firing = input(blue("Type `") + magenta("fire") + blue("` to begin firing sequence (10 second countdown) ") + colorama.Fore.MAGENTA).strip().lower()
                if firing == "fire":
                    print(green("Starting firing sequence..."))
                    try:
                        self.preignition_sequence()
                    except KeyboardInterrupt:
                        self.preignition_abort()
                    try:
                        self.postignition_sequence()
                    except KeyboardInterrupt:
                        self.postignition_abort()
                else:
                    self.prepress_abort()
            except KeyboardInterrupt:
                self.prepress_abort()
        except KeyboardInterrupt:
            print(red("\nTerminating autosequence..."))
            self.shutdown()
    
    def preignition_sequence(self):
        # igniter
        for command, delay, offset in self.firing_sequence:
            if delay > 0:
                if command == "first_mpv" or command == "second_mpv":
                    syauto.wait(delay, color=colorama.Fore.GREEN, offset=offset, increment=0.1, precision=1)
                else:
                    syauto.wait(delay, color=colorama.Fore.GREEN, offset=offset)
            if command == "igniter_open":
                self.igniter.open()
            elif command == "igniter_close":
                self.igniter.close()
            elif command == "end_prepress":
                self.fuel_prepress_running.clear()
                self.fuel_prepress_thread.join()
                if self.ox_prepress_thread.is_alive():
                    self.ox_prepress_running.clear()
                    self.ox_prepress_thread.join()
                self.ox_dome_iso.close()  # fallback
                self.fuel_prepress.close()  # fallback
            elif command == "ox_dome":
                self.ox_dome_iso.open()
            elif command == "fuel_dome":
                self.fuel_dome_iso.open()
            elif command == "return_line":
                self.ox_return_line.close()
            elif command == "first_mpv":
                self.first_mpv.open()
            elif command == "second_mpv":
                self.second_mpv.open()
            elif command == "start_ignition_detection":
                self.igniter_verification_thread = threading.Thread(
                    target=self.validate_ignition,
                    args=(IGNITER_LEAD - OX_DOME_LEAD,)
                )
                self.igniter_verification_thread.start()
                print(green("6"))  # otherwise no print
            elif command == "check_ignition_detection":
                self.igniter_verification_thread.join()
                lit = self.igniter_verified.is_set()
                if not lit:
                    print(red("Failed to verify igniter."))
                    self.preignition_abort()
            else:
                print(red(f"Unknown command: {command}"))

    def postignition_sequence(self):
        
        print(magenta(f"            * / //   /\n---IGNITION---***|||||::::>>>\n            * \\ \\\\   \\"))

        # burn
        syauto.wait(BURN_DURATION, color=colorama.Fore.GREEN)

        print(green("Purging..."))
        # post burn
        syauto.close_all(self.controller, [
            self.first_mpv, self.second_mpv, self.fuel_prevalve, self.ox_prevalve, self.press_iso,
        ])
        # syauto.open_all(self.controller, [
        #     self.ox_vent, self.fuel_vent, self.mpv_purge,
        # ])
        syauto.open_all(self.controller, [
            self.mpv_purge,
        ])
        syauto.wait(PURGE_DURATION, color=colorama.Fore.GREEN, message=green("Purge completed."))

        # post purge
        syauto.close_all(self.controller, [
            self.mpv_purge, self.ox_dome_iso, self.fuel_dome_iso,
        ])
        print(magenta("Firing sequence completed nominally."))
        self.shutdown(phoenix=True)

    def validate_ignition(self, window: float) -> bool:
        """
        Thread-safe input validation with proper timeout handling.
        Returns True iff Enter is pressed within `window` seconds.
        """
        input_received = threading.Event()
        self.igniter_verified.clear()

        def input_thread():
            try:
                sys.stdin.readline()
                input_received.set()
                if input_received.is_set():
                    return
            except:
                pass

        listener = threading.Thread(target=input_thread)
        listener.daemon = True  # to close thread if main exits

        start_time = time.time()
        listener.start()
        print(blue(f"Verify igniter by pressing Enter in the next {window} seconds."))
        while (time.time() - start_time) < window:
            if input_received.is_set():
                print(magenta("---IGNITER HAS BEEN VERIFIED---"))
                self.igniter_verified.set()
                return
            listener.join(0.001)
        input_received.set()
        return

    def prepress_abort(self):
        print(red("\nInitiating PREPRESS ABORT..."))
        self.fuel_prepress_running.clear()
        self.ox_prepress_running.clear()
        print(yellow("Terminating prepress..."))
        print(yellow("Closing valves..."))
        syauto.close_all(self.controller, [
            self.ox_dome_iso, self.fuel_prepress, self.press_iso,
        ])
        self.fuel_prepress_thread.join()
        if self.ox_prepress_thread.is_alive():
            self.ox_prepress_thread.join()
        self.shutdown()

    def preignition_abort(self):
        print(red("\nInitiating PREIGNITION ABORT..."))
        self.fuel_prepress_running.clear()
        self.ox_prepress_running.clear()
        print(red("Closing valves..."))
        syauto.close_all(self.controller, [
            self.fuel_prepress, self.press_iso,
        ])
        print(red("Opening vents..."))
        syauto.open_all(self.controller, [
            self.ox_vent, self.fuel_vent,
        ])
        syauto.wait(PURGE_DURATION, color=colorama.Fore.RED)
        print(red("Closing Dome Isos..."))
        syauto.close_all(self.controller, [
            self.ox_dome_iso, self.fuel_dome_iso,
        ])
        self.fuel_prepress_thread.join()
        self.ox_prepress_thread.join()
        self.shutdown()

    def postignition_abort(self):
        print(red("\nInitiating POSTIGNITION ABORT..."))
        print(red("Closing valves..."))
        syauto.close_all(self.controller, [
            self.press_iso, self.first_mpv, self.second_mpv, self.fuel_prevalve, self.ox_prevalve,
        ])
        print(red("Opening vents and purge..."))
        syauto.open_all(self.controller, [
            self.ox_vent, self.fuel_vent, self.mpv_purge,
        ])
        syauto.wait(PURGE_DURATION, color=colorama.Fore.RED, message=red("Purge completed"))
        print(red("Closing MPV Purge + Dome Isos..."))
        syauto.close_all(self.controller, [
            self.mpv_purge, self.ox_dome_iso, self.fuel_dome_iso,
        ])
        # postignition means prepress has already ended, so no thread merging
        self.shutdown()

    def shutdown(self, phoenix=False):
        try:
            self.controller.release()
            time.sleep(0.5)
        except AttributeError:
            pass
        print(green("Autosequence has released control."))
        if phoenix:
            f = open('phoenix.txt', 'r')
            print(colorama.Fore.RED + f.read() + colorama.Style.RESET_ALL)
            f.close()
        exit()

autosequence = Autosequence()
autosequence.main()