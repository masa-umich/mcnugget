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

import synnax as sy
import argparse
import yaml

# helper function to raise pretty errors
def error_and_exit(message: str, error_code: int=1, exception=None) -> None:
    spinner.stop() # incase it's running
    if (exception != None): # exception is an optional argument
        print(exception)
    print(colored(message, "red", attrs=["bold"]))
    print(colored("Exiting", "red", attrs=["bold"]))
    exit(error_code)

@yaspin(text=colored("Logging onto Synnax cluster...", "yellow"))
def synnax_login(args):
    cluster = "synnax.masa.engin.umich.edu" # default value
    if (args.simulation):
        if (args.verbose):
            spinner.write(colored("Using `localhost` as the cluster for simulation", "yellow"))
        cluster = "localhost"
    try:
        client = sy.Synnax(
            host=cluster,
            port=9090,
            username="synnax",
            password="seldon",
        )
    except Exception as e:
        error_and_exit(f"Could not connect to Synnax at {cluster}, are you sure you're connected?")
    return client

# Allow the use to specify a mappings file which is not the default ("./mappings.yaml")
# And if verbose output should be enabled.
def parse_args() -> list:
    parser = argparse.ArgumentParser(description="The autosequence for preparring Limeight for launch!")
    parser.add_argument(
        "--simulation", 
        "-s",
        help="Should the autosequence be ran as a simulation",
        default=False,
        action="store_true"
    )
    parser.add_argument(
        "--mappings", 
        "-m", 
        help="The file to use for channel mappings",
        default="mappings.yaml",
        type=str
    )
    parser.add_argument(
        "--verbose",
        "-v",
        help="Shold the program output extra debugging information",
        action="store_true"
    ) # Positional argument
    args = parser.parse_args()
    # check that if there was an alternate mappings file given, that it is at least a .yaml file
    if (args.mappings != "mappings.yaml"):
        if (args.mappings.endswith(".yaml")):
            if (args.verbose):
                print(colored(f"Using mappings from file: {args.mappings}", "yellow"))
        else:
            error_and_exit(f"Invalid specified mappings file: {args.mappings}, must be .yaml file")
    return args

def parse_mappings(file_path: str):
    try:
        # using with will automatically close the file when done
        with open(file_path, "r") as file:
            # safe_load avoids trying to parse the yaml as python code (idk why you'd ever want that)
            return yaml.safe_load(file)
    except FileNotFoundError as e:
        error_and_exit(f"Error: The mappings file '{file_path}' could not be found.")
    except IOError as e:
        error_and_exit(f"Error: Unable to read the file '{file_path}'", exception=e)

def main() -> None:
    args = parse_args()
    mappings = parse_mappings(args.mappings)
    client = synnax_login(args)

if __name__ == "__main__":
    spinner.stop() # stop the "initializing..." spinner since we're done loading all the imports
    try:
        main()
    except Exception as e: # catch-all uncaught errors
        error_and_exit("Uncaught exception!", exception=e)