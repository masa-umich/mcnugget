#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax==0.46.0",
#     "transitions",
#     "yaspin",
#     "colorama",
#     "termcolor"
# ]
# ///


from termcolor import colored
from yaspin import yaspin

#fun spinners are mandatory as per jack jammerberg
spinner = yaspin()
spinner.text = colored("Initializing...", "magenta")
spinner.start()


# import syauto 
import time
import synnax as sy
import statistics
import sys
import threading
from transitions.extensions import HierarchicalMachine as Machine
import colorama




"""
Channel indicies, need to account for different bbs
PAIR IS DEFINED AS (INDEX, BOARD)
0: EBOX
1: PRESS BAY BOARD
2: INTERTANK BAY BOARD
3: ENGINE BAY BOARD
"""

VALVE_INDICES = {
    #ebox
    "press_iso_1": (3,0),
    "press_iso_2": (4,0),
    "press_iso_3": (5,0),
    "press_fill_iso": (6,0),
    "press_fill_vent": (7,0),
    "ox_prepress": (8,0),
    "fuel_fill_purge": (11,0),
    "ox_mpv_purge": (12,0),
    "fuel_mpv_purge": (14,0),

    #press bay board
    "copv_vent": (1,1),
    "fuel_dome_iso": (2,1),
    "fuel_vent": (3,1),

    #intertank bay board
    "ox_dome_iso": (1,2),
    "ox_custom_vent": (2,2),

    #engine bay board
    "ox_mpv": (1,3),
    "fuel_mpv": (2,3),
}

PT_INDICES = {
    #Press bay board 
    "copv_1": (1,1),
    "copv_2": (2,1),

    "fuel_tank_1": (7,1),
    "fuel_tank_2": (8,1),

    #Intertank bay board
    "ox_ullage_1": (5,2),
    "ox_ullage_2": (6,2),
}

#make a way to take in indicies and output a channel

def red(text: str):
    return colorama.Fore.RED + text + colorama.Style.RESET_ALL

def green(text: str):
    return colorama.Fore.GREEN + text + colorama.Style.RESET_ALL

def yellow(text: str):
    return colorama.Fore.YELLOW + text + colorama.Style.RESET_ALL

def blue(text: str):
    return colorama.Fore.BLUE + text + colorama.Style.RESET_ALL

def magenta(text: str):
    return colorama.Fore.MAGENTA + text + colorama.Style.RESET_ALL

class Autosequence():
    states = ["init", "copv_press", "copv_press_check",
              "wait_countdown","done",
                {#countown nested state
                  "name": "countdown",
                  "children": ["cd_init", "qds", "qds_confirm",
                               "igniter", "igniter_confirm",
                               "handoff", "exit"],
                  "initial": "cd_init"
                }
    ]

    transitions = [
        {'trigger': 'copv_press_confirm', 'source': 'init', 'dest': 'copv_press'},
        {'trigger': 'copv_press_stage_complete', 'source': 'copv_press', 'dest': 'copv_press_check'},
        {'trigger': 'copv_press_continue', 'source': 'copv_press_check', 'dest': 'copv_press'},
        {'trigger': 'copv_press_complete', 'source': 'copv_press_check', 'dest': 'wait_countdown'},
        {'trigger': 'confirm_countdown', 'source': 'wait_countdown', 'dest': 'countdown'},
    ]
    
    def __init__(self):
        spinner.stop()
        machine = Machine(states = self.states, transitions = self.transitions, initial = 'init', auto_transitions=False)
        try:
            self.mode =  (input(colorama.Fore.BLUE + "Enter mode (sim/real): " + 
                                colorama.Fore.MAGENTA).strip().lower())
            if self.mode == "real":
                    spinner.start()
                    address = "141.212.192.160"
                    self.client = sy.Synnax(
                        host=address,
                        port=9090,
                        username="synnax",
                        password="seldon",
                        secure=False,
                    )
                    spinner.stop()
                    print(green("Connected to cluster at " + address))

            elif self.mode == "sim" or self.mode == "":
                self.mode = "sim"
                address = "172.22.240.1"
                self.client = sy.Synnax(
                    host=address,
                    port=9090,
                    username="synnax",
                    password="seldon",
                    secure=False,
                )
                print(green("Connected to cluster at " + address))
            
            else:
                print(red("erm... try again... that wasn't an option.  Restart the program boss."))
                exit()

        except KeyboardInterrupt:
            print(red("\nTerminating autosequence..."))
            sys.exit(0) # CHANGE THIS TO REAL SHUTDOWN

autosequence = Autosequence()