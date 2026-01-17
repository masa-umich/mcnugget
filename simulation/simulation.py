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
from simulation_utils import State, System, Config

# fun spinner while we load packages
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

import argparse
import random
import synnax as sy

do_noise = True

# helper function to raise pretty errors
def error_and_exit(message: str, error_code: int = 1, exception=None) -> None:
    spinner.stop()  # incase it's running
    if exception != None:  # exception is an optional argument
        print(exception)
    print(colored(message, "red", attrs=["bold"]))
    print(colored("Exiting", "red", attrs=["bold"]))
    exit(error_code)


def parse_args() -> argparse.Namespace:
    global do_noise
    parser = argparse.ArgumentParser(
        description="The autosequence for preparring Limeight for launch!"
    )

    parser.add_argument(
        "-n",
        "--noise",
        help="Should the simulation include simulated sensor noise?",
        default="True",
        type=str,
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
        "-f",
        "--frequency",
        help="Specify a frequency to push data into Synnax at",
        default=50,
        type=int,
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
    if (args.noise.lower() == "true"):
        do_noise = True
    elif (args.noise.lower() == "false"):
        do_noise = False
    else:
        error_and_exit("Argument --noise must be followed by either 'true' or 'false'")
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


# Makes or gets all the channels we care about into Synnax
@yaspin(text=colored("Setting up channels...", "yellow"))
def get_channels(client: sy.Synnax, config: Config):
    valves = config.get_vlvs()
    states = config.get_states()
    sensors = config.get_sensors()

    time_channel = client.channels.create(
        retrieve_if_name_exists=True,
        name="time",
        data_type=sy.DataType.TIMESTAMP,
        virtual=False,
        is_index=True,
    )

    for valve in valves:
        client.channels.create(
            retrieve_if_name_exists=True,
            name=valve,
            data_type=sy.DataType.INT8,
            virtual=True,
        )

    for state in states:
        client.channels.create(
            retrieve_if_name_exists=True,
            name=state,
            data_type=sy.DataType.INT8,
            virtual=False,
            index=time_channel.key,
        )

    for sensor in sensors:
        client.channels.create(
            retrieve_if_name_exists=True,
            name=sensor,
            data_type=sy.DataType.FLOAT32,
            virtual=False,
            index=time_channel.key,
        )


# A fake driver that writes data to all channels according to the simulation
@yaspin(text=colored("Running Simulation...", "green"))
def driver(config: Config, streamer: sy.Streamer, writer: sy.Writer, system: System, args):
    global do_noise
    driver_frequency = args.frequency # Hz
    loop = sy.Loop(sy.Rate.HZ * driver_frequency)

    while loop.wait():
        write_data: dict = {}
        write_data["time"] = sy.TimeStamp.now()

        # Check for incoming valve commands
        fr = streamer.read(timeout=0)
        if fr is not None:
            for channel in fr.channels:
                cmd = fr[channel][0]
                valve = system.get_valve_obj(channel) # type: ignore
                if cmd == True:
                    valve.energize()
                else:
                    valve.de_energize()

        for state_ch in config.get_states():
            valve = system.get_valve_obj(state_ch.replace("state", "vlv"))
            if valve.normally_closed: # Account for normally open valves
                if valve.state == State.OPEN:
                    write_data[state_ch] = 1
                else:
                    write_data[state_ch] = 0
            else:
                if valve.state == State.OPEN:
                    write_data[state_ch] = 0
                else:
                    write_data[state_ch] = 1

        for pt_ch in config.get_pts():
            noise = (random.gauss(0, 10)) if (do_noise) else (0) # instrument noise is approximately gaussian
            # TODO: add different noise for different instruments with some sort of lookup table
            pressure = system.get_pressure(pt_ch) + noise
            write_data[pt_ch] = pressure
        for tc_ch in config.get_tcs():
            noise = (random.gauss(0, 2)) if (do_noise) else (0) # instrument noise is approximately gaussian
            temperature = system.get_temperature(tc_ch) + noise
            write_data[tc_ch] = temperature

        writer.write(write_data)  # type: ignore
        system.update()


def main():
    args = parse_args()
    client = synnax_login(args.cluster)
    config = Config(args.config)
    system = System(config)
    get_channels(client, config)
    # Open streamer for valve commands

    write_chs = config.get_vlvs()
    read_chs = config.get_states() + config.get_sensors() + ["time"]

    with client.open_streamer(channels=write_chs) as streamer:
        # Open writer for everything else
        with client.open_writer(start=sy.TimeStamp.now(), channels=read_chs) as writer:
            driver(config, streamer, writer, system, args)  # Run the fake driver


if __name__ == "__main__":
    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports
    try:
        main()
    except KeyboardInterrupt:  # Abort cases also rely on this, but Python takes the closest exception catch inside nested calls
        error_and_exit("Keyboard interrupt detected")
    except Exception as e:  # catch-all uncaught errors
        error_and_exit("Uncaught exception!", exception=e)
