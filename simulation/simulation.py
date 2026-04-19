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

# Physics constants
AMBIENT_TEMPERATURE = 20.0  # C
AMBIENT_PRESSURE = 14.7  # psi

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

    def __init__(self, name: str, volume: float, initial_pressure: float, initial_temperature: float, channels: list[str]):
        self.name = name
        self.volume = volume  # liters
        self.pressure = initial_pressure  # psi
        self.temperature = initial_temperature  # C
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
    is_normally_open: bool
    is_check_valve: bool # if true, only unidirectional flow from INLET to OUTLET
    inlet_volume_name: str
    outlet_volume_name: str

    # State variables:
    state: State # 0 for closed, 1 for open (or use alias OPEN and CLOSED for readability)

    def __init__(self, channel: str, is_normally_open: bool, is_check_valve: bool, inlet_volume_name: str, outlet_volume_name: str):
        self.channel = channel
        self.is_normally_open = is_normally_open
        self.is_check_valve = is_check_valve
        self.inlet_volume_name = inlet_volume_name
        self.outlet_volume_name = outlet_volume_name
        if is_normally_open:
            self.state = OPEN
        else:
            self.state = CLOSED

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
                    name=name.lower(),
                    volume=float(vol_data["volume"]),
                    initial_pressure=float(vol_data["initial_pressure"]),
                    initial_temperature=float(vol_data.get("initial_temperature", AMBIENT_TEMPERATURE)),
                    channels=list(map(str.lower, vol_data.get("channels", [])))
                )

            self.valves = {}
            for vlv_data in yaml_dict.get("valves", []):
                channel = vlv_data["channel"]
                is_normally_open = bool(vlv_data.get("is_normally_open", False))
                self.valves[channel.lower()] = Valve(
                    channel=channel.lower(),
                    is_normally_open=is_normally_open,
                    is_check_valve=bool(vlv_data.get("is_check_valve", False)),
                    inlet_volume_name=vlv_data["inlet"],
                    outlet_volume_name=vlv_data["outlet"]
                )
        except KeyError as e:
            error_and_exit(f"Missing required key {e} in simulation parameters file {params_path}")
        except Exception as e:
            error_and_exit(f"Error parsing simulation parameters from {params_path}", exception=e)
    
    def update_physics(self):
        """
        Update the physics of the system according to valve states.
        This should be called every time step.
        """
        # For each valve, if it's open, equalize pressure between inlet and outlet volumes according to flowrate
        for valve in self.valves.values():
            if valve.state == OPEN:
                inlet_volume = self.volumes.get(valve.inlet_volume_name.lower())
                outlet_volume = self.volumes.get(valve.outlet_volume_name.lower())
                if inlet_volume is None or outlet_volume is None:
                    error_and_exit(f"Valve {valve.channel} has invalid inlet or outlet volume name, please check your simulation parameters file")
                # Simple flow model: flowrate is proportional to pressure differential, with some constant of proportionality
                pressure_diff = inlet_volume.pressure - outlet_volume.pressure
                flowrate = 0.01 * pressure_diff  # liters per second at 1 psi pressure differential, adjust as needed
                # Update pressures of inlet and outlet volumes according to flowrate and volume size
                inlet_volume.pressure -= flowrate / inlet_volume.volume
                outlet_volume.pressure += flowrate / outlet_volume.volume
                # If it's a check valve, only allow flow from inlet to outlet
                if valve.is_check_valve and pressure_diff < 0:
                    inlet_volume.pressure += flowrate / inlet_volume.volume
                    outlet_volume.pressure -= flowrate / outlet_volume.volume

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

def synnax_to_alias(aliased_name: str, aliases: dict[str, str]) -> str:
    for alias, synnax_ch_name in aliases.items():
        if synnax_ch_name == aliased_name:
            return alias
    error_and_exit(f"Could not find unaliased name for {aliased_name} in aliases, please check your alias file")

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
def driver(streamer: sy.Streamer, writer: sy.Writer, sim: Simulation, aliases: dict[str, str]) -> None:
    loop = sy.Loop(interval=(sy.Rate.HZ * sim.frequency))

    while loop.wait():
        write_data: dict = {}
        write_data["time"] = sy.TimeStamp.now()

        # Check for incoming valve commands
        fr = streamer.read(timeout=0)
        if fr is not None:
            for synnax_ch_name in fr.channels:
                cmd = fr[synnax_ch_name][0]
                valve = sim.valves.get(synnax_to_alias(synnax_ch_name, aliases))
                if valve is None:
                    spinner.write(f" > Valve command received for unmapped channel {synnax_ch_name}, ignoring...")
                    continue
                if valve.is_normally_open:
                    if cmd == 1:  # command to close the valve
                        valve.state = CLOSED
                        spinner.write(f" > Valve {valve.channel} closed")
                    elif cmd == 0:  # command to open the valve
                        valve.state = OPEN
                        spinner.write(f" > Valve {valve.channel} opened")
                else:
                    if cmd == 1:  # command to open the valve
                        valve.state = OPEN
                        spinner.write(f" > Valve {valve.channel} opened")
                    elif cmd == 0:  # command to close the valve
                        valve.state = CLOSED
                        spinner.write(f" > Valve {valve.channel} closed")

        # Write current valve stats
        for valve in sim.valves.values():
            state_ch = aliases[valve.channel].replace("vlv", "state")
            if valve.is_normally_open:
                if valve.state == OPEN:
                    write_data[state_ch] = 0
                else:
                    write_data[state_ch] = 1
            else:
                if valve.state == OPEN:
                    write_data[state_ch] = 1
                else:
                    write_data[state_ch] = 0

        for volume in sim.volumes.values():
            for ch in volume.channels:
                synnax_ch_name = aliases.get(ch)
                if "pt" in ch:
                    # add noise if enabled
                    noise = 0.0
                    if sim.do_noise:
                        noise = random.gauss(0, sim.default_pt_noise_sigma)
                    write_data[synnax_ch_name] = volume.pressure + noise
                elif "tc" in ch:
                    # add noise if enabled
                    noise = 0.0
                    if sim.do_noise:
                        noise = random.gauss(0, sim.default_tc_noise_sigma)
                    write_data[synnax_ch_name] = volume.temperature + noise
        writer.write(write_data)  # type: ignore
        sim.update_physics()

@yaspin(text=colored("Setting up channels...", "yellow"))
def setup_channels(client: sy.Synnax, sim: Simulation, aliases: dict[str, str]) -> tuple[list[str], list[str]]:
    read_channels: list[str] = []
    write_channels: list[str] = []
    
    # time channel always exists
    time_channel = client.channels.create(
        retrieve_if_name_exists=True,
        name="time",
        data_type=sy.DataType.TIMESTAMP,
        virtual=False,
        is_index=True,
    )
    write_channels.append("time") # add time channel to list of channels to write to

    for volume in sim.volumes.values():
        for ch_name in volume.channels:
            synnax_ch_name = aliases.get(ch_name)
            if synnax_ch_name is None:
                error_and_exit(f"Channel {ch_name} for volume {volume.name} not found in aliases, please check your alias file")
            if "pt" in synnax_ch_name:
                client.channels.create(
                    retrieve_if_name_exists=True,
                    name=synnax_ch_name,
                    data_type=sy.DataType.FLOAT32,
                    virtual=False,
                    index=time_channel.key,
                )
            elif "tc" in synnax_ch_name:
                client.channels.create(
                    retrieve_if_name_exists=True,
                    name=synnax_ch_name,
                    data_type=sy.DataType.FLOAT32,
                    virtual=False,
                    index=time_channel.key,
                )
            write_channels.append(synnax_ch_name) # add to list of channels to write to
    for valve in sim.valves.values():
        synnax_ch_name = aliases.get(valve.channel)
        if synnax_ch_name is None:
            error_and_exit(f"Channel {valve.channel} for valve not found in aliases, please check your alias file")
        client.channels.create(
            retrieve_if_name_exists=True,
            name=synnax_ch_name,
            data_type=sy.DataType.INT8,
            virtual=False,
            index=time_channel.key,
        )
        read_channels.append(synnax_ch_name)  # add to list of channels to read from
        # also create state channel for each valve
        state_ch_name = synnax_ch_name.replace("vlv", "state")
        client.channels.create(
            retrieve_if_name_exists=True,
            name=state_ch_name,
            data_type=sy.DataType.INT8,
            virtual=False,
            index=time_channel.key,
        )
        write_channels.append(state_ch_name) # add to list of channels to write to

    return write_channels, read_channels

def main():
    args = parse_args()
    aliases = parse_aliases(args.aliases)
    simulation = Simulation(args.sim_params)
    client = synnax_login(args.cluster)
    write_channels, read_channels = setup_channels(client, simulation, aliases)

    # Open streamer for valve commands
    with client.open_streamer(channels=read_channels) as streamer:
        # Open writer for everything else
        with client.open_writer(start=sy.TimeStamp.now(), channels=write_channels) as writer:
            driver(streamer, writer, simulation, aliases)  # Run the fake driver


if __name__ == "__main__":
    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports
    try:
        main()
    except KeyboardInterrupt:  # Abort cases also rely on this, but Python takes the closest exception catch inside nested calls
        error_and_exit("Keyboard interrupt detected")
