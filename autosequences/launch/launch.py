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
import time

# our modules
from configuration import Configuration

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

# TODO: Add check for COPV temperature
def press_ittr(ctrl: Controller, copv_ch_1, copv_ch_2, copv_ch_3, press_iso_ch, press_rate):
    start_time = time.monotonic()
    end_time = start_time + 60 # one minute after start
    start_pres = (ctrl[copv_ch_1] + ctrl[copv_ch_2] + ctrl[copv_ch_3]) / 3 # average channels
    target_pres = start_pres + press_rate
    ctrl[press_iso_ch] = True
    while (True):
        now = time.monotonic()
        copv_pres = (ctrl[copv_ch_1] + ctrl[copv_ch_2] + ctrl[copv_ch_3]) / 3
        if ((copv_pres >= target_pres) or (now >= end_time)) and (ctrl[press_iso_ch] == True):
            ctrl[press_iso_ch] = False # close press iso
        if (now >= end_time):
            return
        sy.sleep(0.01)


def press_sequence(ctrl: Controller, config: Configuration) -> None:
    for i in range(config.variables.press_rate_1_ittrs):
        press_ittr(
            ctrl, 
            config.channels.COPV_PT_1,
            config.channels.COPV_PT_2,
            config.channels.Fuel_TPC_Inlet_PT,
            config.channels.Press_Iso_1,
            config.variables.press_rate_1
        )

def command_interface(ctrl: Controller, config: Configuration) -> None:
    print(colored(
        """
        Welcome to the Limelight Autosequence!
        """
    ))
    while (True):
        # TODO: add a wait until defined check on all channels
        # and abort if any aren't
        command = input(colored("> ", "green"))
        parse_command(ctrl, config, command)

def parse_command(ctrl: Controller, config: Configuration, input: str):
    match input:
        case "press":
            print(colored("Starting press sequence 1", "green"))
            press_sequence(ctrl, config)
        case "ox fill":
            pass
        case "quit":
            exit(0)

def main() -> None:
    args = parse_args()
    config = Configuration.load(args.config)
    client = synnax_login(args)
    print(colored("Initialization Complete!", "green"))
    with client.control.acquire(
        name="Launch Autosequence",
        write_authorities=1, # 1 is the default console authority
        write=config.valves,
        read=config.valves + config.pts + config.tcs
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
    #     error_and_exit("Uncaught exception!", exception=e)
