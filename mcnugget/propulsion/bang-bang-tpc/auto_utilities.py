from synnax import Synnax, Controller
import time

# this defines a class that can be used for both regular valves and vents
class Valve:
    def __init__(self, auto: Controller, name: str, cmd: str, ack: str, normally_open: bool, 
                mawp: float, wait_for_ack: bool = True):
        self.name = name
        self.cmd_chan = cmd
        self.ack_chan = ack
        self.normally_open = normally_open
        self.auto = auto
        self.wait_for_ack = wait_for_ack
        self.mawp = mawp

    # energizes valve, de-energizes vent
    def open(self):
        # for reg. valve, normally_open is false so cmd is set to True
        # for vent valve, normally_open is true so cmd is set to False
        self.auto[self.cmd_chan] = not self.normally_open
        self.auto.wait_until(self.ack_chan != self.normally_open)

    # de-energizes valve, energizes vent
    def close(self):
        # for reg. valve, normally_open is false so cmd is set to False
        # for vent valve, normally_open is true so cmd is set to True
        self.auto[self.cmd_chan] = self.normally_open
        self.auto.wait_until(self.ack_chan == self.normally_open)

    # returns true iff the valve is below the MAWP
    def check_safe(self, pressure: str):
        return self.auto[pressure] < self.mawp

# this energizes the valve until the target pressure is reached
def pressurize(self, valve: Valve, pressure: str, target: float, inc: float, delay: float = 1):
    partial_target = inc
    if self.requires_confirm:
        input(f"pressurizing {self.name} to {target} - press Enter to continue")
    while True:
        print(f"pressurizing {self.name} to {partial_target}")
        valve.open()
        self.auto.wait_until(lambda auto: auto[pressure] >= partial_target)
        valve.close()
        time.sleep(delay)
        if partial_target >= target:
            print(f"{self.name} has reached {target}")
            break
        partial_target += inc