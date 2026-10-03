# Not a script! Don't try to run this, just a collection of utilities

from dataclasses import dataclass
import random
import yaml
from typing import Final, Any
from pathlib import Path

# Alias for boolean state of a valve to make things easier to read
OPEN: Final[bool] = True
CLOSED: Final[bool] = False

class Volume:
    name: str
    volume: float # liters
    pressure: float # psi
    temperature: float # C
    channels: list[str]

    def __init__(self, name: str, volume: float, initial_pressure: float, initial_temperature: float, channels: list[str]):
        self.name = name
        self.volume = volume
        self.pressure = initial_pressure
        self.temperature = initial_temperature
        self.pressure = initial_pressure
        self.channels = channels

class Valve:
    channel: str
    inlet_volume_name: str
    outlet_volume_name: str
    flow_coefficient: float
    is_check_valve: bool
    is_normally_open: bool

    state: bool # True = open, False = closed

    def __init__(self, channel: str, inlet: str, outlet: str, flow_coefficient: float, is_check_valve: bool, is_normally_open: bool):
        self.channel = channel
        self.inlet_volume_name = inlet
        self.outlet_volume_name = outlet
        self.flow_coefficient = flow_coefficient
        self.is_check_valve = is_check_valve
        self.is_normally_open = is_normally_open
        self.state = CLOSED

class Simulation:
    # Sim settings
    do_noise: bool
    default_pt_noise_sigma: int
    do_temp_simulation: bool
    default_tc_noise_sigma: int
    frequency: int # Hz
    atmosphere_volume_name: str
    # Aliases
    aliases: dict[str, str]
    reverse_aliases: dict[str, str]
    # Sim state
    volumes: list[Volume]
    valves: list[Valve]

    def __init__(self, sim_params_path: Path, aliases_path: Path):
        self.aliases = {}
        self.reverse_aliases = {}
        self.volumes = []
        self.valves = []
        self.parse_aliases(aliases_path)
        self.parse_sim_params(sim_params_path)

    def parse_aliases(self, aliases_path: Path) -> None:
        # Load raw YAML
        raw_aliases = {}
        with open(aliases_path, "r") as f:
            raw_aliases = yaml.safe_load(f)
        # Build new dict with prefixes
        for controller_prefix, channel_type_prefixes in raw_aliases.items():
            for channel_type_prefix, channel_ids in channel_type_prefixes.items():
                for channel_id, alias in channel_ids.items():
                    channel_full_name = f"{controller_prefix}_{channel_type_prefix}_{channel_id}"
                    self.aliases[channel_full_name] = alias
                    self.reverse_aliases[alias] = channel_full_name

    def parse_sim_params(self, sim_params: Path) -> None:
        raw_params = {}
        with open(sim_params, 'r') as f:
            raw_params = yaml.safe_load(f)

        self.do_noise = raw_params["do_noise"]
        self.default_pt_noise_sigma = raw_params["default_pt_noise_sigma"]
        self.do_temp_simulation = raw_params["do_temp_simulation"]
        self.default_tc_noise_sigma = raw_params["default_tc_noise_sigma"]
        self.frequency = raw_params["frequency"]
        self.atmosphere_volume_name = raw_params["atmosphere_volume_name"]

        for volume in raw_params["volumes"]:
            self.volumes.append(Volume(**volume))

        for valve in raw_params["valves"]:
            self.valves.append(Valve(**valve))

    def get_valve_channels(self) -> list[str]:
        valve_channels = []
        for valve in self.valves:
            valve_channels.append(self.reverse_aliases[valve.channel])
        return valve_channels

    def get_sensor_channels(self) -> list[str]:
        sensor_channels = []
        for volume in self.volumes:
            for sensor_channel in volume.channels:
                sensor_channels.append(self.reverse_aliases[sensor_channel])
        return sensor_channels

    # Returns PT, TC, and valve state data with mapping: REAL_CHANNEL_NAME: float | bool
    # Adds noise based on simulation configuration
    def get_channel_readings(self) -> dict[str, Any]:
        readings = {}
        for volume in self.volumes:
            for alias in volume.channels:
                channel_name = self.reverse_aliases[alias]
                if "pt" in channel_name:
                    noise = random.gauss(0, self.default_pt_noise_sigma) if (self.do_noise) else (0)
                    readings[channel_name] = volume.pressure + noise
                if "tc" in channel_name:
                    noise = random.gauss(0, self.default_tc_noise_sigma) if (self.do_noise) else (0)
                    readings[channel_name] = volume.temperature
        for valve in self.valves:
            channel_name = (self.reverse_aliases[valve.channel]).replace("vlv", "state")
            readings[channel_name] = valve.state
        return readings

    def set_valve_state(self, channel_name: str, state: bool) -> None:
        alias = self.aliases[channel_name]
        for valve in self.valves:
            if (valve.channel == alias):
                valve.state = state

    def simulation_step(self, time_step: float) -> None:
        pass
