#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax>=0.58.0",
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

import argparse
import synnax as sy
import os
import time
from typing import Any
from pathlib import Path
from simulation import Simulation

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="A universal fluid simulator for verifying autosequence logic"
    )
    parser.add_argument(
        "-a",
        "--aliases",
        help="The file to use for channel aliases",
        default="aliases.yaml",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "-s",
        "--sim-params",
        help="The file to use for simulation parameters",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "-c",
        "--cluster",
        help="Specify a Synnax cluster to connect to (should almost always be localhost)",
        default=os.getenv("SYNNAX_CLUSTER", "localhost"),
        type=str,
    )
    return parser.parse_args()

@yaspin(text=colored("Logging onto Synnax cluster...", "yellow"))
def synnax_login(cluster: str) -> sy.Synnax:
    try:
        return sy.Synnax(
            host=cluster,
            port=9090,
            username="synnax",
            password="seldon",
        )
    except Exception:
        print(
            f"Could not connect to Synnax at {cluster}, are you sure you're connected?"
        )
        exit(1)

@yaspin(text=colored("Setting up channels...", "yellow"))
def init_channels(client: sy.Synnax, sim: Simulation) -> tuple[list[str], list[str]]:
    read_channels: list[str] = []
    write_channels: list[str] = []

    time_channel = client.channels.create(
        retrieve_if_name_exists=True,
        name="time",
        data_type=sy.DataType.TIMESTAMP,
        virtual=False,
        is_index=True,
    )
    write_channels.append("time")

    sensor_channels: list[str] = sim.get_sensor_channels()
    for sensor_channel in sensor_channels:
        client.channels.create(
            retrieve_if_name_exists=True,
            name=sensor_channel,
            data_type=sy.DataType.FLOAT32,
            virtual=False,
            index=time_channel.key,
        )
        write_channels.append(sensor_channel)

    valve_channels: list[str] = sim.get_valve_channels()
    for cmd_channel in valve_channels:
        # Make command channel (default name)
        client.channels.create(
            retrieve_if_name_exists=True,
            name=cmd_channel,
            data_type=sy.DataType.INT8,
            virtual=True,
        )
        read_channels.append(cmd_channel)
        # Make state channel
        state_channel: str = cmd_channel.replace("vlv", "state")
        client.channels.create(
            retrieve_if_name_exists=True,
            name=state_channel,
            data_type=sy.DataType.INT8,
            virtual=False,
            index=time_channel.key,
        )
        write_channels.append(state_channel)
    return write_channels, read_channels

@yaspin(text=colored("Running simulation...", "green"))
def driver(streamer: sy.Streamer, writer: sy.Writer, sim: Simulation) -> None:
    loop = sy.Loop(interval=(sy.Rate.HZ * sim.frequency))
    channel_readings: dict[str, Any] = {}
    previous_step = time.monotonic()

    while loop.wait():
        current_step = time.monotonic()
        time_step = current_step - previous_step
        previous_step = current_step
        fr = streamer.read(timeout=0)
        if fr is not None:
            for channel in fr.channels:
                cmd = fr[channel][0]
                sim.set_valve_state(channel, cmd)
        sim.simulation_step(time_step)
        channel_readings = sim.get_channel_readings()
        channel_readings["time"] = sy.TimeStamp.now()
        writer.write(channel_readings)

def main() -> None:
    args: argparse.Namespace = parse_args()
    sim: Simulation = Simulation(args.sim_params, args.aliases)
    client: sy.Synnax = synnax_login(args.cluster)
    write_channels, read_channels = init_channels(client, sim)
    with client.open_streamer(channels=read_channels) as streamer:
        with client.open_writer(start=sy.TimeStamp.now(), channels=write_channels) as writer:
            driver(streamer, writer, sim)

if __name__ == "__main__":
    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports
    main()
    # try:
        # main()
    # except KeyboardInterrupt:
    #     print("Keyboard interrupt detected")
    #     exit(0)
    # except Exception as e:  # catch-all uncaught errors
    #     print("Uncaught exception!")
    #     print(e)
    #     exit(1)
