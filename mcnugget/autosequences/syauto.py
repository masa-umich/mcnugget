import time
import sys
import synnax as sy
from synnax.control.controller import Controller
from typing import Union, Callable

import synnax.control.controller
print(synnax.control.controller.__file__)


class Valve:
    # this defines a class that can be used for both regular valves and vents
    def __init__(
            self,
            auto: Controller,
            cmd: str,
            name: str = "",
            ack: str = "",
            normally_open: bool = False,
            mawp: float = 0,
            wait_for_ack: bool = False
    ):
        self.name = name
        self.cmd_chan = cmd
        self.ack = ack
        self.normally_open = normally_open
        self.auto = auto
        self.wait_for_ack = wait_for_ack
        self.mawp = mawp

    def open(self):
        # for reg. valve, normally_open is false so cmd is set to True
        # for vent valve, normally_open is true so cmd is set to False
        self.auto[self.cmd_chan] = not self.normally_open
        if self.wait_for_ack:
            self.auto.wait_until(self.ack_chan != self.normally_open)

    def close(self):
        # for reg. valve, normally_open is false so cmd is set to False
        # for vent valve, normally_open is true so cmd is set to True
        self.auto[self.cmd_chan] = self.normally_open
        if self.wait_for_ack:
            self.auto.wait_until(self.ack_chan == self.normally_open)

    # returns true iff the valve is below the MAWP
    def check_safe(self, pressure: str):
        return self.auto[pressure] < self.mawp


class DualTescomValve:
    def __init__(
        self,
        auto: Controller,
        close_cmd_chan: str,
        open_cmd_chan: str,
        name: str = "",
        normally_open: bool = False,
        mawp: float = 0,
        wait_for_ack: bool = False,
        open_cmd_ack: str = "",
        close_cmd_ack: str = "",
    ):
        self.name = name
        self.normally_open = normally_open
        self.auto = auto
        self.wait_for_ack = wait_for_ack
        self.mawp = mawp
        self.open_cmd_chan = open_cmd_chan
        self.close_cmd_chan = close_cmd_chan
        self.open_cmd_ack = open_cmd_ack
        self.close_cmd_ack = close_cmd_ack

    # energizes the open_cmd_chan valve to open the valve
    def open(self):
        self.auto.set({
            self.close_cmd_chan: False,
            self.open_cmd_chan: True,
        })
        if self.wait_for_ack:
            self.auto.wait_until(self.open_cmd_ack)

    # energizes the close_cmd_chan valve to close the valve

    def close(self):
        self.auto.set({
            self.close_cmd_chan: True,
            self.open_cmd_chan: False,
        })
        if self.wait_for_ack:
            self.auto.wait_until(self.close_cmd_ack)


# def open_close_many_valves(auto: Controller, valves_to_close: list[Valve], valves_to_open: list[Valve]):
#     auto.set({
#         valve.cmd_chan: (not valve.normally_open) if valve in valves_to_close
#         else valve.normally_open
#         for valve in valves_to_open
#     })

def open_close_many_valves(auto: Controller, valves_to_open: list[Valve], valves_to_close: list[Valve]):
    commands = {}
    # Open valves to open
    for valve in valves_to_open:
        if valve.normally_open:
            commands[valve.cmd_chan] = 0
        else:
            commands[valve.cmd_chan] = 1
    # Close valves to close
    for valve in valves_to_close:
        if valve.normally_open:
            commands[valve.cmd_chan] = 1
        else:
            commands[valve.cmd_chan] = 0

    auto.set(commands)


def close_all(auto: Controller, valves: list[Valve]):
    auto.set({valve.cmd_chan: valve.normally_open for valve in valves})


def open_all(auto: Controller, valves: list[Valve]):
    auto.set({valve.cmd_chan: not valve.normally_open for valve in valves})


def pressurize(valve_s: Union[list[Valve], Valve], pressure_s: Union[list[str], str], target: float, inc: float, abort_function: Callable[[Controller], bool], delay: float = 1, custom_auto: Controller = None):
    # this energizes the valve until the target pressure is reached
    # valve_s can be either a single valve or a list

    # single valve
    if isinstance(valve_s, Valve):
        print(f"pressurizing {valve_s.name} to {partial_target}")
        # converts single valve to list with one valve so they are processed the same :o
        if not custom_auto:
            custom_auto = valve_s.auto
        valve_s = [valve_s]

    # list of valves
    else:
        print(f"pressurizing these valves to {partial_target}")
        for v in valve_s:
            print(v.name)
        # assigns custom_auto to auto from first valve by default
        if not custom_auto:
            custom_auto = valve_s[0].auto

    # single pressure channel
    if isinstance(valve_s, Valve):
        print(f"reading from one pressure channel, {pressure_s}")
        # converts single pressure to list with one channel so they are processed the same :ooo
        pressure_s = [pressure_s]

    # list of pressure channels
    else:
        print(f"reading from these pressure channels:")
        for p in pressure_s:
            print(p)

    partial_target = inc
    while True:
        if (abort_function(custom_auto)):
            print("ABORTING PRESSURIZATION due to abort function which was passed in")
            return
        open_all(valve_s)
        custom_auto.wait_until(
            lambda anakin_skywalker: anakin_skywalker[pressure] >= partial_target for pressure in pressure_s)
        close_all(valve_s)
        time.sleep(delay)
        if partial_target >= target:
            print(f"valve(s) have reached {target}")
            break
        partial_target += inc


def purge(valves: list[Valve], duration: float = 1):
    prev_time = time.time()
    for valve in valves:
        while (time.time() - prev_time < duration):
            open_all(valve.auto, valves)
            time.sleep(1)
