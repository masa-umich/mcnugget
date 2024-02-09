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
            requires_confirm: bool = False
    ):
        self.name = name
        self.cmd_chan = cmd
        self.ack = ack
        self.normally_open = normally_open
        self.auto = auto
        self.requires_confirm = requires_confirm
        self.mawp = mawp

    # this energizes the valve until the target pressure is reached
    def pressurize(self, pressure: str, target: float, inc: float, delay: float = 0.5):
        partial_target = inc
        if self.requires_confirm:
            input(f"pressurizing {self.name} to {target} - press Enter to continue")
        while True:
            print(f"pressurizing {self.name} to {partial_target}")
            self.open()
            self.auto.wait_until(lambda auto: auto[pressure] >= partial_target)
            self.close()
            time.sleep(delay)
            if partial_target >= target:
                print(f"{self.name} has reached {target}")
                break
            partial_target += inc

    # closes a vent or opens a valve
    def open(self):
        self.auto[self.cmd_chan] = not self.normally_open

    # opens a vent or closes a valve
    def close(self):
        self.auto[self.cmd_chan] = self.normally_open

    # returns true iff the valve is below the MAWP
    def check_safe(self, pressure: str):
        return self.auto[pressure] < self.mawp


# this function initializes `auto` for the channels specified
def initialize_for_autosequence(cmds: [str], acks: [str], pressures: [str]):
    client = Synnax(
        host="localhost",
        port=9090,
        username="synnax",
        password="seldon",
        secure=False
    )
    return client.control.acquire(
        "bang_bang_tpc",
        write=[
            cmd for cmd in cmds
        ],
        read=[
            ack_or_press for ack_or_press in acks + pressures
        ],
        write_authorities=[255]
    )


def close_all(auto: Controller, valves: list[Valve]):
    auto.set({valve.cmd_chan: valve.normally_open for valve in valves})


def open_all(auto: Controller, valves: list[Valve]):
    auto.set({valve.cmd_chan: not valve.normally_open for valve in valves})
