# Not a script! Don't try to run this, just a collection of utilities

import math
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
        self.state = OPEN if is_normally_open else CLOSED

class Simulation:
    # Sim settings
    do_noise: bool
    default_pt_noise_sigma: int
    do_temp_simulation: bool
    default_tc_noise_sigma: int
    gas_specific_heat_ratio: float
    ambient_temperature: float # C
    thermal_equilibrium_time_constant: float | None # seconds; None uses thermal conductance
    default_heat_transfer_coefficient: float # W/K, effective gas-to-surroundings conductance
    heat_transfer_coefficients: dict[str, float] # optional overrides by volume name
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
        self.gas_specific_heat_ratio = raw_params.get("gas_specific_heat_ratio", 1.4)
        self.ambient_temperature = raw_params.get("ambient_temperature", 20.0)
        self.thermal_equilibrium_time_constant = raw_params.get("thermal_equilibrium_time_constant")
        self.default_heat_transfer_coefficient = raw_params.get("default_heat_transfer_coefficient", 10.0)
        self.heat_transfer_coefficients = raw_params.get("heat_transfer_coefficients", {})
        if not math.isfinite(self.gas_specific_heat_ratio) or self.gas_specific_heat_ratio <= 1:
            raise ValueError("gas_specific_heat_ratio must be finite and greater than one")
        if not math.isfinite(self.ambient_temperature) or self.ambient_temperature <= -273.15:
            raise ValueError("ambient_temperature must be finite and above absolute zero")
        if self.thermal_equilibrium_time_constant is not None:
            if (not math.isfinite(self.thermal_equilibrium_time_constant) or
                    self.thermal_equilibrium_time_constant <= 0):
                raise ValueError("thermal_equilibrium_time_constant must be finite and positive, or null")
        for coefficient in (self.default_heat_transfer_coefficient, *self.heat_transfer_coefficients.values()):
            if not math.isfinite(coefficient) or coefficient < 0:
                raise ValueError("Heat transfer coefficients must be finite and nonnegative")

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
                    readings[channel_name] = volume.temperature + noise
        for valve in self.valves:
            channel_name = (self.reverse_aliases[valve.channel]).replace("vlv", "state")
            if not valve.is_normally_open:
                readings[channel_name] = valve.state
            else:
                readings[channel_name] = not valve.state
        return readings

    def set_valve_state(self, channel_name: str, state: bool) -> None:
        alias = self.aliases[channel_name]
        for valve in self.valves:
            if (valve.channel == alias):
                valve.state = (not bool(state)) if valve.is_normally_open else bool(state)

    def simulation_step(self, time_step: float) -> None:
        """Advance by elapsed seconds using a simple, pressure-driven gas flow.

        Volume.volume is the fixed tank capacity in liters; the amount of gas
        changes instead. Pressures are gauge psi and temperatures are Celsius.
        Flow coefficients are effective areas, with a deliberately naive flow
        speed of one meter/second per psi of pressure difference. Temperature
        simulation uses ideal gas energy (Cp/Cv defaults to 1.4 for nitrogen)
        and heat exchange with a fixed ambient heat sink representing the tank
        wall and surroundings. Disabling it holds temperatures constant.
        """
        if not math.isfinite(time_step) or time_step < 0:
            raise ValueError("time_step must be finite and nonnegative")
        if time_step == 0:
            return

        atmospheric_pressure = 14.6959  # absolute psi
        gas_constant = 1.20591  # psi * liters / (mol * kelvin)
        gamma = self.gas_specific_heat_ratio if self.do_temp_simulation else 1.0
        molar_heat_capacity = 8.314462618 / (self.gas_specific_heat_ratio - 1) # Cv, J/(mol*K)
        ambient_temperature = self.ambient_temperature + 273.15
        volumes = {volume.name: volume for volume in self.volumes}
        atmosphere = self.atmosphere_volume_name
        pressures = {name: volume.pressure for name, volume in volumes.items()}
        temperatures = {name: volume.temperature + 273.15 for name, volume in volumes.items()}
        # The atmosphere can be a virtual endpoint absent from the YAML.
        pressures.setdefault(atmosphere, 0.0)
        temperatures.setdefault(atmosphere, ambient_temperature)

        amounts = {}
        for name, volume in volumes.items():
            if (not math.isfinite(pressures[name]) or
                    pressures[name] <= -atmospheric_pressure or
                    not math.isfinite(temperatures[name]) or temperatures[name] <= 0):
                raise ValueError(f"Volume {name!r} needs positive absolute pressure and temperature")
            if name == atmosphere:
                continue
            if not math.isfinite(volume.volume) or volume.volume <= 0:
                raise ValueError(f"Volume {name!r} must have a positive, finite capacity")
            amounts[name] = ((pressures[name] + atmospheric_pressure) * volume.volume /
                             (gas_constant * temperatures[name]))
        heat_transfer = {
            name: self.heat_transfer_coefficients.get(name, self.default_heat_transfer_coefficient)
            for name in amounts
        }

        def settling_time(name: str) -> float:
            if self.thermal_equilibrium_time_constant is not None:
                return self.thermal_equilibrium_time_constant
            if heat_transfer[name] == 0:
                return math.inf
            return amounts[name] * molar_heat_capacity / heat_transfer[name]

        connections = []
        degree = {name: 0 for name in pressures}
        for valve in self.valves:
            if not valve.state:
                continue
            inlet, outlet = valve.inlet_volume_name, valve.outlet_volume_name
            if inlet not in pressures or outlet not in pressures:
                raise ValueError(f"Valve {valve.channel!r} references an unknown volume")
            if not math.isfinite(valve.flow_coefficient) or valve.flow_coefficient < 0:
                raise ValueError(f"Valve {valve.channel!r} needs a nonnegative, finite flow coefficient")
            if inlet == outlet or valve.flow_coefficient == 0:
                continue
            connections.append(valve)
            degree[inlet] += 1
            degree[outlet] += 1

        remaining = time_step
        while remaining > 0:
            amount_rates = dict.fromkeys(amounts, 0.0)
            energy_rates = dict.fromkeys(amounts, 0.0)  # energy divided by Cv
            outgoing_rates = dict.fromkeys(amounts, 0.0)
            step = remaining
            for valve in connections:
                source, destination = valve.inlet_volume_name, valve.outlet_volume_name
                difference = pressures[source] - pressures[destination]
                if difference < 0:
                    if valve.is_check_valve:
                        continue
                    source, destination = destination, source
                    difference = -difference
                if difference == 0:
                    continue

                # Convert a naive atmospheric-equivalent liters/second flow
                # into moles/second, conserving gas between connected tanks.
                rate = (valve.flow_coefficient * 1000 * difference * atmospheric_pressure /
                        (gas_constant * temperatures[source]))
                if rate == 0:
                    continue
                pressure_rate = 0.0
                for name, direction in ((source, -1), (destination, 1)):
                    if name == atmosphere:
                        continue
                    amount_rates[name] += direction * rate
                    energy_rates[name] += direction * gamma * temperatures[source] * rate
                    if direction < 0:
                        outgoing_rates[name] += rate
                    flow_temperature = temperatures[source] if self.do_temp_simulation else temperatures[name]
                    pressure_rate += gamma * gas_constant * flow_temperature * rate / volumes[name].volume

                # Subdivide large calls so even a tiny manifold or many open
                # valves cannot overshoot equilibrium in a single update.
                if pressure_rate > 0:
                    step = min(step, 0.5 * difference / pressure_rate /
                               max(degree[source], degree[destination]))

            for name, rate in outgoing_rates.items():
                if rate > 0:
                    step = min(step, amounts[name] / (2 * gamma * rate))
                # Resolve heat-driven pressure changes while valves are open,
                # including when connected tanks initially have equal pressure.
                if (self.do_temp_simulation and connections and
                        temperatures[name] != ambient_temperature):
                    step = min(step, 0.25 * settling_time(name))

            for name in amounts:
                energy = amounts[name] * temperatures[name] + energy_rates[name] * step
                amounts[name] += amount_rates[name] * step
                if self.do_temp_simulation:
                    temperatures[name] = energy / amounts[name]
                    # Exponential recovery with either the configured settling
                    # time or the conductance-based time at the new gas amount.
                    # Closed valves still allow recovery toward ambient.
                    cooling_exponent = step / settling_time(name)
                    temperatures[name] += ((ambient_temperature - temperatures[name]) *
                                           -math.expm1(-cooling_exponent))
                pressures[name] = (amounts[name] * gas_constant * temperatures[name] /
                                   volumes[name].volume - atmospheric_pressure)
            remaining -= step

        for name, volume in volumes.items():
            if name != atmosphere:
                volume.pressure = pressures[name]
                if self.do_temp_simulation:
                    volume.temperature = temperatures[name] - 273.15
