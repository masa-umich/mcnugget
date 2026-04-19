#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax>=0.49.0",
#     "yaspin",
#     "termcolor",
#     "pyyaml",
#     "mclib",
# ]
#
# [tool.uv]
# reinstall-package = ["mclib"]
# [tool.uv.sources]
# mclib = { path = "../mclib" }
# ///

from termcolor import colored
from yaspin import yaspin

# fun spinner while we load packages
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

import argparse
import random
import synnax as sy
from typing import NewType

# Valve state alias for readability
State = NewType('State', bool)
OPEN = True
CLOSED = False

class Volume:
    """
    A volume is a class which represents a physical container of fluid.
    Volumes have a constant name, volume, and associated channels.
    Volumes have variables pressure and temperature

    A volume's pressure and temperature are checked and updated every
    time step according to the state of the system (valves).
    """

    # Constants:
    name: str
    volume: float  # liters
    channels: list[str] # list of synnax channel names or aliases

    # State variables:
    pressure: float  # psi
    temperature: float  # C

    def __init__(self, name: str, volume: float, initial_pressure: float, channels: list[str]):
        self.name = name
        self.volume = volume  # liters
        self.pressure = initial_pressure  # psi
        self.channels = channels

class Valve:
    """
    A valve is a class which represents a physical valve in the system.
    Valves have a constant name, normally_open boolean, and associated channels.
    Valves have a state variable which is either OPEN or CLOSED.

    A valve's state is updated according to incoming commands from the streamer.
    """

    # Constants:
    channel: str # synnax channel name or alias for the valve command (valves may only have one channel)
    is_normally_closed: bool
    is_check_valve: bool # if true, only unidirectional flow from INLET to OUTLET
    inlet_volume_name: str
    outlet_volume_name: str

    # State variables:
    state: State # 0 for closed, 1 for open (or use alias OPEN and CLOSED for readability)

    def __init__(self, channel: str, normally_closed: bool, is_check_valve: bool, inlet_volume_name: str, outlet_volume_name: str):
        self.channel = channel
        self.is_normally_closed = normally_closed
        self.is_check_valve = is_check_valve
        self.inlet_volume_name = inlet_volume_name
        self.outlet_volume_name = outlet_volume_name
        if normally_closed:
            self.state = CLOSED
        else:
            self.state = OPEN

class Simulation:
    """
    Class which represents the entire simulation. 
    Contains all volumes and valves, as well as physics updates
    """

    # Simulation Parameters:
    volumes: dict[str, Volume] # dictionary mapping volume names to Volume objects
    valves: dict[str, Valve] # dictionary mapping valve channel names to Valve objects
    do_noise: bool
    default_pt_noise_sigma: float
    do_temp_simulation: bool
    default_tc_noise_sigma: float
    frequency: int # Hz
    atmosphere_volume_name: str

    def __init__(self, params_path: str):
        """
        Parse simulation parameters from yaml
        """
        yaml_dict = load_yaml(params_path)
        try:
            self.do_noise = bool(yaml_dict.get("do_noise", False))
            self.default_pt_noise_sigma = float(yaml_dict.get("default_pt_noise_sigma", 0.0))
            self.do_temp_simulation = bool(yaml_dict.get("do_temp_simulation", False))
            self.default_tc_noise_sigma = float(yaml_dict.get("default_tc_noise_sigma", 0.0))
            self.frequency = int(yaml_dict.get("frequency", 10))
            self.atmosphere_volume_name = str(yaml_dict.get("atmosphere_volume_name", "atmosphere"))

            self.volumes = {}
            for vol_data in yaml_dict.get("volumes", []):
                name = vol_data["name"]
                self.volumes[name] = Volume(
                    name=name,
                    volume=float(vol_data["volume"]),
                    initial_pressure=float(vol_data["initial_pressure"]),
                    channels=vol_data.get("channels", [])
                )

            self.valves = {}
            for vlv_data in yaml_dict.get("valves", []):
                channel = vlv_data["channel"]
                is_normally_open = bool(vlv_data.get("is_normally_open", False))
                self.valves[channel] = Valve(
                    channel=channel,
                    normally_closed=not is_normally_open,
                    is_check_valve=bool(vlv_data.get("is_check_valve", False)),
                    inlet_volume_name=vlv_data["inlet"],
                    outlet_volume_name=vlv_data["outlet"]
                )
        except KeyError as e:
            error_and_exit(f"Missing required key {e} in simulation parameters file {params_path}")
        except Exception as e:
            error_and_exit(f"Error parsing simulation parameters from {params_path}", exception=e)

def load_yaml(path: str) -> dict[str, str]:
    """
    Parses a yaml file of channel aliases and returns a dictionary mapping alias to channel name
    """
    import yaml
    with open(path, 'r') as f:
        yaml_dict = yaml.safe_load(f)
    if yaml_dict is None:
        error_and_exit(f"Alias file {path} is empty or not properly formatted")
    return yaml_dict

def parse_aliases(aliases_path: str) -> dict[str, str]:
    """
    Parses a yaml dictionary of channel aliases and returns a dictionary mapping alias to channel name
    """
    yaml_dict = load_yaml(aliases_path)
    aliases: dict[str, str] = {}

    prefix_map: dict[str, str] = {
        "ebox": "gse",
        "flight_computer": "fc",
        "bay_board_1": "bb1",
        "bay_board_2": "bb2",
        "bay_board_3": "bb3",
    }

    type_suffix_map: dict[str, str] = {"pts": "pt", "valves": "vlv", "tcs": "tc"}

    mappings_data = yaml_dict.get("channel_mappings")
    if not mappings_data:
        error_and_exit(f"Alias file {aliases_path} is missing 'channel_mappings' key or it is empty.")

    for controller_key, prefix in prefix_map.items():
        controller_data = mappings_data.get(controller_key)
        if not controller_data:
            continue

        for type_key, suffix in type_suffix_map.items():
            items = controller_data.get(type_key)
            if not items:
                continue

            for config_ch_name, value in items.items():
                try:
                    ch_index = value
                    if isinstance(value, dict):
                        ch_index = value.get("id")
                        if ch_index is None:
                            raise KeyError("id")

                    synnax_name = f"{prefix}_{suffix}_{ch_index}"
                    aliases[config_ch_name.lower()] = synnax_name
                except KeyError as e:
                    error_and_exit(f"Missing key {e} for channel {config_ch_name} in {aliases_path}")
                except Exception as e:
                    error_and_exit(f"Error parsing channel {config_ch_name} in {aliases_path}", exception=e)

    return aliases

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
        description="A universal fluid simulator for verifying autosequence logic"
    )
    parser.add_argument(
        "-a",
        "--aliases",
        help="The file to use for channel aliases",
        default="aliases.yaml",
        required=True,
        type=str,
    )
    parser.add_argument(
        "-s",
        "--sim-params",
        help="The file to use for simulation parameters",
        required=True,
        type=str,
    )
    parser.add_argument(
        "-c",
        "--cluster",
        help="Specify a Synnax cluster to connect to (should almost always be localhost)",
        default="localhost",
        type=str,
    )
    args = parser.parse_args()
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


# A fake driver that writes data to all channels according to the simulation
@yaspin(text=colored("Running Simulation...", "green"))
def driver(args: argparse.Namespace, streamer: sy.Streamer, writer: sy.Writer, ):
    global do_noise
    driver_frequency = args.frequency  # Hz
    loop = sy.Loop(interval=(sy.Rate.HZ * driver_frequency))

    while loop.wait():
        write_data: dict = {}
        write_data["time"] = sy.TimeStamp.now()

        # Check for incoming valve commands
        fr = streamer.read(timeout=0)
        if fr is not None:
            for channel in fr.channels:
                cmd = fr[channel][0]
                valve = system.get_valve_obj(channel)  # type: ignore
                if cmd == True:
                    valve.energize()
                else:
                    valve.de_energize()

        for state_ch in config.get_states():
            valve = system.get_valve_obj(state_ch.replace("state", "vlv"))
            if valve.normally_closed:  # Account for normally open valves
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
            noise = (
                (random.gauss(0, 10)) if (do_noise) else (0)
            )  # instrument noise is approximately gaussian
            # TODO: add different noise for different instruments with some sort of lookup table
            pressure = system.get_pressure(pt_ch) + noise
            write_data[pt_ch] = pressure
        for tc_ch in config.get_tcs():
            noise = (
                (random.gauss(0, 2)) if (do_noise) else (0)
            )  # instrument noise is approximately gaussian
            temperature = system.get_temperature(tc_ch) + noise
            write_data[tc_ch] = temperature

        writer.write(write_data)  # type: ignore
        system.update()


def main():
    args = parse_args()
    aliases = parse_aliases(args.aliases)
    simulation = Simulation(args.sim_params)
    client = synnax_login(args.cluster)
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
