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

from configuration import Configuration
from system import State, System

# fun spinner while we load packages
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

import argparse
import random
import time
import synnax as sy

global time_channel 
# We use one global timestamp channel to simplify the simulation
# In reality, there are lots of timestamp channels since data 
# can arrive asyncronously from lots of different sources via limewire
# But this isn't useful to simulate the behavior of for the purposes of an autosequence


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


@yaspin(text=colored("Logging onto Synnax cluster...", "yellow"))
def synnax_login(args) -> sy.Synnax:
    cluster = args.cluster
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
    return client # type: ignore


# Makes or gets all the channels we care about into Synnax
@yaspin(text=colored("Setting up channels...", "yellow"))
def get_channels(client: sy.Synnax, config: Configuration):
    global time_channel
    time_channel =  client.channels.create(
        retrieve_if_name_exists=True,
        name="time",
        data_type=sy.DataType.TIMESTAMP,
        virtual=False,
        is_index=True
    )
    channels = config.valves + config.pts + config.states + config.tcs + ["time"]
    for channel_name in channels:
        if "vlv" in channel_name:
            client.channels.create(
                retrieve_if_name_exists=True,
                name=channel_name,
                data_type=sy.DataType.INT8,
                virtual=True
            )
        elif "state" in channel_name:
            client.channels.create(
                retrieve_if_name_exists=True,
                name=channel_name,
                data_type=sy.DataType.INT8,
                virtual=False,
                index=time_channel.key
            )
        else:
            client.channels.create(
                retrieve_if_name_exists=True,
                name=channel_name,
                data_type=sy.DataType.FLOAT32,
                virtual=False,
                index=time_channel.key
            )


# A fake driver that writes data to all channels according to the simulation
@yaspin(text=colored("Running Simulation...", "green"))
def driver(config: Configuration, streamer: sy.Streamer, writer: sy.Writer, system: System):
    global time_channel
    driver_frequency = 20 # Hz
    driver_period = driver_frequency**(-1) # seconds
    channels = config.states + config.pts + config.tcs
    while True:
        start_time = time.time()
        timestamp = [("time", sy.TimeStamp.now())]
        sensor_data = []
        state_data = []

        # Check for incoming valve commands
        fr = streamer.read(timeout=0)
        if fr is not None:
            for channel in fr.channels:
                system.toggle_valve(str(channel))
        
        for channel in channels:
            if "state" in channel:
                vlv = channel.replace("state", "vlv")
                state = system.get_valve_state(vlv)
                if state == State.OPEN:
                    state_data.append((channel, 1))
                else:
                    state_data.append((channel, 0))
            if "pt" in channel:
                noise = random.gauss(0, 150) # instrument noise is approximately gaussian
                # TODO: add different noise for different instruments with some sort of lookup table
                pressure = system.get_pressure(channel) + noise
                sensor_data.append((channel, pressure))
            else:
                sensor_data.append((channel, 0.0))

        write_data = dict(timestamp + sensor_data + state_data)
        writer.write(write_data) # type: ignore

        system.update()

        wakeup_time = start_time + driver_period
        while wakeup_time > time.time():
            sy.sleep(0)
        

def main():
    args = parse_args()
    client = synnax_login(args)
    config = Configuration.load(args.config)
    system = System(config)
    get_channels(client, config)
    # Open streamer for valve commands
    with client.open_streamer(
        channels=config.valves
    ) as streamer:
        # Open writer for everything else
        with client.open_writer(
            start=sy.TimeStamp.now(),
            channels=config.states + config.pts + config.tcs + ["time"]
        ) as writer:
            driver(config, streamer, writer, system) # Run the fake driver


if __name__ == "__main__":
    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports
    try:
        main()
    except KeyboardInterrupt:  # Abort cases also rely on this, but Python takes the closest exception catch inside nested calls
        error_and_exit("Keyboard interrupt detected")
    except Exception as e:  # catch-all uncaught errors
       error_and_exit("Uncaught exception!", exception=e)
