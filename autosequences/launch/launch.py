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
import statistics
import time

# our modules
from configuration import Configuration

REFRESH_RATE = 50 # Hz
loop = sy.Loop(sy.Rate.HZ * 2 * REFRESH_RATE) 
# Standard refresh rate for all checks (doubled because of shannon sampling thereom)

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

# TODO: Add check for COPV temperature
def press_ittr(ctrl: Controller, copv_1, copv_2, copv_3, press_iso_X, press_fill_iso, press_rate):
    start_time = time.monotonic()
    end_time = start_time + 60 # one minute after start
    start_pres = sensor_vote(ctrl, [copv_1, copv_2, copv_3], 40)
    
    target_pres = start_pres + press_rate

    ctrl[press_fill_iso] = True
    ctrl[press_iso_X] = True

    while loop.wait():
        now = time.monotonic()
        copv_pres = sensor_vote(ctrl, [copv_1, copv_2, copv_3], 40)
        if ((copv_pres >= target_pres) or (now >= end_time)) and (ctrl[press_iso_X] == True):
            ctrl[press_iso_X] = False # close press iso
        if (now >= end_time):
            ctrl[press_fill_iso] = False
            return


def press_sequence(ctrl: Controller, config: Configuration) -> None:
    copv_1 = config.mappings.COPV_PT_1
    copv_2 = config.mappings.COPV_PT_2
    copv_3 = config.mappings.Fuel_TPC_Inlet_PT
    press_iso_1 = config.mappings.Press_Iso_1
    press_iso_2 = config.mappings.Press_Iso_2
    press_iso_3 = config.mappings.Press_Iso_3
    press_fill_iso = config.mappings.Press_Fill_Iso
    rate_1 = config.variables.press_rate_1
    rate_2 = config.variables.press_rate_2
    ittrs = config.variables.press_rate_1_ittrs

    for i in range(ittrs):
        press_ittr(ctrl, copv_1, copv_2, copv_3, press_iso_1, press_fill_iso, rate_1)

def command_interface(ctrl: Controller, config: Configuration) -> None:
    print(colored(
        """
        Welcome to the Limelight Autosequence!
        """
    ))

    # while True:
    #     copv_1 = config.mappings.COPV_PT_1
    #     copv_2 = config.mappings.COPV_PT_2
    #     copv_3 = config.mappings.Fuel_TPC_Inlet_PT
    #     copv_pres = sensor_vote(ctrl, [copv_1, copv_2, copv_3], 0)
    #     print(copv_pres, end="\r")
    #     ctrl.sleep(0.01)

    while (True):
        # TODO: add a wait until defined check on all channels
        # and abort if any aren't
        command = input(colored("> ", "green"))
        match command:
            case "press":
                print(colored("Starting press sequence 1", "green"))
                press_sequence(ctrl, config)
            case "ox fill":
                pass
            case "quit":
                exit(0)


def main() -> None:
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
        command_interface(ctrl, config)
        
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
