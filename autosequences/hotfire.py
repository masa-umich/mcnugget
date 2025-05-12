import syauto
import time
import synnax
import statistics
import sys
import threading
import colorama

"""
Only change things declared in ALL_CAPS. All test parameters are referenced from here.
"""

# firing sequence
FIRST_MPV = "fuel"  # set as either "ox" or "fuel"
OX_MPV_TIME = 0
FUEL_MPV_TIME = 1
MPV_DELAY = 0
BURN_DURATION = 5
PURGE_DURATION = 7

# All of these delays should be in seconds backwards from T=0
IGNITER_LEAD = 6
END_PREPRESS_LEAD = 3

# ox
OX_PREPRESS_TARGET = 332  # 327 - 337
OX_PREPRESS_MARGIN = 5  # +/- from the target
OX_PREPRESS_ABORT_PRESSURE = 700

# fuel
FUEL_PREPRESS_TARGET = 570  # 565 - 570
FUEL_PREPRESS_MARGIN = 5  # +/- from the target
FUEL_PREPRESS_ABORT_PRESSURE = 700

# leave these
FUEL_DOME_LEAD = FUEL_MPV_TIME  # T-1
RETURN_LINE_LEAD = OX_MPV_TIME + 1  # T-1
OX_DOME_LEAD = OX_MPV_TIME + 2      # T-2
FIRST_MPV_LEAD = max(FUEL_MPV_TIME, OX_MPV_TIME) - min(FUEL_MPV_TIME, OX_MPV_TIME) + MPV_DELAY   # T-1 FUEL_MPV

# channels - confirm ICD is up to date and check against the ICD
VALVE_INDICES = {
    "ox_dome_iso": 22,
    "ox_mpv": 19,
    "ox_prevalve": 3,
    "ox_vent": 23,

    "fuel_mpv": 12,
    "fuel_prevalve": 17,
    "fuel_dome_iso": 21,
    "fuel_vent": 24,
    "fuel_prepress": 6,

    "press_iso": 20,
    "igniter": 18,
    "mpv_purge": 8,
    "ox_return_line": 1,
}

PT_INDICES = {
    "ox_tank_1": 39,
    "ox_tank_2": 40,
    "ox_tank_3": 41,

    "fuel_tank_1": 19,
    "fuel_tank_2": 20,
    "fuel_tank_3": 21,
}

NORMALLY_OPEN_VALVES = [
    "ox_mpv",
    "fuel_mpv",
    "ox_vent",
    "fuel_vent",
]

def PT(channel: str | int) -> str:
    if type(channel) == str:
        return f"gse_pt_{PT_INDICES[channel]}_avg"
    return f"gse_pt_{str(channel)}_avg"

def VALVE(channel: str | int) -> str:
    if type(channel) == str:
        return f"gse_vlv_{VALVE_INDICES[channel]}"
    return f"gse_vlv_{str(channel)}"


def STATE(channel: str | int) -> str:
    if type(channel) == str:
        return f"gse_state_{VALVE_INDICES[channel]}"
    return f"gse_state_{str(channel)}"

"""
Change things below this comment at your own risk.
"""

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
    def __init__(self):
        """
        The following block runs on initialization, and handles the cluster connection
        and initialization of Valve objects. All actual behavior is handled by other functions.
        """
        try:
            self.mode = input(colorama.Fore.BLUE + "Enter mode (coldflow/hotfire/sim/real): " + colorama.Fore.MAGENTA).strip().lower()
            if self.mode == "coldflow" or self.mode == "hotfire" or self.mode == "real":
                address = "141.212.192.160"
                # address = "35.3.164.151"
                self.client = synnax.Synnax(
                    host=address,
                    port=9090,
                    username="synnax",
                    password="seldon",
                    secure=False,
                )
                print(green("Connected to cluster at " + address))

            elif self.mode == "sim" or self.mode == "":
                self.mode = "sim"
                address = "localhost"
                self.client = synnax.Synnax(
                    host=address,
                    port=9090,
                    username="synnax",
                    password="seldon",
                    secure=False,
                )
                print(green("Connected to cluster at " + address))

            else:
                print(red("Bestie what are you trying to do? If it's a typo, just try again, we're gonna close to program for now though <3"))
                # courtesy of ramona ^
                exit()

            if len(sys.argv) == 1:
                self._using_ox = True
                self._using_fuel = True
            elif len(sys.argv) == 2:
                self._using_ox = sys.argv[1].lower() == "ox"
                self._using_fuel = sys.argv[1].lower() == "fuel"

            if self._using_fuel:
                print(green("USING FUEL"))
            else:
                print(red("NOT USING FUEL"))
            if self._using_ox:
                print(green("USING OX"))
            else:
                print(red("NOT USING OX"))

            if FIRST_MPV == "ox":
                print(green("FIRST MPV: OX"))
            elif FIRST_MPV == "fuel":
                print(green("FIRST MPV: FUEL"))

            self.read_channels = []
            self.write_channels = []
            for channel in VALVE_INDICES.values():
                self.read_channels.append(STATE(channel))
                self.write_channels.append(VALVE(channel))
            for channel in PT_INDICES.values():
                self.read_channels.append(PT(channel))

            self.controller = self.client.control.acquire("Hotfire Autosequence", self.read_channels, self.write_channels, 232)
        
        except KeyboardInterrupt:
            print(red("\nTerminating autosequence..."))
            self.shutdown()

    def initialize(self) -> bool:
        """
        This function exists to make sure things aren't messed up.
            - no negative wait times
            - no invalid channels
            - confirm test specs
            - checks starting state
        Also sets up the Autosequence to run with the specified Controller
        """
        print(yellow("Initializing..."))
        print(yellow("Checking for negative wait times..."))
        self.times = [
            ("igniter_open", IGNITER_LEAD),
            ("igniter_close", IGNITER_LEAD - 1),
            ("end_prepress", END_PREPRESS_LEAD),
            ("ox_dome", OX_DOME_LEAD),
            ("fuel_dome", FUEL_DOME_LEAD),
            ("return_line", RETURN_LINE_LEAD),
            ("first_mpv", FIRST_MPV_LEAD),
            ("second_mpv", 0),
            ("start_ignition_detection", IGNITER_LEAD - 0.01),
            ("check_ignition_detection", max(OX_DOME_LEAD, FUEL_DOME_LEAD)),
        ]
        self.times = list(reversed(sorted(self.times, key=lambda x: x[1])))
        self.firing_sequence = []
        # calculate order + delays for events, sum should be 10 seconds
        for i, (cmd, t_minus) in enumerate(self.times):
            if i == 0:
                self.firing_sequence.append((cmd, 10 - t_minus, t_minus))
            else:
                self.firing_sequence.append((cmd, self.times[i-1][1] - t_minus, t_minus))
        
        # print(f"TIMES: {self.times}")
        # print(f"FIRING SEQUENCE: {self.firing_sequence}")

        sequence_time = sum(event[1] for event in self.firing_sequence)
        # print(f"Total time for firing sequence is {sequence_time} seconds")
        if not (abs(sequence_time - 10) < 0.0001):
            print(red(f"ERROR: Firing sequence should be 10 seconds total, not {sequence_time} seconds"))
            exit(1)

        print(yellow("Checking valves..."))
        self.ox_dome_iso = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("ox_dome_iso"),
            state=STATE("ox_dome_iso"),
            normally_open="ox_dome_iso" in NORMALLY_OPEN_VALVES,
        )
        self.ox_mpv = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("ox_mpv"),
            state=STATE("ox_mpv"),
            normally_open="ox_mpv" in NORMALLY_OPEN_VALVES,
        )
        self.ox_prevalve = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("ox_prevalve"),
            state=STATE("ox_prevalve"),
            normally_open="ox_prevalve" in NORMALLY_OPEN_VALVES,
        )
        self.ox_vent = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("ox_vent"),
            state=STATE("ox_vent"),
            normally_open="ox_vent" in NORMALLY_OPEN_VALVES,
        )

        self.fuel_mpv = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("fuel_mpv"),
            state=STATE("fuel_mpv"),
            normally_open="fuel_mpv" in NORMALLY_OPEN_VALVES,
        )
        self.fuel_prevalve = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("fuel_prevalve"),
            state=STATE("fuel_prevalve"),
            normally_open="fuel_prevalve" in NORMALLY_OPEN_VALVES,
        )
        self.fuel_dome_iso = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("fuel_dome_iso"),
            state=STATE("fuel_dome_iso"),
            normally_open="fuel_dome_iso" in NORMALLY_OPEN_VALVES,
        )
        self.fuel_vent = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("fuel_vent"),
            state=STATE("fuel_vent"),
            normally_open="fuel_vent" in NORMALLY_OPEN_VALVES,
        )
        self.fuel_prepress = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("fuel_prepress"),
            state=STATE("fuel_prepress"),
            normally_open="fuel_prepress" in NORMALLY_OPEN_VALVES,
        )

        self.press_iso = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("press_iso"),
            state=STATE("press_iso"),
            normally_open="press_iso" in NORMALLY_OPEN_VALVES,
        )
        self.igniter = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("igniter"),
            state=STATE("igniter"),
            normally_open="igniter" in NORMALLY_OPEN_VALVES,
        )
        self.mpv_purge = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("mpv_purge"),
            state=STATE("mpv_purge"),
            normally_open="mpv_purge" in NORMALLY_OPEN_VALVES,
        )
        self.ox_return_line = syauto.Valve(
            auto=self.controller,
            cmd=VALVE("ox_return_line"),
            state=STATE("ox_return_line"),
            normally_open="ox_return_line" in NORMALLY_OPEN_VALVES,
        )

        if FIRST_MPV == "ox":
            self.first_mpv = self.ox_mpv
            self.second_mpv = self.fuel_mpv
        elif FIRST_MPV == "fuel":
            self.first_mpv = self.fuel_mpv
            self.second_mpv = self.ox_mpv
        else:
            print(red(f"ERROR: FIRST_MPV must be either 'ox' or 'fuel', not {FIRST_MPV}"))

        valves = [
            self.ox_dome_iso,
            self.ox_mpv,
            self.ox_prevalve,
            self.ox_vent,
            self.fuel_mpv,
            self.fuel_prevalve,
            self.fuel_dome_iso,
            self.fuel_vent,
            self.fuel_prepress,
            self.press_iso,
            self.igniter,
            self.mpv_purge,
        ]
        if len([valve for valve in valves if valve.normally_open]) != len(NORMALLY_OPEN_VALVES):
            print(red("ERROR: Unable to find some normally open valves, please fix."))
            exit(1)
        
        print(yellow("Checking for invalid channels..."))
        for channel in self.read_channels + self.write_channels:
            try:
                self.client.channels.retrieve(channel)
            except synnax.exceptions.NotFoundError:
                print(red(f"ERROR: Unable to find channel {channel}"))
                exit(1)

        time.sleep(0.25)  # for controller to wake up
        print(yellow("Checking starting state..."))
        # check valves which should be open
        if self.controller[STATE("ox_prevalve")] == 0:
            input(f"{red('Ox prevalve')} {yellow('is not open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("fuel_prevalve")] == 0:
            input(f"{red('Fuel prevalve')} {yellow('is not open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("press_iso")] == 0:
            input(f"{red('Press Iso')} {yellow('is not open, press enter to manually override or ctrl-c to stop.')}")

        # check valves which should be closed
        if self.controller[STATE("ox_mpv")] == 0: # normally open
            input(f"{red('Ox MPV')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("fuel_mpv")] == 0: # normally open
            input(f"{red('Fuel MPV')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("ox_dome_iso")] == 1:
            input(f"{red('Ox Dome Iso')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("fuel_dome_iso")] == 1:
            input(f"{red('Fuel Dome Iso')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("ox_vent")] == 0: # normally open
            input(f"{red('Ox vent')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("fuel_vent")] == 0: # normally open
            input(f"{red('Fuel vent')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("fuel_prepress")] == 1:
            input(f"{red('Fuel prepress')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("mpv_purge")] == 1:
            input(f"{red('MPV purge')} {yellow('is open, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("ox_return_line")] == 0:
            input(f"{red('Ox return line')} {yellow('is closed, press enter to manually override or ctrl-c to stop.')}")
        if self.controller[STATE("igniter")] == 1:
            input(red(f"wtf man why you got the igniter on? just abort bro just abort "))

        self.fuel_upper_bound = FUEL_PREPRESS_TARGET
        self.fuel_lower_bound = FUEL_PREPRESS_TARGET - FUEL_PREPRESS_MARGIN
        self.fuel_abort_pressure = FUEL_PREPRESS_ABORT_PRESSURE
        self.ox_upper_bound = OX_PREPRESS_TARGET + OX_PREPRESS_MARGIN
        self.ox_lower_bound = OX_PREPRESS_TARGET - OX_PREPRESS_MARGIN
        self.ox_abort_pressure = OX_PREPRESS_ABORT_PRESSURE

        self.fuel_prepress_running = threading.Event()
        self.fuel_prepress_dome_iso_running = threading.Event()
        self.ox_prepress_running = threading.Event()
        self.igniter_verified = threading.Event()

        self.fuel_prepress_thread = threading.Thread()
        self.fuel_prepress_dome_iso_thread = threading.Thread()
        self.ox_prepress_thread = threading.Thread()

        if self.mode == "real" or self.mode == "sim":
            print(green(f"BURN_DURATION: ") + magenta(str(BURN_DURATION)))
            print(green(f"OX_PREPRESS_TARGET: ") + magenta(str(OX_PREPRESS_TARGET)))
            print(green(f"FUEL_PREPRESS_TARGET: ") + magenta(str(FUEL_PREPRESS_TARGET)))
            print(green(f"FIRST_MPV: ") + magenta(str(FIRST_MPV)))
            input(magenta("Press enter to confirm the test parameters listed above: "))

        print(green("All checks passed - initialization complete.\n"))
        return True

    def prepress_wrapper(self, prepress, flag):
        while flag.is_set():
            prepress()
            time.sleep(0.05)

    def prepress_fuel(self) -> bool:
        fuel_tank_pressure = statistics.median([
            self.controller[PT("fuel_tank_1")],
            self.controller[PT("fuel_tank_2")],
            self.controller[PT("fuel_tank_3")]
        ])
        fuel_prepress_open = self.controller[STATE("fuel_prepress")]

        if fuel_prepress_open and (fuel_tank_pressure >= self.fuel_upper_bound):
            self.fuel_prepress.close()

        elif (not fuel_prepress_open) and (fuel_tank_pressure <= self.fuel_lower_bound):
            self.fuel_prepress.open()

        elif fuel_tank_pressure >= self.fuel_abort_pressure:
            self.prepress_abort()

    def prepress_fuel_dome_iso(self) -> bool:
        fuel_tank_pressure = statistics.median([
            self.controller[PT("fuel_tank_1")],
            self.controller[PT("fuel_tank_2")],
            self.controller[PT("fuel_tank_3")]
        ])
        fuel_dome_iso_open = self.controller[STATE("fuel_dome_iso")]

        if fuel_dome_iso_open and (fuel_tank_pressure >= self.fuel_upper_bound):
            self.fuel_dome_iso.close()
        
        elif (not fuel_dome_iso_open) and (fuel_tank_pressure <= self.fuel_lower_bound):
            self.fuel_dome_iso.open()
        
        elif fuel_tank_pressure >= self.fuel_abort_pressure:
            self.prepress_abort()

    def prepress_ox(self) -> bool:
        ox_tank_pressure = statistics.median([
            self.controller[PT("ox_tank_1")],
            self.controller[PT("ox_tank_2")],
            self.controller[PT("ox_tank_3")]
        ])
        ox_dome_iso_open = self.controller[STATE("ox_dome_iso")]

        if ox_dome_iso_open and (ox_tank_pressure >= self.ox_upper_bound):
            self.ox_dome_iso.close()

        elif (not ox_dome_iso_open) and (ox_tank_pressure <= self.ox_lower_bound):
            self.ox_dome_iso.open()

        elif ox_tank_pressure >= self.ox_abort_pressure:
            self.prepress_abort()

    def main(self):
        """
        This function is the main thread which manages all the other
        parts of the autosequence. Minimal logic should be here.
        """
        try:
            self.initialize()
            prepress_delay = 3
            if self._using_fuel: # outside of try to avoid triggering prepress abort
                input(colorama.Fore.BLUE + f"Press enter to begin fuel prepress with PREPRESS valve ({prepress_delay} second countdown) " + colorama.Style.RESET_ALL)
                syauto.wait(prepress_delay, color=colorama.Fore.BLUE)
            try:
                if self._using_fuel:
                    self.fuel_prepress_running.clear()
                    self.fuel_prepress_running.set()
                    self.fuel_prepress_thread = threading.Thread(name="prepress_fuel_thread", target=self.prepress_wrapper, args=(self.prepress_fuel,self.fuel_prepress_running,))
                    print(green("Starting fuel prepress..."))
                    self.fuel_prepress_thread.start()

                if self._using_fuel:
                    input(colorama.Fore.BLUE + f"Press enter to begin fuel prepress with DOME ISO valve ({prepress_delay} second countdown) " + colorama.Style.RESET_ALL)
                    self.fuel_prepress_running.clear()
                    self.fuel_prepress_thread.join()
                    self.fuel_prepress.close()
                    
                    syauto.wait(prepress_delay, color=colorama.Fore.BLUE)
                    self.fuel_prepress_dome_iso_running.clear()
                    self.fuel_prepress_dome_iso_running.set()
                    self.fuel_prepress_dome_iso_thread = threading.Thread(name="prepress_fuel_dome_iso_thread", target=self.prepress_wrapper, args=(self.prepress_fuel_dome_iso,self.fuel_prepress_dome_iso_running,))
                    print(green("Starting fuel prepress dome iso..."))
                    self.fuel_prepress_dome_iso_thread.start()

                if self._using_ox:
                    input(colorama.Fore.BLUE + f"Press enter to begin ox prepress ({prepress_delay} second countdown) " + colorama.Style.RESET_ALL)
                    syauto.wait(prepress_delay, color=colorama.Fore.BLUE)

                    self.ox_vent.close()
                    self.ox_prepress_running.clear()
                    self.ox_prepress_running.set()
                    self.ox_prepress_thread = threading.Thread(name="prepress_ox_thread", target=self.prepress_wrapper, args=(self.prepress_ox,self.ox_prepress_running,))
                    print(green("Starting ox prepress..."))
                    self.ox_prepress_thread.start()

                firing = input(blue("Type `") + magenta("fire") + blue("` to begin firing sequence (10 second countdown) ") + colorama.Fore.MAGENTA).strip().lower()
                if firing == "fire":
                    print(green("Starting firing sequence..."))
                    try:
                        self.preignition_sequence()
                    except KeyboardInterrupt:
                        self.preignition_abort()
                    try:
                        self.postignition_sequence()
                    except KeyboardInterrupt:
                        self.postignition_abort()
                else:
                    self.prepress_abort()
            except KeyboardInterrupt:
                self.prepress_abort()
        except KeyboardInterrupt:
            print(red("\nTerminating autosequence..."))
            self.shutdown()
    
    def preignition_sequence(self):
        # igniter
        for command, delay, offset in self.firing_sequence:
            if delay > 0:
                if command == "first_mpv" or command == "second_mpv":
                    syauto.wait(delay, color=colorama.Fore.GREEN, offset=offset, increment=0.1, precision=1)
                else:
                    syauto.wait(delay, color=colorama.Fore.GREEN, offset=offset)
            if command == "igniter_open":
                self.igniter.open()
            elif command == "igniter_close":
                self.igniter.close()
            elif command == "end_prepress":
                if self.fuel_prepress_thread.is_alive():
                    self.fuel_prepress_running.clear()
                    self.fuel_prepress_thread.join()
                if self.ox_prepress_thread.is_alive():
                    self.ox_prepress_running.clear()
                    self.ox_prepress_thread.join()
                if self.fuel_prepress_dome_iso_thread.is_alive():
                    self.fuel_prepress_dome_iso_running.clear()
                    self.fuel_prepress_dome_iso_thread.join()
                self.ox_dome_iso.close()  # fallback
                self.fuel_prepress.close()  # fallback
                self.fuel_dome_iso.close()  # fallback
            elif command == "ox_dome":
                if not self._using_ox:
                    continue
                self.ox_dome_iso.open()
            elif command == "fuel_dome":
                if not self._using_fuel:
                    continue
                self.fuel_dome_iso.open()
            elif command == "return_line":
                if not self._using_ox:
                    continue
                self.ox_return_line.close()
            elif command == "first_mpv":
                self.first_mpv.open()
            elif command == "second_mpv":
                if not self._using_ox or not self._using_fuel:
                    continue  # assumes first MPV is the one for the test
                self.second_mpv.open()
            elif command == "start_ignition_detection":
                self.igniter_verification_thread = threading.Thread(
                    target=self.validate_ignition,
                    args=(IGNITER_LEAD - OX_DOME_LEAD,)
                )
                self.igniter_verification_thread.start()
                print(green("6"))  # otherwise no print
            elif command == "check_ignition_detection":
                self.igniter_verification_thread.join()
                lit = self.igniter_verified.is_set()
                if not lit:
                    print(red("Failed to verify igniter."))
                    self.preignition_abort()
            else:
                print(red(f"Unknown command: {command}"))

    def postignition_sequence(self):
        
        print(magenta(f"            * / //   /\n---IGNITION---***|||||::::>>>\n            * \\ \\\\   \\"))

        # burn
        syauto.wait(BURN_DURATION, color=colorama.Fore.GREEN)

        print(green("Purging..."))
        # post burn
        syauto.close_all(self.controller, [
            self.first_mpv, self.second_mpv, self.fuel_prevalve, self.ox_prevalve, self.press_iso,
        ])
        # if self._using_fuel:
        #     self.fuel_vent.open()
        # if self._using_ox:
        #     self.ox_vent.open()
        self.mpv_purge.open()
        syauto.wait(PURGE_DURATION, color=colorama.Fore.GREEN, message=green("Purge completed."))

        # post purge
        syauto.close_all(self.controller, [
            self.mpv_purge, self.ox_dome_iso, self.fuel_dome_iso,
        ])
        print(magenta("Firing sequence completed nominally."))
        self.shutdown(phoenix=True)

    def validate_ignition(self, window: float) -> bool:
        """
        Thread-safe input validation with proper timeout handling.
        Returns True iff Enter is pressed within `window` seconds.
        """
        input_received = threading.Event()
        self.igniter_verified.clear()

        def input_thread():
            try:
                sys.stdin.readline()
                input_received.set()
                if input_received.is_set():
                    return
            except:
                pass

        listener = threading.Thread(target=input_thread)
        listener.daemon = True  # to close thread if main exits

        start_time = time.time()
        listener.start()
        print(blue(f"Verify igniter by pressing Enter in the next {window} seconds."))
        while (time.time() - start_time) < window:
            if input_received.is_set():
                print(magenta("---IGNITER HAS BEEN VERIFIED---"))
                self.igniter_verified.set()
                return
            listener.join(0.001)
        input_received.set()
        return

    def prepress_abort(self):
        print(red("\nInitiating PREPRESS ABORT..."))
        self.fuel_prepress_running.clear()
        self.ox_prepress_running.clear()
        print(yellow("Terminating prepress..."))
        print(yellow("Closing valves..."))
        syauto.close_all(self.controller, [
            self.ox_dome_iso, self.fuel_prepress, self.press_iso, self.fuel_dome_iso,
        ])
        if self.fuel_prepress_thread.is_alive():
            self.fuel_prepress_thread.join()
        if self.ox_prepress_thread.is_alive():
            self.ox_prepress_thread.join()
        self.shutdown()

    def preignition_abort(self):
        print(red("\nInitiating PREIGNITION ABORT..."))
        self.fuel_prepress_running.clear()
        self.ox_prepress_running.clear()
        print(red("Closing valves..."))
        syauto.close_all(self.controller, [
            self.fuel_prepress, self.press_iso,
        ])
        print(red("Opening vents..."))
        if self._using_fuel:
            self.fuel_vent.open()
        if self._using_ox:
            self.ox_vent.open()
        syauto.wait(PURGE_DURATION, color=colorama.Fore.RED)
        print(red("Closing Dome Isos..."))
        syauto.close_all(self.controller, [
            self.ox_dome_iso, self.fuel_dome_iso,
        ])
        if self.fuel_prepress_thread.is_alive():
            self.fuel_prepress_thread.join()
        if self.ox_prepress_thread.is_alive():
            self.ox_prepress_thread.join()
        self.shutdown()

    def postignition_abort(self):
        print(red("\nInitiating POSTIGNITION ABORT..."))
        print(red("Closing valves..."))
        syauto.close_all(self.controller, [
            self.press_iso, self.first_mpv, self.second_mpv, self.fuel_prevalve, self.ox_prevalve,
        ])
        print(red("Opening vents and purge..."))
        if self._using_fuel:
            self.fuel_vent.open()
        if self._using_ox:
            self.ox_vent.open()
        syauto.wait(PURGE_DURATION, color=colorama.Fore.RED, message=red("Purge completed"))
        print(red("Closing MPV Purge + Dome Isos..."))
        syauto.close_all(self.controller, [
            self.mpv_purge, self.ox_dome_iso, self.fuel_dome_iso,
        ])
        # postignition means prepress has already ended, so no thread merging
        self.shutdown()

    def shutdown(self, phoenix=False):
        try:
            self.controller.release()
            time.sleep(0.5)
        except AttributeError:
            pass
        print(green("Autosequence has released control."))
        if phoenix:
            f = open('phoenix.txt', 'r')
            print(colorama.Fore.RED + f.read() + colorama.Style.RESET_ALL)
            f.close()
        exit()

autosequence = Autosequence()
autosequence.main()