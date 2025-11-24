
from enum import Enum, auto
from configuration import Configuration, ChannelMap
from dataclasses import fields

AMBIENT_TEMP: float = 26.0 # degrees celsius

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

    def __init__(self, config: Configuration):
        for valve in config.valves:
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
                    config.channels.COPV_PT_1,
                    config.channels.COPV_PT_2,
                    config.channels.Fuel_TPC_Inlet_PT
                ],
                volume=20,
                pressure=0
            ),
            Bottle(
                name="Bottle 1",
                channels=[config.channels.Bottle_1_PT],
                volume=20,
                pressure=6000
            ),
            Bottle(
                name="Bottle 2",
                channels=[config.channels.Bottle_2_PT],
                volume=20,
                pressure=6000
            ),
            Bottle(
                name="Bottle 3",
                channels=[config.channels.Bottle_3_PT],
                volume=20,
                pressure=6000
            )
        ]
            

    def get_pressure(self, channel_name: str) -> float:
        channel_name = channel_name.lower()
        for bottle in self.bottles:
            for channel in bottle.channels:
                if channel_name == channel:
                    return bottle.pressure
        return 0.0

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

    def update(self, config: Configuration):
        COPV_Vent_State: State = self.get_valve_state(config.channels.COPV_Vent)
        if COPV_Vent_State == State.OPEN:
            rate = 20
            pressure = self.get_pressure(config.channels.COPV_PT_1)
            if (pressure >= rate):
                amount = rate
            else:
                amount = pressure
            self.change_pressure("COPV", -amount)
            
        Press_Iso_1_State: State = self.get_valve_state(config.channels.Press_Iso_1)
        if Press_Iso_1_State == State.OPEN:
            rate = 1
            bottle_pressure = self.get_pressure(config.channels.Bottle_1_PT)
            if (bottle_pressure >= rate):
                amount = rate
            else:
                amount = bottle_pressure
            self.change_pressure("Bottle 1", -amount)
            self.change_pressure("COPV", amount)


        Press_Iso_2_State: State = self.get_valve_state(config.channels.Press_Iso_2)
        if Press_Iso_2_State == State.OPEN:
            rate = 1
            bottle_pressure = self.get_pressure(config.channels.Bottle_2_PT)
            if (bottle_pressure >= rate):
                amount = rate
            else:
                amount = bottle_pressure
            self.change_pressure("Bottle 2", -amount)
            self.change_pressure("COPV", amount)

        Press_Iso_3_State: State = self.get_valve_state(config.channels.Press_Iso_3)
        if Press_Iso_3_State == State.OPEN:
            rate = 1
            bottle_pressure = self.get_pressure(config.channels.Bottle_3_PT)
            if (bottle_pressure >= rate):
                amount = rate
            else:
                amount = bottle_pressure
            self.change_pressure("Bottle 3", -amount)
            self.change_pressure("COPV", amount)