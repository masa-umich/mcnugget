from enum import Enum, auto
from typing import Any
import yaml


class Config:
    """
    Parses a config.yaml file for channel mappings and autosequence variables.
    Use get_var(name) or get_vlv(name) to get objects from the config file
    Also checks that the requested field exists, throws an error if it doesn't
    """

    _yaml_data: dict

    vars: dict[str, Any]
    vlvs: dict[str, str]
    pts: dict[str, str]
    tcs: dict[str, str]

    def __init__(self, filepath: str):
        self.vlvs: dict[str, str] = {}
        self.normally_open_vlvs: dict[str, bool] = {}
        self.pts: dict[str, str] = {}
        self.tcs: dict[str, str] = {}
        self.vars: dict[str, Any] = {}

        prefix_map: dict[str, str] = {
            "ebox": "gse",
            "flight_computer": "fc",
            "bay_board_1": "bb1",
            "bay_board_2": "bb2",
            "bay_board_3": "bb3",
        }

        type_suffix_map: dict[str, str] = {"pts": "pt", "valves": "vlv", "tcs": "tc"}

        with open(filepath, "r") as f:
            self._yaml_data: dict = yaml.safe_load(f)

        self.vars: dict[str, Any] = self._yaml_data.get("variables", {})
        mappings_data: dict[Any, Any] = self._yaml_data.get("channel_mappings", {})

        for controller_key, prefix in prefix_map.items():
            controller_data = mappings_data.get(controller_key)
            if not controller_data:
                continue

            for type_key, suffix in type_suffix_map.items():
                items = controller_data.get(type_key)
                if not items:
                    continue  # Skip if this controller doesn't have TCs (e.g. Flight Computer)

                for config_ch_name, value in items.items():
                    # Construct Synnax Name: prefix_suffix_index (e.g., gse_pt_1)
                    ch_index = value
                    is_normally_open = False # Default assumption

                    # If the entry has extra information
                    if isinstance(value, dict):
                        ch_index = value.get("id")
                        # We use .get(key, default) so it still works if 'normally_open' is omitted
                        is_normally_open = value.get("normally_open", False)
                    
                    # Construct Synnax Name
                    synnax_name = f"{prefix}_{suffix}_{ch_index}"
                    real_name: str = config_ch_name.lower()

                    if suffix == "pt":
                        self.pts[real_name] = synnax_name
                    elif suffix == "tc":
                        self.tcs[real_name] = synnax_name
                    elif suffix == "vlv":
                        self.vlvs[real_name] = synnax_name
                        self.normally_open_vlvs[real_name] = is_normally_open
                        self.normally_open_vlvs[synnax_name] = is_normally_open # Also map by synnax name for convenience
                    else:
                        raise Exception("Bad entry in mappings part of config")

    def get_var(self, name: str) -> Any:
        var: Any | None = self.vars.get(name.lower())
        if var is not None:
            return var
        else:
            raise Exception(f"Could not find variable with name: '{name}' in config")

    def get_vlv(self, name: str) -> str:
        vlv: str | None = self.vlvs.get(name.lower())
        if vlv is not None:
            return vlv
        else:
            raise Exception(f"Could not find valve with name: '{name}' in config")

    def is_vlv_nc(self, name: str) -> bool:
        nc: bool | None = self.normally_open_vlvs.get(name.lower())
        if nc is not None:
            return not nc
        else:
            raise Exception(f"Could not find valve with name: '{name}' in config")

    def get_state(self, name: str) -> str:
        vlv: str | None = self.vlvs.get(name.lower())
        if vlv is not None:
            return vlv.replace("vlv", "state")
        else:
            raise Exception(f"Could not find valve with name: '{name}' in config")

    def get_pt(self, name: str) -> str:
        pt: str | None = self.pts.get(name.lower())
        if pt is not None:
            return pt
        else:
            raise Exception(f"Could not find pt with name: '{name}' in config")

    def get_tc(self, name: str) -> str:
        tc: str | None = self.tcs.get(name.lower())
        if tc is not None:
            return tc
        else:
            raise Exception(f"Could not find tc with name: '{name}' in config")

    def get_vlvs(self) -> list[str]:
        all_vlvs: list[str] = []
        for vlv in self.vlvs.values():
            all_vlvs.append(vlv)
        return all_vlvs

    def get_states(self) -> list[str]:
        all_states: list[str] = []
        for vlv in self.vlvs.values():
            all_states.append(vlv.replace("vlv", "state"))
        return all_states

    def get_pts(self) -> list[str]:
        all_pts: list[str] = []
        for pt in self.pts.values():
            all_pts.append(pt)
        return all_pts
    
    def get_tcs(self) -> list[str]:
        all_tcs: list[str] = []
        for tc in self.tcs.values():
            all_tcs.append(tc)
        return all_tcs

    def get_sensors(self) -> list[str]:
        all_sensors: list[str] = []
        for pt in self.pts.values():
            all_sensors.append(pt)
        for tc in self.tcs.values():
            all_sensors.append(tc)
        return all_sensors


AMBIENT_TEMP: float = 22.0  # degrees celsius
STD_BOTTLE_VOLUME: float = 42.2  # Liters
COPV_VOLUME: float = 31.3  # Liters
GAMMA: float = 1.4  # Ratio of specific heats (1.4 for diatomic gases like N2/Air)
THERMAL_RELAXATION_RATE: float = 0.01  # How fast temp returns to ambient (0.0 to 1.0)


class State(Enum):
    OPEN = auto()
    CLOSED = auto()


class Node:
    name: str
    channels: list
    pressure: float
    temperature: float
    volume: float

    def __init__(self, name: str, channels: list, volume: float, pressure: float, temperature: float = AMBIENT_TEMP):
        self.name = name
        self.channels = channels
        self.pressure = pressure
        self.temperature = AMBIENT_TEMP
        self.volume = volume
        self.temperature = temperature

    def thermal_relax(self):
        diff = AMBIENT_TEMP - self.temperature
        self.temperature += diff * THERMAL_RELAXATION_RATE


class Valve:
    name: str
    normally_closed: bool
    state: State
    cv: float

    def __init__(self, name: str, normally_closed: bool, cv: float):
        if normally_closed == True:
            self.state = State.CLOSED
        else:
            self.state = State.OPEN
        self.name = name
        self.normally_closed = normally_closed
        self.cv = cv

    def get_state(self) -> State:
        return self.state
    
    def energize(self) -> None:
        if self.normally_closed:
            self.state = State.OPEN
        else:
            self.state = State.CLOSED

    def de_energize(self) -> None:
        if self.normally_closed:
            self.state = State.CLOSED
        else:
            self.state = State.OPEN


class System:
    valves = []
    nodes = []
    config: Config

    def __init__(self, config: Config):
        self.config: Config = config

        for valve in config.get_vlvs():
            normally_closed: bool = config.is_vlv_nc(valve)
            self.valves.append(Valve(valve, normally_closed, 0.01))  # "default" valve

        # Manually set cv of some valves
        self.get_valve_obj(config.get_vlv("COPV_Vent")).cv = 0.01
        self.get_valve_obj(config.get_vlv("Press_Fill_Iso")).cv = 0.01
        self.get_valve_obj(config.get_vlv("Press_Fill_Vent")).cv = 0.01

        self.nodes = [
            Node(
                name="COPV",
                channels=[
                    config.get_pt("COPV_PT_1"),
                    config.get_pt("COPV_PT_2"),
                    config.get_pt("Fuel_TPC_Inlet_PT"),
                    config.get_tc("COPV_TC_1"),
                    config.get_tc("COPV_TC_2"),
                ],
                volume=COPV_VOLUME,
                pressure=0,
            ),
            Node(
                name="Bottle 1",
                channels=[
                    config.get_pt("Bottle_1_PT"),
                    config.get_tc("Bottle_1_Skin_TC"),
                ],
                volume=STD_BOTTLE_VOLUME,
                pressure=5600,
            ),
            Node(
                name="Bottle 2",
                channels=[
                    config.get_pt("Bottle_2_PT"),
                    config.get_tc("Bottle_2_Skin_TC"),
                ],
                volume=STD_BOTTLE_VOLUME,
                pressure=5600,
            ),
            Node(
                name="Bottle 3",
                channels=[
                    config.get_pt("Bottle_3_PT"),
                    config.get_tc("Bottle_3_Skin_TC"),
                ],
                volume=STD_BOTTLE_VOLUME,
                pressure=5600,
            ),
            Node(
                name="press_node",
                channels=[config.get_pt("Post_Press_Fill_PT")],
                volume=0.01,  # idk what a good value should be
                pressure=0,
            ),
        ]

    def get_valve_obj(self, name: str) -> Valve:
        for valve in self.valves:
            if valve.name.lower() == name.lower():
                return valve
        raise Exception(f"Couldn't find valve {name}")

    def get_node_obj(self, name: str) -> Node:
        for node in self.nodes:
            if node.name.lower() == name.lower():
                return node
        raise Exception(f"Couldn't find node {name}")

    def get_valve_state(self, valve_name: str) -> State:
        valve_name = valve_name.lower()
        for valve in self.valves:
            if valve.name.lower() == valve_name:
                return valve.get_state()
        return State.CLOSED  # for invalid or non-existant names

    def toggle_valve(self, valve_name: str):
        valve_name = valve_name.lower()
        for valve in self.valves:
            if valve.name == valve_name.lower():
                return valve.toggle()
    
    def set_valve(self, valve_name: str, cmd: int):
        valve_name = valve_name.lower()
        for valve in self.valves:
            if valve.name == valve_name.lower():
                valve.set_state(cmd)

    def get_temperature(self, channel_name: str) -> float:
        channel_name = channel_name.lower()
        for node in self.nodes:
            for channel in node.channels:
                if channel_name == channel:
                    return node.temperature
        return 0.0  # for invalid or non-existant names

    def get_pressure(self, channel_name: str) -> float:
        channel_name = channel_name.lower()
        for node in self.nodes:
            for channel in node.channels:
                if channel_name == channel:
                    return node.pressure
        return 0.0  # for invalid or non-existant names

    def _apply_adiabatic_temp_change(
        self, node: Node, old_pressure: float, new_pressure: float
    ):
        # T2 = T1 * (P2 / P1) ^ ((gamma - 1) / gamma)

        if old_pressure <= 0.1 or new_pressure <= 0.1:
            return  # Avoid division by zero or vacuum math issues

        pressure_ratio = new_pressure / old_pressure
        exponent = (GAMMA - 1) / GAMMA

        # Calculate new temp
        node.temperature = node.temperature * (pressure_ratio**exponent)

    def transfer_fluid(self, source_name: str, dest_name: str, cv: float):
        source = self.get_node_obj(source_name)
        dest = self.get_node_obj(dest_name)

        if not source or not dest:
            return

        p_diff = source.pressure - dest.pressure

        # If pressure is equal or negative (dest higher than source), no flow
        if p_diff <= 0:
            return

        PV_transfer = p_diff * cv

        src_p_old = source.pressure
        dest_p_old = dest.pressure

        source_drop = PV_transfer / source.volume
        source.pressure -= source_drop
        dest_rise = PV_transfer / dest.volume
        dest.pressure += dest_rise

        # self._apply_adiabatic_temp_change(source, src_p_old, source.pressure)
        # self._apply_adiabatic_temp_change(dest, dest_p_old, dest.pressure)

    def vent_to_atmosphere(self, source_name: str, cv: float):
        source = self.get_node_obj(source_name)
        if not source:
            return

        p_diff = source.pressure - 0
        if p_diff <= 0:
            return
        loss = p_diff * cv

        src_p_old = source.pressure

        source.pressure -= loss

        # self._apply_adiabatic_temp_change(source, src_p_old, source.pressure)

    def update(self):
        # for node in self.nodes:
        #     node.thermal_relax()

        press_fill_iso = self.get_valve_obj(self.config.get_vlv("Press_Fill_Iso"))
        press_fill_vent = self.get_valve_obj(self.config.get_vlv("Press_Fill_Vent"))
        copv_vent = self.get_valve_obj(self.config.get_vlv("COPV_Vent"))
        press_iso_1 = self.get_valve_obj(self.config.get_vlv("Press_Iso_1"))
        press_iso_2 = self.get_valve_obj(self.config.get_vlv("Press_Iso_2"))
        press_iso_3 = self.get_valve_obj(self.config.get_vlv("Press_Iso_3"))

        if copv_vent.get_state() == State.OPEN:
            self.vent_to_atmosphere("COPV", copv_vent.cv)

        if press_iso_1.get_state() == State.OPEN:
            self.transfer_fluid("Bottle 1", "press_node", press_iso_1.cv)

        if press_iso_2.get_state() == State.OPEN:
            self.transfer_fluid("Bottle 2", "press_node", press_iso_2.cv)

        if press_iso_3.get_state() == State.OPEN:
            self.transfer_fluid("Bottle 3", "press_node", press_iso_3.cv)

        if press_fill_iso.get_state() == State.OPEN:
            self.transfer_fluid("press_node", "COPV", press_fill_iso.cv)

        if press_fill_vent.get_state() == State.OPEN:
            self.vent_to_atmosphere("press_node", press_fill_vent.cv)
