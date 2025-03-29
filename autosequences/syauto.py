from synnax.control.controller import Controller
import math
import time
import colorama

"""
syauto is a library intended to abstract away confusing parts of how we interface with the system.

Some brief background on valves, commands, and this library:
Valves are basically 'gates for pressure'. They can be open (allowing pressure to flow through) or closed.
Note that pressure always goes from the higher pressure to the lower pressure.

A valve can be 'normally open' or 'normally closed'. Usually we want this property to be 
    specified based on what the 'fail state' of the component is (whether we want it open/closed if things go wrong).
    Vents are generally 'normally open', so if we lose power, the system will automatically depressurize.
A valve can be 'energized' or 'deenergized'. 
    If a valve is deenergized, it is in its default state.
    If a valve is energized, it is in the opposite of its default state.
In Synnax, valves have a command channel and an acknowledgement channel. 
    The command channel is where we send commands to open or close, and the acknowledgement channel sends the 
    'state' of the system (from the source where we physically implement the commands we send).

Pulling this all together, suppose we have a valve with the following specifications:
    command channel 'valve_1_cmd'
    acknowledgement channel 'valve_1_ack'
    normally_open = false (it is not a vent)
If we want to open the valve, we need to send a command to energize the valve. We do this with
    `auto['valve_1_cmd'] = True`
Since `auto` is a controller which gives us access to the state of the Synnax cluster (and, by extension, the physical system),
sending this command results in energizing valve_1, after which we will receive a `1` or `True` value on the acknowledgement channel.

"""

class Valve:
    # this defines a class that can be used for both regular valves and vents
    def __init__(
            self,                               # python thing
            auto: Controller,                   # the controller this valve uses to talk with system
            cmd: str,                           # command channel name
            ack: str,                           # acknowledgement channel name
            normally_open: bool = False,        # whether the valve's default state is 'open'
            wait_for_ack: bool = False
    ):
        self.cmd_chan = cmd
        self.ack = ack
        self.normally_open = normally_open
        self.auto = auto
        self.wait_for_ack = wait_for_ack

    def open(self):
        # for reg. valve, normally_open is false so cmd is set to True
        # for vent valve, normally_open is true so cmd is set to False
        # sanity check ^
        self.auto[self.cmd_chan] = not self.normally_open
        if self.wait_for_ack:
            self.auto.wait_until(self.ack_chan != self.normally_open)

    def close(self):
        # for reg. valve, normally_open is false so cmd is set to False
        # for vent valve, normally_open is true so cmd is set to True
        # sanity check ^
        self.auto[self.cmd_chan] = self.normally_open
        if self.wait_for_ack:
            self.auto.wait_until(self.ack_chan == self.normally_open)

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

def wait(duration: float, increment: float = 1, offset: float = 0, precision: float = 0, message: str = None, color = None):
    """
    Prints the time remaining in the wait.
        - duration: how long to wait in seconds
        - increment: how long to wait between prints
        - offset: added to each print statement
        - precision: how many decimal points to print
        - message: printed at the end
    Will not print any increments less than `increment`
    """
    if color is not None:
        prestring = color
        poststring = colorama.Style.RESET_ALL
    else:
        prestring = ""
        poststring = ""
    while duration >= increment:
        print(prestring + f"{round(offset + duration, precision)}" + poststring)
        time.sleep(increment)
        duration -= increment
    if duration > 0:
        time.sleep(duration)
    if message is not None:
        print(message)


# functions that we don't use but could be used as ideas for future functionality:

# def purge(valves: list[Valve], duration: float = 1):
#     prev_time = time.time()
#     for valve in valves:
#         while (time.time() - prev_time < duration):
#             open_all(valve.auto, valves)
#             time.sleep(1)


# def compute_medians(auto_: Controller, channels: list[str], running_median_size: int = 100):
#     # this function takes in a list of channel names and returns a list
#     # where each channel name is replaced by its reading, averaged over RUNNING_MEDIAN_SIZE readings
#     median_arrs = []
#     for channel in channels:
        
#         if len(median_arrs) > running_median_size:
#             median_arrs.pop(0)
#         median_arrs.append(statistics.median(auto_[channel]))

#     return median_arrs
