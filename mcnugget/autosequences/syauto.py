import time
import synnax as sy
from synnax.control.controller import Controller
from typing import Union, Callable
import statistics

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
    commands = {}
    # Open valves to open
    for valve in valves:
        if valve.normally_open:
            commands[valve.cmd_chan] = 1
        else:
            commands[valve.cmd_chan] = 0
    auto.set(commands)


def open_all(auto: Controller, valves: list[Valve]):
    commands = {}
    for valve in valves:
        if valve.normally_open:
            commands[valve.cmd_chan] = 0
        else:
            commands[valve.cmd_chan] = 1

    auto.set(commands)


def pressurize(auto_: Controller, valve_s: Union[list[Valve], Valve], pressure_s: Union[list[str], str],
               target: float, max: float, inc: float, delay: float = 1):
    # This energizes the valve until the target pressure is reached.
    # valve_s can be either a single valve or a list.

    # if custom_auto is None:
    #     custom_auto = Controller

    if isinstance(valve_s, Valve):
        print(f"Pressurizing {valve_s.name} to {target}")
        valve_s = [valve_s]

    else:
        print("Pressurizing using these valves:")
        for v in valve_s:
            print(str(v.name))

    if isinstance(pressure_s, str):
        print(f"Reading from one pressure channel: {pressure_s}")
        pressure_s = [pressure_s]

    else:
        print("Reading from these pressure channels:")
        for p in pressure_s:
            print(p)

    # pressurizes the valve until the target pressure is reached
    partial_target = get_median_value(auto_, pressure_s) + inc
    while partial_target <= target:
        if (get_median_value(auto_, pressure_s) > max):
            return
        print(f"Pressurizing to {partial_target}")

        # Opens all valves since a single valve would already be converted to list of size 1
        open_all(auto_, valve_s)

        auto_.wait_until(
            lambda pressure: all(
                auto_[pressure] >= partial_target for pressure in pressure_s), delay
        )

        close_all(auto_, valve_s)

        time.sleep(delay)
        partial_target += inc

    print(f"Valve(s) have reached {target}")


def purge(valves: list[Valve], duration: float = 1):
    prev_time = time.time()
    for valve in valves:
        while (time.time() - prev_time < duration):
            open_all(valve.auto, valves)
            time.sleep(1)

#returns a list of medians
def compute_medians(auto_: Controller, channels: list[str], running_median_size: int = 100):
    # this function takes in a list of channel names and returns a list
    # where each channel name is replaced by its reading, averaged over RUNNING_MEDIAN_SIZE readings
    median_arrs = []
    for channel in channels:
        
        if len(median_arrs) > running_median_size:
            median_arrs.pop(0)
        median_arrs.append(statistics.median(auto_[channel]))

    return median_arrs

#returns a single median value
def get_median_value(auto_: Controller, channels: list[str]):
    return statistics.median(auto_[channel] for channel in channels)
