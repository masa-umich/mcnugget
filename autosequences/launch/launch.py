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
import yaml

# standard modules
import argparse
from enum import Enum, auto
import time


class State(Enum):
    START = auto()
    BOTTLE_1_EQ = auto()
    BOTTLE_2_EQ = auto()
    BOTTLE_3_EQ = auto()


# helper function to raise pretty errors
def error_and_exit(message: str, error_code: int = 1, exception=None) -> None:
    spinner.stop()  # incase it's running
    if exception != None:  # exception is an optional argument
        print(exception)
    print(colored(message, "red", attrs=["bold"]))
    print(colored("Exiting", "red", attrs=["bold"]))
    exit(error_code)


@yaspin(text=colored("Logging onto Synnax cluster...", "yellow"))
def synnax_login(args) -> sy.Synnax:
    cluster = args.cluster  # default value (synnax.masa.engin.umich.edu)
    if args.simulation:
        if args.verbose:
            spinner.write(
                colored("Using `localhost` as the cluster for simulation", "yellow")
            )
        cluster = "localhost"
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
        "-s",
        "--simulation",
        help="Should the autosequence be ran as a simulation",
        default=False,
        action="store_true",
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


# TODO: make this return read_channels, write_channels, 
# and a custom class with predefined config options
# so that intellisense works with it 
def parse_config(file_path: str):
    try:
        # using with will automatically close the file when done
        with open(file_path, "r") as file:
            # safe_load avoids trying to parse the yaml as python code (idk why you'd ever want that)
            return yaml.safe_load(file)
    except FileNotFoundError as e:
        error_and_exit(f"Error: The config file '{file_path}' could not be found.")
    except IOError as e:
        error_and_exit(f"Error: Unable to read the file '{file_path}'", exception=e)

# Get all channels from the config that we might want to write to (valves)
def get_write_channels(config):
    write_channels = []
    controllers = ["ebox", "flight_computer", "bay_board_1", "bay_board_2", "bay_board_3"]
    for controller in controllers:
        for controller in controllers:
            prefix = ""
            if controller == controllers[0]:
                prefix = "gse"
            elif controller == controllers[1]:
                prefix = "fc"
            elif controller == controllers[2]:
                prefix = "bb1"
            elif controller == controllers[3]:
                prefix = "bb2"
            elif controller == controllers[4]:
                prefix = "bb3"
        for valve in config[controller]["valves"].keys():
            valve_id = str(config[controller]["valves"][valve])
            write_channels.append(f"{prefix}_vlv_{valve_id}")
    return write_channels

# Get all channels from the config we might want to read from
def get_read_channels(config):
    read_channels = []
    controllers = ["ebox", "flight_computer", "bay_board_1", "bay_board_2", "bay_board_3"]
    for controller in controllers:
        prefix = ""
        if controller == controllers[0]:
            prefix = "gse"
        elif controller == controllers[1]:
            prefix = "fc"
        elif controller == controllers[2]:
            prefix = "bb1"
        elif controller == controllers[3]:
            prefix = "bb2"
        elif controller == controllers[4]:
            prefix = "bb3"
        for pt in config[controller]["pts"].keys():
            pt_id = str(config[controller]["pts"][pt])
            read_channels.append(f"{prefix}_pt_{pt_id}")
        for tc in config[controller]["tcs"].keys():
            tc_id = str(config[controller]["tcs"][tc])
            read_channels.append(f"{prefix}_tc_{tc_id}")
        for valve in config[controller]["valves"].keys():
            valve_id = str(config[controller]["valves"][valve])
            read_channels.append(f"{prefix}_state_{valve_id}")
    return read_channels

# Get the Synnax channel name corresponding to alias of the channel 
# Example: "press_iso_1" would return "gse_pt_3"
# All name matching is case-insensitive!
# Duplicate name aren't handled!
def get_channel_name(config, channel_name: str) -> str:
    controllers = ["ebox", "flight_computer", "bay_board_1", "bay_board_2", "bay_board_3"]
    for controller in controllers:
        prefix = ""
        if controller == controllers[0]:
            prefix = "gse"
        elif controller == controllers[1]:
            prefix = "fc"
        elif controller == controllers[2]:
            prefix = "bb1"
        elif controller == controllers[3]:
            prefix = "bb2"
        elif controller == controllers[4]:
            prefix = "bb3"
        for pt in config[controller]["pts"].keys():
            pt_id = str(config[controller]["pts"][pt])
            if pt.lower() == channel_name.lower():
                return prefix + "_pt_" + pt_id
        for tc in config[controller]["tcs"].keys():
            tc_id = str(config[controller]["tcs"][tc])
            if tc.lower() == channel_name.lower():
                return prefix + "_tc_" + tc_id
        for valve in config[controller]["valves"].keys():
            valve_id = str(config[controller]["valves"][valve])
            if valve.lower() == channel_name.lower():
                return prefix + "_vlv_" + valve_id

def get_sy_channel(config, client: sy.Synnax, channel_name: str) -> sy.Channel:
    return client.channels.retrieve(get_channel_name(config, channel_name))

# TODO: Add check for COPV temperature
def press_ittr(config, ctrl: Controller, copv_ch_1, copv_ch_2, press_iso_ch, press_rate):
    start_time = time.monotonic()
    end_time = start_time + 60 # one minute after start
    start_pres = (ctrl[copv_ch_1] + ctrl[copv_ch_2]) / 2
    target_pres = start_pres + press_rate
    ctrl[press_iso_ch] = True # open press iso
    while (True):
        now = time.monotonic()
        copv_pres = ((ctrl[copv_ch_1] + ctrl[copv_ch_2]) / 2)
        if ((copv_pres < target_pres) or (now >= end_time)):
            ctrl[press_iso_ch] = False # close press iso
            return

@yaspin(text=colored("Running Autosequence...", "light_blue"))
def state_machine(ctrl: Controller, config, client: sy.Synnax) -> None:
    state = State.START
    COPV_1 = get_channel_name(config, "copv_pt_1")
    COPV_2 = get_channel_name(config, "copv_pt_2")
    OX_PRESS_ISO_1 = get_channel_name(config, "ox_press_iso_1")
    OX_PRESS_ISO_2 = get_channel_name(config, "ox_press_iso_2")
    OX_PRESS_ISO_3 = get_channel_name(config, "ox_press_iso_3")
    try:
        while True:
            match state:
                case (
                    State.START
                ):  # Prompt for state to jump to (bottle 1 default, or skip to 2 or 3)
                    pass
                case State.BOTTLE_1_EQ:
                    # Open Press Fill Iso
                    # Open Press Iso 1 for press rate #1, then close
                    #   [MANUAL FOR NOW] During press, close Press Iso 1 if COPV temp exceeds the upper bound
                    # Wait for the remainder of the 1 minute
                    # Repeat with press rate #1 for 4 iterations
                    press_rate_2 = config["variables"]["press_rate_1"]
                    press_rate_1 = config["variables"]["press_rate_1"]
                    press_rate_1_ittrs = config["variables"]["press_rate_1_ittrs"]
                    # copv_pressure = (ctrl[COPV_1] + ctrl[COPV_2]) / 2
                    for i in range(press_rate_1_ittrs):
                        press_ittr(config, ctrl, COPV_1, COPV_2, OX_PRESS_ISO_1, press_rate_1)

                    # TODO:
                    # Open Press Iso 1 for press rate #2
                    #   [MANUAL FOR NOW] During press, close Press Iso 1 if COPV temp exceeds the upper bound
                    # Wait for the remainder of the 1 minute
                    # Repeat until the COPV pressure is within x psi (equalization threshold) of the 6k Bottle PT 1, close Press Iso 1 and continue to next section
                    pass
                case State.BOTTLE_2_EQ:
                    # First check that the 6k Bottle PT 2 is greater than the COPV pressure
                    # Open Press Fill Iso
                    # Then, open Press Iso 2 for press rate #1, then close
                    # [MANUAL FOR NOW] During press, close Press Iso 2 if COPV temp exceeds the upper bound
                    # Wait for the remainder of the 1 minute
                    # Repeat with press rate #1 for 4 iterations
                    # Open Press Iso 2 for press rate #2
                    # [MANUAL FOR NOW] During press, close Press Iso 2 if COPV temp exceeds the upper bound
                    # Wait for the remainder of the 1 minute
                    # Repeat until the COPV pressure is within x psi (equalization threshold) of 6k Bottle PT 2, close Press Iso 2 and continue to next section
                    pass
                case State.BOTTLE_3_EQ:
                    # First check that the 6k Bottle PT 3 is greater than the COPV pressure
                    # Open Press Fill Iso
                    # Then, open Press Iso 3 for press rate #1, then close
                    # [MANUAL FOR NOW] During press, close Press Iso 3 if COPV temp exceeds the upper bound
                    # Wait for the remainder of the 1 minute
                    # Repeat with press rate #1 for 4 iterations
                    # Open Press Iso 3 for press rate #2
                    # [MANUAL FOR NOW] During press, close Press Iso 3 if COPV temp exceeds the upper bound
                    # Wait for the remainder of the 1 minute
                    # Repeat until the COPV pressure is within x psi (equalization threshold) of 6k Bottle PT 3 OR at with the COPV target pressure bounds, then close Press Iso 3
                    # If target pressure achieved and the 6k Bottle PT 3 is x psig greater than the COPV pressure, continuously monitor the COPV pressure, and cycle Press Iso 3 to TPC the COPV within the target pressure bounds
                    pass
                case (
                    _
                ):  # Default case, in our case we should never reach this and its invalid
                    pass
    except KeyboardInterrupt or Exception:
        match state:
            case State.START:
                # abort case for start state
                pass
            case State.BOTTLE_1_EQ:
                # abort case for bottle_1_eq state
                pass

def main() -> None:
    args = parse_args()
    config = parse_config(args.config)
    client = synnax_login(args)
    print(colored("Initialization Complete!", "green"))
    with client.control.acquire(
        name="Launch Autosequence",
        write_authorities=[200],
        write=get_write_channels(config),
        read=get_read_channels(config)
    ) as ctrl:
        state_machine(ctrl, config, client)
    print(colored("Autosequence complete! have a nice day :)", "green"))


if __name__ == "__main__":
    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports
    try:
        main()
    except KeyboardInterrupt:  # Abort cases also rely on this, but Python takes the closest exception catch inside nested calls
        error_and_exit("Keyboard interrupt detected")
    except Exception as e:  # catch-all uncaught errors
        error_and_exit("Uncaught exception!", exception=e)
