
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

class Bottle:
    name: str
    channels: list
    pressure: float
    temperature: float
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

    def __init__(self, name: str, normally_closed: bool):
        self.name = name
        self.normally_closed = normally_closed
        self.energized = False

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
    bottles = []
    config: Configuration

    def __init__(self, config: Configuration):
        self.config = config

        for valve in config.get_valves():
            self.valves.append(
                Valve(
                    name=valve,
                    normally_closed=True
                )
            )

        self.bottles = [
            Bottle(
                name="COPV",
                channels=[
                    config.mappings.COPV_PT_1,
                    config.mappings.COPV_PT_2,
                    config.mappings.Fuel_TPC_Inlet_PT
                ],
                volume=COPV_VOLUME,
                pressure=0
            ),
            Bottle(
                name="Bottle 1",
                channels=[config.mappings.Bottle_1_PT],
                volume=STD_BOTTLE_VOLUME,
                pressure=6000
            ),
            Bottle(
                name="Bottle 2",
                channels=[config.mappings.Bottle_2_PT],
                volume=STD_BOTTLE_VOLUME,
                pressure=6000
            ),
            Bottle(
                name="Bottle 3",
                channels=[config.mappings.Bottle_3_PT],
                volume=STD_BOTTLE_VOLUME,
                pressure=6000
            )
        ]

    def get_bottle_obj(self, name: str) -> Bottle | None:
        for bottle in self.bottles:
            if bottle.name.lower() == name.lower():
                return bottle
        return None

    def get_pressure(self, channel_name: str) -> float:
        channel_name = channel_name.lower()
        for bottle in self.bottles:
            for channel in bottle.channels:
                if channel_name == channel:
                    return bottle.pressure
        return 0.0 # for invalid or non-existant names

    def change_pressure(self, bottle_name: str, delta: float):
        bottle_name = bottle_name.lower()
        for bottle in self.bottles:
            if bottle.name.lower() == bottle_name:
                bottle.pressure += delta
                
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

    def transfer_fluid(self, source_name: str, dest_name: str):
        source = self.get_bottle_obj(source_name)
        dest = self.get_bottle_obj(dest_name)

        if not source or not dest:
            return

        p_diff = source.pressure - dest.pressure
        
        # If pressure is equal or negative (dest higher than source), no flow
        if p_diff <= 0:
            return

        PV_transfer = p_diff * FLOW_COEFFICIENT

        source_drop = PV_transfer / source.volume
        source.pressure -= source_drop
        dest_rise = PV_transfer / dest.volume
        dest.pressure += dest_rise


    def vent_to_atmosphere(self, source_name: str):
        source = self.get_bottle_obj(source_name)
        if not source: return

        p_diff = source.pressure - 0 
        if p_diff <= 0: return
        loss = p_diff * FLOW_COEFFICIENT
        source.pressure -= loss


    def update(self):
        if self.get_valve_state(self.config.mappings.COPV_Vent) == State.OPEN:
            self.vent_to_atmosphere("COPV")
            
        if self.get_valve_state(self.config.mappings.Press_Iso_1) == State.OPEN:
            self.transfer_fluid("Bottle 1", "COPV")

        if self.get_valve_state(self.config.mappings.Press_Iso_2) == State.OPEN:
            self.transfer_fluid("Bottle 2", "COPV")

        if self.get_valve_state(self.config.mappings.Press_Iso_3) == State.OPEN:
            self.transfer_fluid("Bottle 3", "COPV")