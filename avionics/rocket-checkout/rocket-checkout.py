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
from typing import List

class Configuration:
    channels: dict

    def get_rocket_valves(self):
        rocket_valves = []
        for channel in self.channels:
            if ("vlv" in channel) and ("gse" not in channel):
                rocket_valves.append(channel)

    def __init__(self, filepath: str):
        self.channels = {} # initialize the channels flat map

        with open(filepath, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        prefix_map = {
            "ebox": "gse",
            "flight_computer": "fc",
            "bay_board_1": "bb1",
            "bay_board_2": "bb2",
            "bay_board_3": "bb3"
        }

        type_suffix_map = {
            "pts": "pt",
            "valves": "vlv",
            "tcs": "tc"
        }

        mappings_data = yaml_data.get("channel_mappings", {})

        for controller_key, prefix in prefix_map.items():
            controller_data = mappings_data.get(controller_key)
            if not controller_data:
                continue

            for type_key, suffix in type_suffix_map.items():
                items = controller_data.get(type_key)
                if not items:
                    continue # Skip if this controller doesn't have TCs (e.g. Flight Computer)

                for real_name, index in items.items():
                    # Construct Synnax Name: prefix_suffix_index (e.g., gse_pt_1)
                    synnax_name = f"{prefix}_{suffix}_{index}"
                    self.channels[real_name] = synnax_name

REFRESH_RATE = 50 # Hz
loop = sy.Loop(sy.Rate.HZ * 2 * REFRESH_RATE) 
# Standard refresh rate for all checks (doubled because of shannon sampling thereom)

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

def checkout_sequence(ctrl: Controller, config: Configuration) -> None:
    rocket_valves = config.get_rocket_valves()
    for valve in rocket_valves:
        ctrl[valve] = True
        sy.sleep(0.5)
        ctrl[valve] = False
        sy.sleep(0.5)

def command_interface(ctrl: Controller, config: Configuration) -> None:
    print(colored(
        """
        Welcome to the Limelight Autosequence!
        Options:
            - go
            - quit
        """
    ))

    while (True):
        command = input(colored("> ", "green"))
        match command:
            case "go":
                print(colored("", "green"))
                checkout_sequence(ctrl, config)
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
        name="Rocket Checkouts",
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