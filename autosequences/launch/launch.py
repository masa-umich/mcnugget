#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax==0.46.0",
#     "yaspin",
#     "termcolor",
#     "pyyaml",
#     "prompt-toolkit",
# ]
# ///

import threading
from termcolor import colored
from yaspin import yaspin

# fun spinner while we load packages
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

# 3rd party modules
import synnax as sy
from synnax.control.controller import Controller
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import ANSI

# standard modules
import argparse
from typing import List
import statistics
import time

# our modules
from configuration import Configuration

REFRESH_RATE = 50  # Hz
loop = sy.Loop(sy.Rate.HZ * 2 * REFRESH_RATE)
# Standard refresh rate for all checks (doubled because of shannon sampling thereom)

def log(*args, **kwargs):
    # Convert all arguments to strings and join them
    msg = " ".join(map(str, args))
    # Wrap in ANSI so prompt_toolkit parses termcolor codes correctly
    print_formatted_text(ANSI(msg), **kwargs)

class State:
    INIT: bool = False
    PRESS_FILL: bool = False
    OX_FILL: bool = False
    PRE_PRESS: bool = False
    QDS: bool = False

class Threads:
    press_fill_thread = threading.Thread()
    press_fill_thread_running = threading.Event()

    ox_fill_thread = threading.Thread()
    ox_fill_thread_running = threading.Event()

    pre_press_thread = threading.Thread()
    pre_press_thread_running = threading.Event()

    qds_thread = threading.Thread()
    qds_thread_running = threading.Event()

# Class to hold all useful autosequence objects
class Auto:
    ctrl: Controller
    config: Configuration
    state: State
    threads: Threads

    def __init__(self):
        self.ctrl = None
        self.config = None
        self.state = State()
        self.threads = Threads()

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

    def set_avg(self, input: float) -> None:
        self.avg = input

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
    # ctrl.wait_until_defined(channels)
    values: List[float] = []
    for ch in channels:
        values.append(ctrl.get(ch))
    return sensor_vote_values(values, threshold)


# Helper function to average and sensor vote multiple channels for a specified amount of time in seconds
def avg_and_vote_for(ctrl: Controller, channels: List[str], threshold: float, averaging_time: float) -> float:
    value = average_ch(round(REFRESH_RATE * averaging_time))
    end_time = sy.TimeStamp.now() + sy.TimeSpan.from_seconds(averaging_time)
    while (sy.TimeStamp.now() < end_time):
        value.add(sensor_vote(ctrl, channels, threshold))
    return value.get()

# helper function to raise pretty errors
def error_and_exit(message: str, error_code: int = 1, exception = None) -> None:
    # TODO: close all valves and possibly open vents. Basically an "abort"
    spinner.stop()  # incase it's running
    if exception != None:  # exception is an optional argument
        log(exception)
    log(colored(message, "red", attrs=["bold"]))
    log(colored("Exiting", "red", attrs=["bold"]))
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
    except Exception:
        error_and_exit(f"Could not connect to Synnax at {cluster}, are you sure you're connected?")
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
                log(colored(f"Using config from file: {args.config}", "yellow"))
        else:
            error_and_exit(f"Invalid specified config file: {args.config}, must be .yaml file")
    return args


# helper function that gets the "state" equivelant to a valve channel
def STATE(input: str) -> str:
    if "vlv" in input:
        return input.replace("vlv", "state")
    else:
        error_and_exit("Input to STATE() conversion function is not valid valve!")


# Helper function to handle all abort cases
def abort(auto: Auto) -> None:
    # TODO: aborting lol
    auto.threads.press_fill_thread_running.clear()
    auto.threads.ox_fill_thread_running.clear()
    auto.threads.pre_press_thread_running.clear()
    auto.threads.qds_thread_running.clear()
    log(colored("Threads killed.", "green"))
    auto.ctrl.release()
    log(colored("Autosequence has released control.", "green"))
    time.sleep(0.5) # time for everything to stop
    if auto.threads.press_fill_thread.is_alive():
        auto.threads.press_fill_thread.join()
    if auto.threads.ox_fill_thread.is_alive():
        auto.threads.ox_fill_thread.join()
    if auto.threads.pre_press_thread.is_alive():
        auto.threads.pre_press_thread.join()
    if auto.threads.qds_thread.is_alive():
        auto.threads.qds_thread.join()
    return


def press_fill(auto: Auto) -> None:
    press_fill_iso = auto.config.mappings.Press_Fill_Iso
    press_iso_1 = auto.config.mappings.Press_Iso_1
    press_iso_2 = auto.config.mappings.Press_Iso_2
    press_iso_3 = auto.config.mappings.Press_Iso_3

    copv_pts = [
        auto.config.mappings.COPV_PT_1,
        auto.config.mappings.COPV_PT_2,
        auto.config.mappings.Fuel_TPC_Inlet_PT,
    ]

    bottle_1_pt = auto.config.mappings.Bottle_1_PT
    bottle_2_pt = auto.config.mappings.Bottle_2_PT
    bottle_3_pt = auto.config.mappings.Bottle_3_PT

    avging_time = auto.config.variables.averaging_time 
    press_rate_1 = auto.config.variables.press_rate_1
    press_rate_2 = auto.config.variables.press_rate_2
    press_rate_ittrs = auto.config.variables.press_rate_1_ittrs
    ittr_time = auto.config.variables.copv_cooldown_time

    bottle_eq_threshold = auto.config.variables.bottle_equalization_threshold

    copv_press = average_ch(round(REFRESH_RATE * avging_time)) # Average COPV pressure

    # Bottle 1 equalization

    auto.ctrl[press_fill_iso] = True # Open press fill iso
    auto.ctrl[press_iso_1] = False # Make sure press iso 1 starts closed TODO: put starting valve states somewhere else

    # Press rate 1
    for i in range(press_rate_ittrs):
        log(f"Starting Bottle 1 Equalization Itteration: {i+1}") # TODO: Make only in verbose output
        end_time = sy.TimeStamp.now() + sy.TimeSpan.from_seconds(ittr_time) # Each itteration lasts for exactly 1 minute

        # Get starting pressure by averaging for 1 second
        start_press = avg_and_vote_for(auto.ctrl, copv_pts, press_rate_1, avging_time)
        copv_press.set_avg(start_press)
        target_press = start_press + press_rate_1

        auto.ctrl[press_iso_1] = True # Open press iso 1
        while (sy.TimeStamp.now() < end_time): # Wait until 1 minute has elapsed
            copv_press.add(sensor_vote(auto.ctrl, copv_pts, press_rate_1))
            value = copv_press.get()
            if ((value >= target_press) and (auto.ctrl[STATE(press_iso_1)] == True)):
                auto.ctrl.set(press_iso_1, False) # Close press iso 1
            time.sleep(0) # allow thread to yield
        auto.ctrl[press_iso_1] = False # Make sure press iso 1 is closed
        log(f"Finished Bottle 1 Equalization Itteration: {i+1}") # TODO: Make only in verbose output

    log("Bottle 1 completed press rate 1") # TODO: Make only in verbose output

    # Press rate 2
    while True: # Repeat until equalized
        end_time = sy.TimeStamp.now() + sy.TimeSpan.from_seconds(ittr_time) # Each itteration lasts for exactly 1 minute
        # Get starting pressure of the COPV and Bottle
        # NOTE: this will need to be adjusted since the Bottle PT will be waaay noiser than the COPV and so will probably need more averaging
        bottle_start_press = avg_and_vote_for(auto.ctrl, [bottle_1_pt], press_rate_2, avging_time)
        copv_start_press = avg_and_vote_for(auto.ctrl, copv_pts, press_rate_2, avging_time)
        copv_press.set_avg(start_press)
        pressure_delta = abs(bottle_start_press - copv_start_press)
        copv_target_press = copv_start_press + press_rate_2

        if (pressure_delta <= bottle_eq_threshold): # If we've reached the equalization threshold, stop
            break

        auto.ctrl[press_iso_1] = True # Open press iso 1
        while (sy.TimeStamp.now() < end_time): # Wait until 1 minute has elapsed
            copv_press.add(sensor_vote(auto.ctrl, copv_pts, press_rate_2))
            value = copv_press.get() 
            if ((value >= copv_target_press) and (auto.ctrl[STATE(press_iso_1)] == True)):
                auto.ctrl[press_iso_1] = False # Close press iso 1
            time.sleep(0) # allow thread to yield
        auto.ctrl[press_iso_1] = False # Make sure press iso 1 is closed
    auto.ctrl[press_iso_1] = False # Really make sure press iso 1 is closed

    auto.ctrl[press_fill_iso] = False # Close press fill iso

    log("Bottle 1 completed press rate 2")

    # Bottle 2 equalization

    # Bottle 3 equalization

    return 

def press_fill_wrapper(auto: Auto) -> None:
    try:
        auto.threads.press_fill_thread_running.set()
        auto.state.PRESS_FILL = True
        log(colored("Press Fill now running", "light_blue"))
        while (auto.threads.press_fill_thread_running.is_set()):
            press_fill(auto)
            time.sleep(0)
        auto.state.PRESS_FILL = False
        return
    except:
        return

def ox_fill(auto: Auto) -> None:
    auto.state.OX_FILL = False
    return

def ox_fill_wrapper(auto: Auto) -> None:
    try:
        auto.threads.ox_fill_thread_running.set()
        auto.state.OX_FILL = True
        log(colored("Ox Fill now running", "light_blue"))
        while (auto.threads.ox_fill_thread_running.is_set()):
            ox_fill(auto)
            time.sleep(0)
        auto.state.OX_FILL = False
        return
    except:
        return

def pre_press(auto: Auto) -> None:
    auto.state.PRE_PRESS = False
    return

def pre_press_wrapper(auto: Auto) -> None:
    try:
        auto.threads.pre_press_thread_running.set()
        auto.state.PRE_PRESS = True
        log(colored("Pre-Press now running", "light_blue"))
        while (auto.threads.pre_press_thread_running.is_set()):
            ox_fill(auto)
            time.sleep(0)
        auto.state.PRE_PRESS = False
        return
    except:
        return

def qds(auto: Auto) -> None:
    auto.state.QDS = False
    return

def qds_wrapper(auto: Auto) -> None:
    try:
        auto.threads.qds_thread_running.set()
        auto.state.QDS = True
        log(colored("QDs now running", "light_blue"))
        while (auto.threads.qds_thread_running.is_set()):
            ox_fill(auto)
            time.sleep(0)
        auto.state.QDS = False
        return
    except:
        return


def command_interface(auto: Auto) -> None:
    log(colored(
    """
    Welcome to the Limelight Autosequence!
    Commands:
        - press fill
        - ox fill
        - pre press
        - qds
        - quit
    """, "green"
    ))

    try:
        session = PromptSession()
        while True:
            # TODO: add a wait until defined check on all channels and abort if any aren't
            # TODO: only allow some state transitions
            # TODO: add safe pausing of threads 
            command = session.prompt(" > ")
            match command:
                case "press fill":
                    auto.threads.press_fill_thread.start()
                case "ox fill":
                    auto.threads.ox_fill_thread.start()
                case "pre press":
                    auto.threads.pre_press_thread.start()
                case "qds":
                    auto.threads.qds_thread.start()
                case "quit":
                    abort(auto)
                    break
    except KeyboardInterrupt:
        log(colored("Keyboard interrupt detected, aborting!", "red", attrs=["bold"]))
        abort(auto)
    return


def main() -> None:
    auto = Auto()
    auto.state.INIT = True

    args = parse_args()
    config = Configuration(args.config)
    auto.config = config

    client = synnax_login(args.cluster)
    log(colored("Initialization Complete!", "green"))

    write_chs = config.get_valves()
    read_chs = config.get_states() + config.get_pts() + config.get_tcs()

    # Create thread objects
    press_fill_thread = threading.Thread(name="press_fill_thread", target=press_fill_wrapper, args=(auto,))
    auto.threads.press_fill_thread = press_fill_thread
    auto.threads.press_fill_thread_running = threading.Event()

    ox_fill_thread = threading.Thread(name="ox_fill_thread", target=ox_fill_wrapper, args=(auto,))
    auto.threads.ox_fill_thread = ox_fill_thread
    auto.threads.ox_fill_thread_running = threading.Event()

    pre_press_thread = threading.Thread(name="pre_press_thread", target=pre_press_wrapper, args=(auto,))
    auto.threads.pre_press_thread = pre_press_thread
    auto.threads.pre_press_thread_running = threading.Event()

    qds_thread = threading.Thread(name="qds_thread", target=qds_wrapper, args=(auto,))
    auto.threads.qds_thread = qds_thread
    auto.threads.qds_thread_running = threading.Event()

    ctrl = client.control.acquire(
        name="Launch Autosequence",
        write_authorities=1,  # 1 is the default console authority
        write=write_chs,
        read=read_chs,
    )
    with patch_stdout():
        auto.ctrl = ctrl
        command_interface(auto)
        log(colored("Autosequence complete! have a nice day :)", "green"))
        exit(0)


if __name__ == "__main__":
    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports
    try:
        main()
    except KeyboardInterrupt:  # Abort cases also rely on this, but Python takes the closest exception catch inside nested calls
        error_and_exit("Keyboard interrupt detected")
    except Exception as e:  # catch-all uncaught errors
        error_and_exit("Uncaught exception!", exception=e)
