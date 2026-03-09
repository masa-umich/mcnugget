from enum import Enum, auto
from typing import Any, List, Dict
import yaml
from mclib.config import Config


class State(Enum):
    OPEN = auto()
    CLOSED = auto()


AMBIENT_TEMP: float = 22.0  # degrees celsius
STD_BOTTLE_VOLUME: float = 42.2  # Liters
COPV_VOLUME: float = 31.3  # Liters
GAMMA: float = 1.4  # Ratio of specific heats (1.4 for diatomic gases like N2/Air)
THERMAL_RELAXATION_RATE: float = 0.01  # How fast temp returns to ambient (0.0 to 1.0)


class Node:
    name: str
    channels: list
    pressure: float
    temperature: float
    volume: float

    def __init__(
        self,
        name: str,
        channels: list,
        volume: float,
        pressure: float,
        temperature: float = AMBIENT_TEMP,
    ):
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
        if self.normally_closed:  # Invert operation for NO valves
            self.state = State.OPEN
        else:
            self.state = State.CLOSED

    def de_energize(self) -> None:
        if self.normally_closed:
            self.state = State.CLOSED
        else:
            self.state = State.OPEN

    def toggle(self):
        if self.state == State.OPEN:
            self.de_energize()
        else:
            self.energize()

    def set_state(self, cmd: int):
        # 1 for open, 0 for closed
        if cmd == 1:
            self.energize()
        else:
            self.de_energize()


class System:
    valves: List[Valve] = []
    nodes: List[Node] = []
    config: Config

    def __init__(self, config: Config):
        self.config: Config = config
        self.valves = []
        self.nodes = []

        for valve_name in config.get_vlvs():
            normally_closed: bool = config.is_vlv_nc(valve_name)
            self.valves.append(
                Valve(valve_name, normally_closed, 0.02)
            )  # "default" valve

        # Manually set cv of some valves
        self.get_valve_obj(config.get_vlv("COPV_Vent")).cv = 0.01
        self.get_valve_obj(config.get_vlv("Press_Fill_Iso")).cv = 0.02
        self.get_valve_obj(config.get_vlv("Press_Fill_Vent")).cv = 0.01
        self.get_valve_obj(config.get_vlv("Ox_Fill_Valve")).cv = 0.0000001

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
                name="Bottle 4",
                channels=[
                    config.get_pt("Bottle_4_PT"),
                    config.get_tc("Bottle_4_Skin_TC"),
                ],
                volume=STD_BOTTLE_VOLUME,
                pressure=5600,
            ),
            Node(
                name="press_node",
                channels=[config.get_pt("Post_Press_Fill_PT")],
                volume=0.1,  # idk what a good value should be
                pressure=0,
            ),
            Node(
                name="Ox Dewar",
                channels=[],
                volume=999.0,
                pressure=300,
            ),
            Node(
                name="Ox Tank Level",
                channels=[config.get_pt("Ox_Level_Sensor")],
                volume=66.4,
                pressure=0,
            ),
            Node(
                name="Ox Tank",
                channels=[
                    config.get_pt("Ox_Tank_PT_1"),
                    config.get_pt("Ox_Tank_PT_2"),
                ],  # add
                volume=66.4,
                pressure=0,
            ),
            Node(
                name="Fuel Tank",
                channels=[],  # add
                volume=59.8,
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
        ox_fill_valve = self.get_valve_obj(self.config.get_vlv("Ox_Fill_Valve"))
        ox_vent = self.get_valve_obj(self.config.get_vlv("Ox_Vent"))
        ox_pre_press = self.get_valve_obj(self.config.get_vlv("Ox_Pre_Press"))
        press_iso_4 = self.get_valve_obj(self.config.get_vlv("Press_Iso_4"))

        if copv_vent.get_state() == State.OPEN:
            self.vent_to_atmosphere("COPV", copv_vent.cv)

        if press_iso_1.get_state() == State.OPEN:
            self.transfer_fluid("Bottle 1", "press_node", press_iso_1.cv)

        if press_iso_2.get_state() == State.OPEN:
            self.transfer_fluid("Bottle 2", "press_node", press_iso_2.cv)

        if press_iso_3.get_state() == State.OPEN:
            self.transfer_fluid("Bottle 3", "press_node", press_iso_3.cv)

        if press_iso_4.get_state() == State.OPEN:
            self.transfer_fluid("Bottle 4", "press_node", press_iso_4.cv)

        if press_fill_iso.get_state() == State.OPEN:
            self.transfer_fluid("press_node", "COPV", press_fill_iso.cv)

        if press_fill_vent.get_state() == State.OPEN:
            self.vent_to_atmosphere("press_node", press_fill_vent.cv)

        if ox_fill_valve.get_state() == State.OPEN:
            self.transfer_fluid("Ox Dewar", "Ox Tank Level", ox_fill_valve.cv)

        if ox_vent.get_state() == State.OPEN:
            self.vent_to_atmosphere("Ox Tank Level", ox_vent.cv)

        if ox_pre_press.get_state() == State.OPEN:
            self.transfer_fluid(
                "Bottle 1", "Ox Tank", ox_pre_press.cv
            )  # it does not come from bottle 1 but placeholder cuz idk

        self.vent_to_atmosphere("Ox Tank Level", 0.00005)  # Small leak to atmosphere
        self.vent_to_atmosphere("Ox Tank", 0.00005)  # Small leak to atmosphere
