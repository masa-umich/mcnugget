#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax==0.46.0",
#     "yaspin",
#     "termcolor",
#     "pyyaml",
# ]
# ///

from termcolor import colored
from yaspin import yaspin

# fun spinner while we load packages
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

# 3rd party modules
import synnax as sy
from synnax.control.controller import Controller

# standard modules
import argparse
from typing import List
from collections import deque
import statistics
import time

# our modules
from configuration import Configuration

REFRESH_RATE = 50 # Hz
loop = sy.Loop(sy.Rate.HZ * 2 * REFRESH_RATE) 
# Standard refresh rate for all checks (doubled because of shannon sampling thereom)

# Mutli-state enum
class State:
    INIT: bool = False
    PRESS_FILL: bool = False
    OX_FILL: bool = False
    PRE_PRESS: bool = False
    QDS: bool = False

# Weighted running average
class average_ch:
    avg: float
    initialized: bool
    alpha: float

    def __init__(self, window: int):
        # Alpha approximates a window of N items: alpha = 2 / (N + 1)
        self.alpha = 2.0 / (window + 1)
        self.avg = 0.0
        self.initialized = False

    def add(self, value: float) -> None:
        if not self.initialized:
            self.avg = value
            self.initialized = True
        else:
            # Standard EWMA formula
            self.avg = (value * self.alpha) + (self.avg * (1 - self.alpha))

    def get(self) -> float:
        return self.avg

# Helper function to vote & average multiple sensor readings
def sensor_vote_values(input: List[float], threshold: float) -> float:
    if not input:
        return None
    if len(input) == 1:
        return input[0]
    
    median_val = statistics.median(input)

    trusted_sensors = [x for x in input if abs(x - median_val) <= threshold]

    if not trusted_sensors:
        return median_val
    
    return sum(trusted_sensors) / len(trusted_sensors)


def sensor_vote(ctrl: Controller, channels: List[str], threshold: float) -> float:
    ctrl.wait_until_defined(channels)
    values: List[float] = []
    for ch in channels:
        values.append(ctrl.get(ch))
    return sensor_vote_values(values, threshold)


# helper function to raise pretty errors
def error_and_exit(message: str, error_code: int = 1, exception=None) -> None:
    # TODO: close all valves and possibly open vents. Basically an "abort"
    spinner.stop()  # incase it's running
    if exception != None:  # exception is an optional argument
        print(exception)
    print(colored(message, "red", attrs=["bold"]))
    print(colored("Exiting", "red", attrs=["bold"]))
    exit(error_code)


@yaspin(text=colored("Logging onto Synnax cluster...", "yellow"))
def synnax_login(cluster: str) -> sy.Synnax:
    try:
        client = sy.Synnax(
            host=cluster,
            port=9090,
            username="synnax",
            password="seldon",
        )
    except Exception as e:
        error_and_exit(
            f"Could not connect to Synnax at {cluster}, are you sure you're connected?"
        )
    return client


# Allow the use to specify a config file which is not the default ("./config.yaml")
# And if verbose output should be enabled.
def parse_args() -> list:
    parser = argparse.ArgumentParser(
        description="The autosequence for preparring Limeight for launch!"
    )
    parser.add_argument(
        "-m",
        "--config",
        help="The file to use for channel config",
        default="config.yaml",
        type=str,
    )
    parser.add_argument(
        "-c",
        "--cluster",
        help="Specify a Synnax cluster to connect to",
        default="synnax.masa.engin.umich.edu",
        type=str,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Shold the program output extra debugging information",
        action="store_true",
    )  # Positional argument
    args = parser.parse_args()
    # check that if there was an alternate config file given, that it is at least a .yaml file
    if args.config != "config.yaml":
        if args.config.endswith(".yaml"):
            if args.verbose:
                print(colored(f"Using config from file: {args.config}", "yellow"))
        else:
            error_and_exit(
                f"Invalid specified config file: {args.config}, must be .yaml file"
            )
    return args

# Helper function to handle all abort cases
def abort(ctrl: Controller, state: State):
    # TODO: aborting lol
    ctrl.release()
    print(colored("Autosequence has released control.", "green"))

# TODO: Add check for COPV temperature
def press_ittr(ctrl: Controller, copv_1, copv_2, copv_3, press_iso_X, press_fill_iso, press_rate):
    start_time = time.monotonic()
    end_time = start_time + 60 # one minute after start
    copv_pres = average_ch(50) # 50 sample standard window

    # Average over 1 second to get the starting pressure
    for i in range(50):
        copv_pres.add(sensor_vote(ctrl, [copv_1, copv_2, copv_3], 40))
    start_pres = copv_pres.get()
    
    target_pres = start_pres + press_rate

    ctrl[press_fill_iso] = True
    ctrl[press_iso_X] = True

    while loop.wait():
        now = time.monotonic()
        copv_pres.add(sensor_vote(ctrl, [copv_1, copv_2, copv_3], 40))
        if ((copv_pres.get() >= target_pres) or (now >= end_time)) and (ctrl[press_iso_X] == True):
            ctrl[press_iso_X] = False # close press iso
        if (now >= end_time):
            ctrl[press_fill_iso] = False
            return

def press_fill(ctrl: Controller, config: Configuration) -> None:
    copv_1 = config.mappings.COPV_PT_1
    copv_2 = config.mappings.COPV_PT_2
    copv_3 = config.mappings.Fuel_Manifold_PT_1

    copv_pres = average_ch(100) # 50 sample standard window
    while True:
        copv_pres.add(sensor_vote(ctrl, [copv_1, copv_2, copv_3], 40))
        print(copv_pres.get())

def ox_fill(ctrl: Controller, config: Configuration) -> None:
    pass

def pre_press(ctrl: Controller, config: Configuration) -> None:
    pass

def qds(ctrl: Controller, config: Configuration) -> None:
    pass

def command_interface(ctrl: Controller, auto_state: State, config: Configuration) -> None:
    print(colored(
    """
    Welcome to the Limelight Autosequence!
    Commands:
        - press fill
        - ox fill
        - pre press
        - qds
        - quit
    """
    ))

    try:
        while (True):
            # TODO: add a wait until defined check on all channels
            # and abort if any aren't
            command = input(colored("> ", "green"))
            match command:
                case "press fill":
                    auto_state.PRESS_FILL = True
                    press_fill(ctrl, config)
                case "ox fill":
                    auto_state.OX_FILL = True
                    ox_fill(ctrl, config)
                case "pre press":
                    auto_state.PRE_PRESS = True
                    pre_press(ctrl, config)
                case "qds":
                    auto_state.QDS = True
                    qds(ctrl, config)
                case "quit":
                    abort(ctrl, auto_state)
                    break
    except KeyboardInterrupt:
        print(colored("Keyboard interrupt detected, aborting!", "red", attrs=["bold"]))
        abort(ctrl, auto_state)


def main() -> None:
    auto_state = State()
    auto_state.INIT = True

    args = parse_args()
    config = Configuration(args.config)
    client = synnax_login(args.cluster)
    print(colored("Initialization Complete!", "green"))

    write_chs = config.get_valves()
    read_chs = config.get_valves() + config.get_pts() + config.get_tcs()

    with client.control.acquire(
        name="Launch Autosequence",
        write_authorities=1, # 1 is the default console authority
        write=write_chs,
        read=read_chs
    ) as ctrl:
        command_interface(ctrl, auto_state, config)
        
    print(colored("Autosequence complete! have a nice day :)", "green"))
    exit(0)


if __name__ == "__main__":
    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports
    try:
        main()
    except KeyboardInterrupt:  # Abort cases also rely on this, but Python takes the closest exception catch inside nested calls
        error_and_exit("Keyboard interrupt detected")
    # except Exception as e:  # catch-all uncaught errors
        # error_and_exit("Uncaught exception!", exception=e)
