import time
from synnax import Synnax
from synnax.control.controller import Controller


# this defines a class that can be used for both regular valves and vents
class Valve:
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
        self.auto.wait_until(self.ack_chan != self.normally_open)


    def close(self):
        # for reg. valve, normally_open is false so cmd is set to False
        # for vent valve, normally_open is true so cmd is set to True
        self.auto[self.cmd_chan] = self.normally_open
        self.auto.wait_until(self.ack_chan == self.normally_open)

    # returns true iff the valve is below the MAWP
    def check_safe(self, pressure: str):
        return self.auto[pressure] < self.mawp

class DualTescomValve(Valve):
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
        super.__init__(self, auto, "multiple cmd channels", name, 
                       "multiple ack channels", normally_open, mawp, wait_for_ack)
        self.open_cmd_chan = open_cmd_chan
        self.close_cmd_chan = close_cmd_chan
        self.open_cmd_ack = open_cmd_ack
        self.close_cmd_ack = close_cmd_ack

    # energizes the open_cmd_chan valve to open the valve
    def open(self):
        self.auto[self.open_cmd_chan] = True
        if self.wait_for_ack:
            self.auto.wait_until(self.open_cmd_ack)


    # energizes the close_cmd_chan valve to close the valve
    def close(self):
        self.auto[self.close_cmd_chan] = True
        if self.wait_for_ack:
            self.auto.wait_until(self.close_cmd_ack)


def open_close_many_valves(auto: Controller, valves_to_close: [Valve], valves_to_open: [Valve]):
    dict1 = {valve.cmd_chan: not valve.normally_open for valve in valves_to_close}
    dict2 = {valve.cmd_chan: valve.normally_open for valve in valves_to_open}
    dict = dict1 + dict2
    auto.set({
        dict
    })

def open_close_many_valves(auto: Controller, valves_to_close: [Valve], valves_to_open: [Valve]):
    auto.set({
        valve.cmd_chan: (not valve.normally_open) if valve in valves_to_close 
        else valve.normally_open 
        for valve in valves_to_open
    })
    # trust


def close_all(auto: Controller, valves: list[Valve]):
    auto.set({valve.cmd_chan: valve.normally_open for valve in valves})


def open_all(auto: Controller, valves: list[Valve]):
    auto.set({valve.cmd_chan: not valve.normally_open for valve in valves})


# this energizes the valve until the target pressure is reached
def pressurize(valve: Valve, pressure: str, target: float, inc: float, delay: float = 0.5):
    partial_target = inc
    while True:
        print(f"pressurizing {valve.name} to {partial_target}")
        valve.open()
        valve.auto.wait_until(lambda auto: auto[pressure] >= partial_target)
        valve.close()
        time.sleep(delay)
        if partial_target >= target:
            print(f"{valve.name} has reached {target}")
            break
        partial_target += inc
