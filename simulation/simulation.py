#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax>=0.55.0",
#     "yaspin",
#     "termcolor",
#     "pyyaml",
#     "CoolProp>=6.6",
# ]
# ///

from termcolor import colored
from yaspin import yaspin

spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

import argparse
import math
import os
import random
from dataclasses import dataclass
from typing import Any, Final, NoReturn, cast

import synnax as sy
from CoolProp.CoolProp import PropsSI  # pyrefly: ignore[missing-import]
from synnax.framer.frame import CrudeFrame

# --- Constants ---

OPEN: Final[bool] = True
CLOSED: Final[bool] = False

PSI_TO_PA = 6894.757293168
PA_TO_PSI = 1.0 / PSI_TO_PA
LITERS_TO_M3 = 1.0e-3
AMBIENT_TEMPERATURE_C = 20.0
AMBIENT_PRESSURE_PSI = 14.7
AMBIENT_TEMPERATURE_K = AMBIENT_TEMPERATURE_C + 273.15
AMBIENT_PRESSURE_PA = AMBIENT_PRESSURE_PSI * PSI_TO_PA
MIN_MASS_KG = 1.0e-9
MASS_CHANGE_FRACTION_LIMIT = 0.05
DEFAULT_FLUID = "Nitrogen"
MIN_ABSOLUTE_PRESSURE_PA = 1000.0  # CoolProp lower bound


def gauge_psi_to_absolute_pa(gauge_psi: float) -> float:
    """Convert gauge pressure (psi) to absolute pressure (Pa) for thermodynamics."""
    return max((gauge_psi + AMBIENT_PRESSURE_PSI) * PSI_TO_PA, MIN_ABSOLUTE_PRESSURE_PA)


def absolute_pa_to_gauge_psi(p_pa: float) -> float:
    """Convert absolute pressure (Pa) to gauge pressure (psi) for PT telemetry."""
    return p_pa * PA_TO_PSI - AMBIENT_PRESSURE_PSI


# --- Physics ---


@dataclass
class FlowContribution:
    """Mass and enthalpy flow into a volume (positive = gain)."""

    mass_rate: float = 0.0  # kg/s
    enthalpy_rate: float = 0.0  # W (m_dot * h)


@dataclass
class Volume:
    """Physical fluid container with mass/energy state and CoolProp-derived properties."""

    name: str
    volume_m3: float
    channels: list[str]
    fluid: str
    wall_ua: float  # W/K
    mass: float  # kg
    internal_energy: float  # J
    initial_temperature_k: float
    is_reservoir: bool = False

    @classmethod
    def from_config(
        cls,
        name: str,
        volume_liters: float,
        initial_pressure_psi: float,
        initial_temperature_c: float,
        channels: list[str],
        fluid: str = DEFAULT_FLUID,
        wall_ua: float = 0.0,
        is_reservoir: bool = False,
    ) -> "Volume":
        volume_m3 = volume_liters * LITERS_TO_M3
        t_k = initial_temperature_c + 273.15
        p_pa = gauge_psi_to_absolute_pa(initial_pressure_psi)

        if is_reservoir:
            density = PropsSI("D", "P", AMBIENT_PRESSURE_PA, "T", AMBIENT_TEMPERATURE_K, fluid)
            mass = density * volume_m3 if volume_m3 > 0 else 1.0
            u = PropsSI("U", "P", AMBIENT_PRESSURE_PA, "T", AMBIENT_TEMPERATURE_K, fluid)
        else:
            density = PropsSI("D", "P", p_pa, "T", t_k, fluid)
            mass = max(density * volume_m3, MIN_MASS_KG)
            u = PropsSI("U", "P", p_pa, "T", t_k, fluid)

        return cls(
            name=name,
            volume_m3=volume_m3,
            channels=channels,
            fluid=fluid,
            wall_ua=wall_ua,
            mass=mass,
            internal_energy=mass * u,
            initial_temperature_k=t_k,
            is_reservoir=is_reservoir,
        )

    @property
    def density(self) -> float:
        return self.mass / self.volume_m3

    @property
    def specific_internal_energy(self) -> float:
        return self.internal_energy / self.mass

    @property
    def pressure_pa(self) -> float:
        if self.is_reservoir:
            return AMBIENT_PRESSURE_PA
        return float(
            PropsSI(
                "P",
                "D",
                self.density,
                "U",
                self.specific_internal_energy,
                self.fluid,
            )
        )

    @property
    def temperature_k(self) -> float:
        if self.is_reservoir:
            return AMBIENT_TEMPERATURE_K
        return float(
            PropsSI(
                "T",
                "D",
                self.density,
                "U",
                self.specific_internal_energy,
                self.fluid,
            )
        )

    @property
    def pressure(self) -> float:
        """Gauge pressure in psi for telemetry."""
        return absolute_pa_to_gauge_psi(self.pressure_pa)

    @property
    def temperature(self) -> float:
        """Temperature in C for telemetry."""
        return self.temperature_k - 273.15

    def thermo_state(self) -> tuple[float, float, float]:
        """Return (P_pa, T_k, h_J/kg) for flow calculations."""
        p = self.pressure_pa
        t = self.temperature_k
        h = float(PropsSI("H", "P", p, "T", t, self.fluid))
        return p, t, h

    def clamp_mass(self) -> None:
        self.mass = max(self.mass, MIN_MASS_KG)

    def enforce_isothermal(self) -> None:
        u = float(
            PropsSI(
                "U",
                "D",
                self.density,
                "T",
                self.initial_temperature_k,
                self.fluid,
            )
        )
        self.internal_energy = self.mass * u


class Valve:
    """Valve connecting two volumes (or a volume and the atmosphere)."""

    channel: str
    is_normally_open: bool
    is_check_valve: bool
    inlet_volume_name: str
    outlet_volume_name: str
    cda: float  # Cd * A in m^2
    state: bool

    def __init__(
        self,
        channel: str,
        is_normally_open: bool,
        is_check_valve: bool,
        inlet_volume_name: str,
        outlet_volume_name: str,
        cda: float = 1.0e-5,
    ) -> None:
        self.channel = channel
        self.is_normally_open = is_normally_open
        self.is_check_valve = is_check_valve
        self.inlet_volume_name = inlet_volume_name.lower()
        self.outlet_volume_name = outlet_volume_name.lower()
        self.cda = cda
        self.state = OPEN if is_normally_open else CLOSED


def _fluid_gamma(fluid: str, p_pa: float, t_k: float) -> float:
    cp = float(PropsSI("CPMASS", "P", p_pa, "T", t_k, fluid))
    cv = float(PropsSI("CVMASS", "P", p_pa, "T", t_k, fluid))
    return cp / cv


def _fluid_gas_constant(fluid: str) -> float:
    return float(PropsSI("GAS_CONSTANT", fluid)) / float(PropsSI("MOLAR_MASS", fluid))


def compressible_mass_flow(
    cda: float,
    p_up_pa: float,
    t_up_k: float,
    p_down_pa: float,
    fluid: str,
) -> float:
    """Mass flow rate (kg/s) through an orifice; upstream conditions."""
    if p_up_pa <= p_down_pa or p_up_pa <= 0 or t_up_k <= 0:
        return 0.0

    gamma = _fluid_gamma(fluid, p_up_pa, t_up_k)
    r_specific = _fluid_gas_constant(fluid)
    r_ratio = p_down_pa / p_up_pa
    r_crit = (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))

    if r_ratio <= r_crit:
        term = (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
        return cda * p_up_pa * math.sqrt(gamma / (r_specific * t_up_k)) * term

    inner = (2.0 * gamma / (gamma - 1.0)) / (r_specific * t_up_k)
    inner *= r_ratio ** (2.0 / gamma) - r_ratio ** ((gamma + 1.0) / gamma)
    if inner <= 0:
        return 0.0
    return cda * p_up_pa * math.sqrt(inner)


class Simulation:
    """Full fluid system with real-gas thermodynamics."""

    volumes: dict[str, Volume]
    valves: dict[str, Valve]
    do_noise: bool
    default_pt_noise_sigma: float
    do_temp_simulation: bool
    default_tc_noise_sigma: float
    frequency: int
    atmosphere_volume_name: str

    def __init__(self, params_path: str) -> None:
        yaml_dict = load_yaml(params_path)
        try:
            self.do_noise = bool(yaml_dict.get("do_noise", False))
            self.default_pt_noise_sigma = float(yaml_dict.get("default_pt_noise_sigma", 0.0))
            self.do_temp_simulation = bool(yaml_dict.get("do_temp_simulation", False))
            self.default_tc_noise_sigma = float(yaml_dict.get("default_tc_noise_sigma", 0.0))
            self.frequency = int(yaml_dict.get("frequency", 10))
            self.atmosphere_volume_name = str(
                yaml_dict.get("atmosphere_volume_name", "atmosphere")
            ).lower()

            self.volumes = {}
            for vol_data in yaml_dict.get("volumes", []):
                if not isinstance(vol_data, dict):
                    continue
                name = str(_require(vol_data, "name", params_path)).lower()
                self.volumes[name] = Volume.from_config(
                    name=name,
                    volume_liters=float(_require(vol_data, "volume", params_path)),
                    initial_pressure_psi=float(
                        _require(vol_data, "initial_pressure", params_path)
                    ),
                    initial_temperature_c=float(
                        vol_data.get("initial_temperature", AMBIENT_TEMPERATURE_C)
                    ),
                    channels=list(map(str.lower, vol_data.get("channels", []))),
                    fluid=str(vol_data.get("fluid", DEFAULT_FLUID)),
                    wall_ua=float(vol_data.get("wall_ua", 0.0)),
                )

            self.valves = {}
            for vlv_data in yaml_dict.get("valves", []):
                if not isinstance(vlv_data, dict):
                    continue
                channel = str(_require(vlv_data, "channel", params_path)).lower()
                self.valves[channel] = Valve(
                    channel=channel,
                    is_normally_open=bool(vlv_data.get("is_normally_open", False)),
                    is_check_valve=bool(vlv_data.get("is_check_valve", False)),
                    inlet_volume_name=str(_require(vlv_data, "inlet", params_path)),
                    outlet_volume_name=str(_require(vlv_data, "outlet", params_path)),
                    cda=float(vlv_data.get("flow_coefficient", 1.0e-5)),
                )
        except KeyError as e:
            error_and_exit(
                f"Missing required key {e} in simulation parameters file {params_path}"
            )
        except Exception as e:
            error_and_exit(
                f"Error parsing simulation parameters from {params_path}", exception=e
            )

    def _resolve_volume(self, name: str) -> Volume | None:
        key = name.lower()
        if key == self.atmosphere_volume_name:
            return None
        return self.volumes.get(key)

    def _atmosphere_state(self, fluid: str) -> tuple[float, float, float]:
        h = float(
            PropsSI(
                "H",
                "P",
                AMBIENT_PRESSURE_PA,
                "T",
                AMBIENT_TEMPERATURE_K,
                fluid,
            )
        )
        return AMBIENT_PRESSURE_PA, AMBIENT_TEMPERATURE_K, h

    def _compute_valve_flow(
        self, valve: Valve
    ) -> tuple[Volume | None, Volume | None, float, float]:
        """
        Returns (upstream_vol, downstream_vol, m_dot, h_upstream).
        Either volume may be None when that side is the atmosphere.
        """
        inlet = self._resolve_volume(valve.inlet_volume_name)
        outlet = self._resolve_volume(valve.outlet_volume_name)
        inlet_is_atm = valve.inlet_volume_name == self.atmosphere_volume_name
        outlet_is_atm = valve.outlet_volume_name == self.atmosphere_volume_name

        if inlet_is_atm and outlet_is_atm:
            return None, None, 0.0, 0.0

        fluid = DEFAULT_FLUID
        if inlet is not None:
            fluid = inlet.fluid
        elif outlet is not None:
            fluid = outlet.fluid

        if inlet_is_atm:
            p_in, t_in, h_in = self._atmosphere_state(fluid)
        else:
            assert inlet is not None
            p_in, t_in, h_in = inlet.thermo_state()

        if outlet_is_atm:
            p_out, _, _ = self._atmosphere_state(fluid)
        else:
            assert outlet is not None
            p_out, _, _ = outlet.thermo_state()

        if abs(p_in - p_out) < 1.0:
            return None, None, 0.0, 0.0

        if p_in >= p_out:
            up_vol, down_vol = inlet, outlet
            p_up, t_up, h_up = p_in, t_in, h_in
            p_down = p_out
            nominal_forward = True
        else:
            up_vol, down_vol = outlet, inlet
            if outlet_is_atm:
                p_up, t_up, h_up = self._atmosphere_state(fluid)
            else:
                assert outlet is not None
                p_up, t_up, h_up = outlet.thermo_state()
            p_down = p_in
            nominal_forward = False

        if valve.is_check_valve and not nominal_forward:
            return None, None, 0.0, 0.0

        m_dot = compressible_mass_flow(valve.cda, p_up, t_up, p_down, fluid)
        return up_vol, down_vol, m_dot, h_up

    def _integrate_substep(self, dt: float) -> int:
        """One physics substep; returns number of substeps used (1 if no refinement)."""
        contributions: dict[str, FlowContribution] = {
            name: FlowContribution() for name in self.volumes
        }

        max_mass_fraction = 0.0
        for valve in self.valves.values():
            if valve.state != OPEN:
                continue
            up, down, m_dot, h_up = self._compute_valve_flow(valve)
            if m_dot <= 0:
                continue

            dm = m_dot * dt

            if up is not None:
                contributions[up.name].mass_rate -= m_dot
                contributions[up.name].enthalpy_rate -= m_dot * h_up
                if up.mass > 0:
                    max_mass_fraction = max(max_mass_fraction, dm / up.mass)

            if down is not None:
                contributions[down.name].mass_rate += m_dot
                contributions[down.name].enthalpy_rate += m_dot * h_up
                if down.mass > 0:
                    max_mass_fraction = max(max_mass_fraction, dm / down.mass)

        if max_mass_fraction > MASS_CHANGE_FRACTION_LIMIT:
            n_sub = max(2, int(math.ceil(max_mass_fraction / MASS_CHANGE_FRACTION_LIMIT)))
            sub_dt = dt / n_sub
            for _ in range(n_sub):
                self._integrate_substep(sub_dt)
            return n_sub

        for vol in self.volumes.values():
            if vol.is_reservoir:
                continue
            c = contributions[vol.name]
            vol.mass += c.mass_rate * dt
            if self.do_temp_simulation:
                q_wall = vol.wall_ua * (AMBIENT_TEMPERATURE_K - vol.temperature_k)
                vol.internal_energy += c.enthalpy_rate * dt + q_wall * dt
            vol.clamp_mass()
            if not self.do_temp_simulation:
                vol.enforce_isothermal()

        return 1

    def update_physics(self) -> None:
        dt = 1.0 / self.frequency
        self._integrate_substep(dt)


# --- YAML / aliases ---


def load_yaml(path: str) -> dict[str, Any]:
    import yaml

    with open(path) as f:
        yaml_dict = yaml.safe_load(f)
    if yaml_dict is None:
        error_and_exit(f"YAML file {path} is empty or not properly formatted")
    if not isinstance(yaml_dict, dict):
        error_and_exit(f"YAML file {path} must contain a mapping at the top level")
    return yaml_dict


def _require(data: dict[str, Any], key: str, context: str) -> Any:
    if key not in data:
        raise KeyError(f"{key} (in {context})")
    return data[key]


def parse_aliases(aliases_path: str) -> dict[str, str]:
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

    mappings_raw = yaml_dict.get("channel_mappings")
    if not mappings_raw or not isinstance(mappings_raw, dict):
        error_and_exit(
            f"Alias file {aliases_path} is missing 'channel_mappings' key or it is empty."
        )
    mappings_data: dict[str, Any] = mappings_raw

    for controller_key, prefix in prefix_map.items():
        controller_data = mappings_data.get(controller_key)
        if not controller_data or not isinstance(controller_data, dict):
            continue

        for type_key, suffix in type_suffix_map.items():
            items = controller_data.get(type_key)
            if not items or not isinstance(items, dict):
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
                    error_and_exit(
                        f"Missing key {e} for channel {config_ch_name} in {aliases_path}"
                    )
                except Exception as e:
                    error_and_exit(
                        f"Error parsing channel {config_ch_name} in {aliases_path}",
                        exception=e,
                    )
    return aliases


def synnax_to_alias(aliased_name: str, aliases: dict[str, str]) -> str:
    name = str(aliased_name)
    for alias, synnax_ch_name in aliases.items():
        if synnax_ch_name == name:
            return alias
    error_and_exit(
        f"Could not find unaliased name for {name} in aliases, please check your alias file"
    )


def resolve_alias(ch: str, aliases: dict[str, str]) -> str:
    synnax_name = aliases.get(ch)
    if synnax_name is None:
        error_and_exit(
            f"Channel {ch} not found in aliases, please check your alias file"
        )
    return synnax_name


def error_and_exit(
    message: str, error_code: int = 1, exception: BaseException | None = None
) -> NoReturn:
    spinner.stop()
    if exception is not None:
        print(exception)
    print(colored(message, "red", attrs=["bold"]))
    print(colored("Exiting", "red", attrs=["bold"]))
    raise SystemExit(error_code)


# --- CLI ---


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
        default=os.getenv("SYNNAX_CLUSTER", "localhost"),
        type=str,
    )
    return parser.parse_args()


# --- Synnax I/O ---


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
        error_and_exit(
            f"Could not connect to Synnax at {cluster}, are you sure you're connected?"
        )


@yaspin(text=colored("Running Simulation...", "green"))
def driver(
    streamer: sy.Streamer,
    writer: sy.Writer,
    sim: Simulation,
    aliases: dict[str, str],
) -> None:
    loop = sy.Loop(interval=(sy.Rate.HZ * sim.frequency))

    while loop.wait():
        write_data: dict[str, Any] = {}
        write_data["time"] = sy.TimeStamp.now()

        fr = streamer.read(timeout=0)
        if fr is not None:
            for synnax_ch_name in fr.channels:
                cmd = fr[synnax_ch_name][0]
                valve = sim.valves.get(synnax_to_alias(str(synnax_ch_name), aliases))
                if valve is None:
                    spinner.write(
                        f" > Valve command received for unmapped channel {synnax_ch_name}, ignoring..."
                    )
                    continue
                if valve.is_normally_open:
                    if cmd == 1:
                        valve.state = CLOSED
                        spinner.write(f" > Valve {valve.channel} closed")
                    elif cmd == 0:
                        valve.state = OPEN
                        spinner.write(f" > Valve {valve.channel} opened")
                else:
                    if cmd == 1:
                        valve.state = OPEN
                        spinner.write(f" > Valve {valve.channel} opened")
                    elif cmd == 0:
                        valve.state = CLOSED
                        spinner.write(f" > Valve {valve.channel} closed")

        for valve in sim.valves.values():
            state_ch = resolve_alias(valve.channel, aliases).replace("vlv", "state")
            if valve.is_normally_open:
                write_data[state_ch] = 0 if valve.state == OPEN else 1
            else:
                write_data[state_ch] = 1 if valve.state == OPEN else 0

        for volume in sim.volumes.values():
            for ch in volume.channels:
                synnax_ch_name = resolve_alias(ch, aliases)
                if "pt" in ch:
                    noise = (
                        random.gauss(0, sim.default_pt_noise_sigma)
                        if sim.do_noise
                        else 0.0
                    )
                    write_data[synnax_ch_name] = volume.pressure + noise
                elif "tc" in ch:
                    noise = (
                        random.gauss(0, sim.default_tc_noise_sigma)
                        if sim.do_noise
                        else 0.0
                    )
                    write_data[synnax_ch_name] = volume.temperature + noise

        writer.write(cast(CrudeFrame, write_data))
        sim.update_physics()


@yaspin(text=colored("Setting up channels...", "yellow"))
def setup_channels(
    client: sy.Synnax, sim: Simulation, aliases: dict[str, str]
) -> tuple[list[str], list[str]]:
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

    for volume in sim.volumes.values():
        for ch_name in volume.channels:
            synnax_ch_name = resolve_alias(ch_name, aliases)
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
            write_channels.append(synnax_ch_name)

    for valve in sim.valves.values():
        synnax_ch_name = resolve_alias(valve.channel, aliases)
        client.channels.create(
            retrieve_if_name_exists=True,
            name=synnax_ch_name,
            data_type=sy.DataType.INT8,
            virtual=False,
            index=time_channel.key,
        )
        read_channels.append(synnax_ch_name)
        state_ch_name = synnax_ch_name.replace("vlv", "state")
        client.channels.create(
            retrieve_if_name_exists=True,
            name=state_ch_name,
            data_type=sy.DataType.INT8,
            virtual=False,
            index=time_channel.key,
        )
        write_channels.append(state_ch_name)

    return write_channels, read_channels


def main() -> None:
    args = parse_args()
    aliases = parse_aliases(args.aliases)
    simulation = Simulation(args.sim_params)
    client = synnax_login(args.cluster)
    write_channels, read_channels = setup_channels(client, simulation, aliases)

    with client.open_streamer(channels=read_channels) as streamer:
        with client.open_writer(
            start=sy.TimeStamp.now(), channels=write_channels
        ) as writer:
            driver(streamer, writer, simulation, aliases)


if __name__ == "__main__":
    spinner.stop()
    try:
        main()
    except KeyboardInterrupt:
        error_and_exit("Keyboard interrupt detected")
