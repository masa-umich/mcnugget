import synnax as sy

# this defines a class that can be used for both regular valves and vents
class Valve:
    def __init__(self, auto, name: str, cmd: str, ack: str, default_open: bool, 
                mawp: float, requires_confirm: bool = True):
        self.name = name
        self.cmd = cmd
        self.ack = ack
        self.default_open = default_open
        self.auto = auto
        self.requires_confirm = requires_confirm
        self.mawp = mawp

    # this energizes the valve until the target pressure is reached
    def pressurize(self, pressure: str, target: float, inc: float):
        partial_target = inc
        if self.requires_confirm:
            input(f"pressurizing {self.name} to {target} - press Enter to continue")
        while True:
            print(f"pressurizing {self.name} to {partial_target}")
            self.auto[self.cmd] = True
            self.auto.wait_until(lambda auto: auto[pressure] >= partial_target)
            if partial_target >= target:
                print(f"{self.name} has reached {target}")
                break
            partial_target += inc

    # closes a vent or opens a valve
    def energize(self):
        self.auto[self.cmd] = not self.default_open

    # opens a vent or closes a valve
    def de_energize(self):
        self.auto[self.cmd] = self.default_open

    # returns true iff the valve is below the MAWP
    def check_safe(self, pressure: str):
        return self.auto[pressure] < self.mawp


# this function initializes `auto` for the channels specified
def initialize_for_autosequence(cmds: [str], acks: [str], pressures: [str]):
    client = sy.Synnax(
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