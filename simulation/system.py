
from enum import Enum, auto
from configuration import Configuration, ChannelMap
from dataclasses import fields

AMBIENT_TEMP: float = 26.0 # degrees celsius
FLOW_COEFFICIENT: float = 0.05 # Cv constant - in the real world this is different for each part of the system
STD_BOTTLE_VOLUME: float = 42.2 # Liters
COPV_VOLUME: float = 31.3 # Liters

class State(Enum):
    OPEN = auto()
    CLOSED = auto()

class Node:
    name: str
    channels: list
    pressure: float
    temperature: float
    cv: float
    volume: float

    def __init__(self, name: str, channels: list, volume: float, pressure: float):
        self.name = name
        self.channels = channels
        self.pressure = pressure
        self.temperature = AMBIENT_TEMP
        self.volume = volume

class Valve:
    name: str
    normally_closed: bool
    energized: bool
    cv: float

    def __init__(self, name: str, normally_closed: bool, cv: float):
        self.name = name
        self.normally_closed = normally_closed
        self.energized = False
        self.cv = cv

    def get_state(self):
        if (self.energized) and (self.normally_closed):
            return State.OPEN
        elif (self.energized) and not (self.normally_closed):
            return State.CLOSED
        elif not (self.energized) and (self.normally_closed):
            return State.CLOSED
        else:
            return State.OPEN

    def energize(self):
        self.energized = True

    def de_energize(self):
        self.energized = False

    def toggle(self):
        if (self.energized):
            self.de_energize()
        else:
            self.energize()

class System:
    valves = []
    nodes = []
    config: Configuration

    def __init__(self, config: Configuration):
        self.config = config

        for valve in config.get_valves():
            self.valves.append(
                Valve(
                    name=valve,
                    normally_closed=True,
                    cv=FLOW_COEFFICIENT
                )
            )

        # Manually set cv of some valves
        self.get_valve_obj(config.mappings.COPV_Vent).cv = 0.05
        self.get_valve_obj(config.mappings.Press_Fill_Iso).cv = 0.20
        self.get_valve_obj(config.mappings.Press_Fill_Vent).cv = 0.05

        self.nodes = [
            Node(
                name="COPV",
                channels=[
                    config.mappings.COPV_PT_1,
                    config.mappings.COPV_PT_2,
                    config.mappings.Fuel_TPC_Inlet_PT,
                    config.mappings.COPV_TC_1,
                    config.mappings.COPV_TC_2
                ],
                volume=COPV_VOLUME,
                pressure=0
            ),
            Node(
                name="Bottle 1",
                channels=[
                    config.mappings.Bottle_1_PT,
                    config.mappings.Bottle_1_Skin_TC
                ],
                volume=STD_BOTTLE_VOLUME,
                pressure=6000
            ),
            Node(
                name="Bottle 2",
                channels=[
                    config.mappings.Bottle_2_PT,
                    config.mappings.Bottle_2_Skin_TC
                ],
                volume=STD_BOTTLE_VOLUME,
                pressure=6000
            ),
            Node(
                name="Bottle 3",
                channels=[
                    config.mappings.Bottle_3_PT,
                    config.mappings.Bottle_3_Skin_TC
                ],
                volume=STD_BOTTLE_VOLUME,
                pressure=6000
            ),
            Node(
                name="press_node",
                channels=[None],
                volume=1, # idk what a good value should be
                pressure=0
            )
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
        return State.CLOSED # for invalid or non-existant names
    
    def toggle_valve(self, valve_name: str):
        valve_name = valve_name.lower()
        for valve in self.valves:
            if valve.name == valve_name.lower():
                return valve.toggle()

    def energize_valve(self, valve_name: str):
        valve_name = valve_name.lower()
        for valve in self.valves:
            if valve.name == valve_name.lower():
                valve.energize()
    
    def de_energize_valve(self, valve_name: str):
        valve_name = valve_name.lower()
        for valve in self.valves:
            if valve.name == valve_name.lower():
                valve.de_energize()

    def get_temperature(self, channel_name: str) -> float:
        channel_name = channel_name.lower()
        for node in self.nodes:
            for channel in node.channels:
                if channel_name == channel:
                    return node.temperature
        return 0.0 # for invalid or non-existant names        

    def get_pressure(self, channel_name: str) -> float:
        channel_name = channel_name.lower()
        for node in self.nodes:
            for channel in node.channels:
                if channel_name == channel:
                    return node.pressure
        return 0.0 # for invalid or non-existant names

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

        source_drop = PV_transfer / source.volume
        source.pressure -= source_drop
        dest_rise = PV_transfer / dest.volume
        dest.pressure += dest_rise


    def vent_to_atmosphere(self, source_name: str, cv: float):
        source = self.get_node_obj(source_name)
        if not source: return

        p_diff = source.pressure - 0 
        if p_diff <= 0: return
        loss = p_diff * cv
        source.pressure -= loss


    def update(self):
        press_fill_iso = self.get_valve_obj(self.config.mappings.Press_Fill_Iso)
        press_fill_vent = self.get_valve_obj(self.config.mappings.Press_Fill_Vent)
        copv_vent = self.get_valve_obj(self.config.mappings.COPV_Vent)
        press_iso_1 = self.get_valve_obj(self.config.mappings.Press_Iso_1)
        press_iso_2 = self.get_valve_obj(self.config.mappings.Press_Iso_2)
        press_iso_3 = self.get_valve_obj(self.config.mappings.Press_Iso_3)


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