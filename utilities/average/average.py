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

import datetime
from termcolor import colored
from yaspin import yaspin

# fun spinner while we load packages
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

import argparse
from collections import deque
import synnax as sy

from collections import deque

class average_ch:
    __slots__ = ('name', 'alpha', '_avg', '_initialized')

    def __init__(self, name: str, window: int):
        self.name = name
        # Alpha approximates a window of N items: alpha = 2 / (N + 1)
        self.alpha = 2.0 / (window + 1)
        self._avg = 0.0
        self._initialized = False

    def add(self, value: float) -> None:
        if not self._initialized:
            self._avg = value
            self._initialized = True
        else:
            # Standard EWMA formula
            self._avg = (value * self.alpha) + (self._avg * (1 - self.alpha))

    def get(self) -> float:
        return self._avg


# helper function to raise pretty errors
def error_and_exit(message: str, error_code: int = 1, exception=None) -> None:
    spinner.stop()  # incase it's running
    if exception != None:  # exception is an optional argument
        print(exception)
    print(colored(message, "red", attrs=["bold"]))
    print(colored("Exiting", "red", attrs=["bold"]))
    exit(error_code)


def parse_args() -> argparse.Namespace:
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
        default="localhost",
        type=str,
    )
    parser.add_argument(
        "-w",
        "--window",
        help="Specify the amount of samples to average per channel",
        default=50,
        type=int,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Shold the program output extra debugging information",
        action="store_true",
    )  # Positional argument
    parser.add_argument(
        "-a",
        "--all",
        help="Shold the program average all channels?",
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
    if not args.all: # TODO: remove this when channel selections are supported
        error_and_exit(
            f"Averaging for specific channels not yet supported, please use the flag `-a` to average all channels\n Example: ./average -a"
        )
    return args


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
    return client  # type: ignore


# Returns write_channels and read_channels
@yaspin(text=colored("Setting up channels...", "yellow"))
def setup_channels(client: sy.Synnax) -> tuple[list[str], list[str]]:
    avg_time = client.channels.create(
        name="avg_time",
        data_type=sy.DataType.TIMESTAMP,
        is_index=True,
        retrieve_if_name_exists=True,
    )

    read_channels = []
    write_channels = []

    for channel in client.channels.retrieve(["*"]): # get all channels with some cursed API usage
        # TODO: Add option to change channel types to be averaged (maybe per board or sensor type)
        if (channel.data_type == sy.DataType.FLOAT32) and ("pt" in channel.name) and ("avg" not in channel.name):
            read_channels.append(channel.name)
    
    for channel in read_channels:
        avg_name = channel + "_avg"
        client.channels.create(
            name=avg_name,
            index=avg_time.key,
            data_type=sy.DataType.FLOAT32,
            retrieve_if_name_exists=True,
        )
        write_channels.append(avg_name)
    
    write_channels += ["avg_time"] # add time channel

    return write_channels, read_channels

# A driver to write average values to the server
@yaspin(text=colored("Running Averaging...", "green"))
def driver(streamer: sy.Streamer, writer: sy.Writer, read_chs: list[str], args):
    window_size = args.window # TODO: add to config

    avg_channels = []
    for channel in read_chs:
        avg_channels.append(average_ch(channel, window_size))
    
    # TODO: Fix streamer buffering under bad script performance or at least report significant timestamp mistmatches
    for frame in streamer:
        write_data = {}
        
        for channel in avg_channels:
            value = frame[channel.name]
            channel.add(value)
            write_data[channel.name + "_avg"] = channel.get()

        write_data["avg_time"] = frame["time"] # TODO: make this not the simulation time
        writer.write(write_data)

def main():
    args = parse_args()
    client = synnax_login(args.cluster)
    write_chs, read_chs = setup_channels(client)

    # Streamer for sesnor values
    # with client.open_streamer(channels=read_chs + ["time"]) as streamer: # include sensor time channel to show streamer lagging
    with client.open_streamer(channels=read_chs + ["time"]) as streamer:
        # Open writer for everything else
        with client.open_writer(start=sy.TimeStamp.now(), channels=write_chs) as writer:
            driver(streamer, writer, read_chs, args)


if __name__ == "__main__":
    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports
    try:
        main()
    except KeyboardInterrupt:  # Abort cases also rely on this, but Python takes the closest exception catch inside nested calls
        error_and_exit("Keyboard interrupt detected")
    # except Exception as e:  # catch-all uncaught errors
        # error_and_exit("Uncaught exception!", exception=e)