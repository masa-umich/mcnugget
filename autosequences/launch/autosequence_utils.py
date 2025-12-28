# A helper file & classses for common autosequence utilties
from datetime import datetime
import statistics
import time
from termcolor import colored
import yaml
import synnax as sy
from synnax.control.controller import Controller
from typing import Any, Callable
import threading
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import ANSI


class Config:
    """
    Parses a config.yaml file for channel mappings and autosequence variables.
    Use get_var(name) or get_vlv(name) to get objects from the config file
    Also checks that the requested field exists, throws an error if it doesn't
    """

    _yaml_data: dict

    vars: dict[str, Any]
    vlvs: dict[str, str]
    pts: dict[str, str]
    tcs: dict[str, str]

    def __init__(self, filepath: str):
        self.vlvs: dict[str, str] = {}
        self.normally_open_vlvs: dict[str, bool] = {}
        self.pts: dict[str, str] = {}
        self.tcs: dict[str, str] = {}
        self.vars: dict[str, Any] = {}

        prefix_map: dict[str, str] = {
            "ebox": "gse",
            "flight_computer": "fc",
            "bay_board_1": "bb1",
            "bay_board_2": "bb2",
            "bay_board_3": "bb3",
        }

        type_suffix_map: dict[str, str] = {"pts": "pt", "valves": "vlv", "tcs": "tc"}

        with open(filepath, "r") as f:
            self._yaml_data: dict = yaml.safe_load(f)

        self.vars: dict[str, Any] = self._yaml_data.get("variables", {})
        mappings_data: dict[Any, Any] = self._yaml_data.get("channel_mappings", {})

        for controller_key, prefix in prefix_map.items():
            controller_data = mappings_data.get(controller_key)
            if not controller_data:
                continue

            for type_key, suffix in type_suffix_map.items():
                items = controller_data.get(type_key)
                if not items:
                    continue  # Skip if this controller doesn't have TCs (e.g. Flight Computer)

                for config_ch_name, value in items.items():
                    # Construct Synnax Name: prefix_suffix_index (e.g., gse_pt_1)
                    ch_index = value
                    is_normally_open = False # Default assumption

                    # If the entry has extra information
                    if isinstance(value, dict):
                        ch_index = value.get("id")
                        # We use .get(key, default) so it still works if 'normally_open' is omitted
                        is_normally_open = value.get("normally_open", False)
                    
                    # Construct Synnax Name
                    synnax_name = f"{prefix}_{suffix}_{ch_index}"
                    real_name: str = config_ch_name.lower()

                    if suffix == "pt":
                        self.pts[real_name] = synnax_name
                    elif suffix == "tc":
                        self.tcs[real_name] = synnax_name
                    elif suffix == "vlv":
                        self.vlvs[real_name] = synnax_name
                        self.normally_open_vlvs[real_name] = is_normally_open
                        self.normally_open_vlvs[synnax_name] = is_normally_open # add both name styles
                    else:
                        raise Exception("Bad entry in mappings part of config")

    def get_var(self, name: str) -> Any:
        var: Any | None = self.vars.get(name.lower())
        if var is not None:
            return var
        else:
            raise Exception(f"Could not find variable with name: '{name}' in config")

    def get_vlv(self, name: str) -> str:
        vlv: str | None = self.vlvs.get(name.lower())
        if vlv is not None:
            return vlv
        else:
            raise Exception(f"Could not find valve with name: '{name}' in config")

    def is_vlv_nc(self, name: str) -> bool:
        nc: bool | None = self.normally_open_vlvs.get(name.lower())
        if nc is not None:
            return not nc
        else:
            raise Exception(f"Could not find valve with name: '{name}' in config")

    def get_state(self, name: str) -> str:
        vlv: str | None = self.vlvs.get(name.lower())
        if vlv is not None:
            return vlv.replace("vlv", "state")
        else:
            raise Exception(f"Could not find valve with name: '{name}' in config")

    def get_pt(self, name: str) -> str:
        pt: str | None = self.pts.get(name.lower())
        if pt is not None:
            return pt
        else:
            raise Exception(f"Could not find pt with name: '{name}' in config")

    def get_tc(self, name: str) -> str:
        tc: str | None = self.tcs.get(name.lower())
        if tc is not None:
            return tc
        else:
            raise Exception(f"Could not find tc with name: '{name}' in config")

    def get_vlvs(self) -> list[str]:
        all_vlvs: list[str] = []
        for vlv in self.vlvs.values():
            all_vlvs.append(vlv)
        return all_vlvs

    def get_states(self) -> list[str]:
        all_states: list[str] = []
        for vlv in self.vlvs.values():
            all_states.append(vlv.replace("vlv", "state"))
        return all_states

    def get_sensors(self) -> list[str]:
        all_sensors: list[str] = []
        for pt in self.pts.values():
            all_sensors.append(pt)
        for tc in self.tcs.values():
            all_sensors.append(tc)
        return all_sensors


class average_ch:
    """
    Uses EWMA to run a weighted running average on data in a performant way
    https://en.wikipedia.org/wiki/EWMA_chart
    """

    avg: float
    initialized: bool
    alpha: float

    def __init__(self, window: float | int):
        # Alpha approximates a window of N items: alpha = 2 / (N + 1)
        self.alpha: float = 2.0 / (window + 1)
        self.avg = 0.0
        self.initialized = False

    def add(self, value: float | None) -> None:
        if not self.initialized:
            if value is None:
                raise Exception("Cannot add None value to uninitialized average_ch")
            self.avg: float = value
            self.initialized = True
        else:
            if value is None:
                return
            # Standard EWMA formula
            self.avg: float = (value * self.alpha) + (self.avg * (1 - self.alpha))

    def set_avg(self, input: float) -> None:
        self.avg: float = input

    def get(self) -> float:
        return self.avg

    def add_and_get(self, value: float | None) -> float:
        self.add(value)
        return self.get()


def sensor_vote_values(input: list[float], threshold: float) -> float | None:
    """
    Helper function to vote between a list of values.
    For the values agree within the given threshold, the median is returned
    Values that don't agree inside of the threshold are discarded
    """
    if not input:
        return None
    if len(input) == 1:
        return input[0]

    median_val: float = statistics.median(input)

    trusted_sensors: list[float] = [
        x for x in input if abs(x - median_val) <= threshold
    ]

    if not trusted_sensors:
        return median_val

    return sum(trusted_sensors) / len(trusted_sensors)


def sensor_vote(
    ctrl: Controller, channels: list[str], threshold: float
) -> float | None:
    """
    Wrapper of sensor_vote_values which skips the step of getting the values from the controller
    """
    values: list[float] = []
    for ch in channels:
        value: float | None = ctrl.get(ch)
        if value is not None:
            values.append(value)
    return sensor_vote_values(values, threshold)


def open_vlv(ctrl: Controller, vlv_name: str) -> None:
    """
    Helper function to open a valve only if not already open
    """
    state_name: str = vlv_name.replace("vlv", "state")
    state = ctrl.get(state_name)
    if state is None:
        raise Exception(f"Could not get state of valve: {vlv_name}, is the valve defined?")
    if state == True:
        return
    ctrl[vlv_name] = True


def close_vlv(ctrl: Controller, vlv_name: str) -> None:
    """
    Helper function to close a valve only if not already closed
    """
    state_name: str = vlv_name.replace("vlv", "state")
    state = ctrl.get(state_name)
    if state is None:
        raise Exception(f"Could not get state of valve: {vlv_name}, is the valve defined?")
    if state == False:
        return
    ctrl[vlv_name] = False


logs: list[str] = []  # Global log list for storing logs if needed

def log(msg: str, color: str = "white", bold: bool = False, phase_name: str | None = None) -> None:
    """
    Helper function to get around prompt_toolkit printing issues w/ termcolor
    Also adds ISO 8601 timestamp and phase name if provided
    Also can be written to a log file later with `write_logs_to_file()`
    """
    now: str = datetime.now().isoformat()
    entry: str = now

    if phase_name != None: # Add phase name if provided
        entry += colored(f" [{phase_name}]", color="yellow")
    entry += colored(" > ", color="dark_grey")

    if bold == False: # Add message with color / bolding
        entry += colored(msg, color=color)
    else:
        entry += colored(msg, color=color, attrs=["bold"])
    
    # Store log without ANSI codes
    raw_entry: str = now
    if phase_name != None:
        raw_entry += f" [{phase_name}]"
    raw_entry += " > " + msg
    logs.append(raw_entry)

    print_formatted_text(ANSI(entry))


def write_logs_to_file(filepath: str) -> None:
    """
    Helper function to write the current logs to a file
    """
    with open(filepath, "w") as f:
        for log_entry in logs:
            # Strip ANSI codes for file writing
            f.write(log_entry + "\n")


def printf(msg: str, color: str = "white", bold: bool = False) -> None:
    """
    Helper function to get around prompt_toolkit printing issues w/ termcolor
    """
    if bold == False:
        print_formatted_text(ANSI(colored(msg, color=color)))
    else:
        print_formatted_text(ANSI(colored(msg, color=color, attrs=["bold"])))


class SequenceAborted(Exception):
    """
    Exceptions are used for abort logic, under an abort case this exception is raised
    which can then be caught in a try except block inside of the phase
    """

    pass


class Phase:
    """
    A phase which is a function wrapper for a portion of Autosequence logic.
    A "phase" also associates a thread with the function and allows
    for an abort case to run when closing the thread with a try except block

    Underlying function for each phase's logic should be defined in another file.
    Every function passed to the constructor must take a Phase object as its only argument.
    The Synnax controller and config objects can be taken from that Phase object
    """

    name: str

    ctrl: Controller
    config: Config

    _abort: threading.Event  # Thread-safe flag
    _pause: threading.Event  # Thread-safe flag

    _func_thread: threading.Thread  # Thread wrapper

    _refresh_rate: int  # Hz
    # The minimum amount of time (in seconds) the thread should be spent sleeping / yielding
    # Large values (0.1+) result in an unresponsive autosequence
    # Small values (0.01-) may use more system resources and overhead
    # A good value should be twice the time of your system's refresh rate (50Hz -> 0.01s)
    _refresh_period: float

    # Constructor
    def __init__(
        self,
        name: str,
        func: Callable,
        ctrl: Controller,
        config: Config,
        refresh_rate: int = 50,
    ):
        self.name: str = name

        self.ctrl: Controller = ctrl
        self.config: Config = config

        self._refresh_rate: int = refresh_rate
        self._refresh_period: float = 1.0 / (2.0 * self._refresh_rate)

        self._func_thread = threading.Thread(
            name=self.name,
            target=self._func_wrapper,
            args=(func,),
        )

        self._pause = threading.Event()
        self._pause.clear()  # Make sure flag is cleared initially

        self._abort = threading.Event()
        self._abort.clear()  # Make sure flag is cleared initially

    # Checks for abort or pause signals. Blocks if paused
    def _check_signals(self) -> None:
        if self._abort.is_set():
            raise SequenceAborted("Sequence Aborted")

        while self._pause.is_set():
            if self._abort.is_set():
                raise SequenceAborted("Sequence Aborted during pause")
            time.sleep(self._refresh_period)  # Sleep and yield thread

    # Sleep function that should be used inside of the control sequence
    # Allows for thread aborting and pausing with _check_signals
    # This should be used instead of time.sleep() at all times when thread yielding is safe
    def sleep(self, duration: float) -> None:
        end_time: float = time.time() + duration
        while True:
            self._check_signals()
            remaining: float = end_time - time.time()
            if remaining <= 0:
                return
            time.sleep(min(self._refresh_period, remaining))  # Sleep and yield thread

    # Similar to ctrl.wait_until() but allows yielding, similar to phase.sleep()
    def wait_until(
        self, cond: Callable[[Controller], bool], timeout: float | None = None
    ) -> bool:
        start_time: float = time.time()
        while True:
            self._check_signals()

            # Calculate slice timeout
            slice_time: float = self._refresh_period
            if timeout is not None:
                elapsed: float = time.time() - start_time
                remaining: float = timeout - elapsed
                if remaining <= 0:
                    return False
                slice_time: float = min(slice_time, remaining)

            # Use the synnax controller to wait for this slice
            if self.ctrl.wait_until(cond, timeout=slice_time):
                return True

    def avg_and_vote_for(
        self,
        ctrl: Controller,
        channels: list[str],
        threshold: float,
        averaging_time: float,
    ) -> float:
        """
        Helper function to both average and vote on a set of channels over a given time period, useful for getting a baseline reading
        """
        value = average_ch(
            round(self._refresh_rate * averaging_time)
        )  # would be better to base off real refresh rate
        end_time: sy.TimeStamp = sy.TimeStamp.now() + sy.TimeSpan.from_seconds(
            averaging_time
        )
        while sy.TimeStamp.now() < end_time:
            value.add(sensor_vote(ctrl, channels, threshold))
            self.sleep(self._refresh_period)  # allow time to yield
        return value.get()

    def log(self, msg: str, color: str = "white", bold: bool = False) -> None:
        """
        Log wrapper that inserts the phase name responsible for the log entry
        """
        log(msg=msg, color=color, bold=bold, phase_name=self.name)

    # A function wrapper to be able to do threading stuff (might not be necessary)
    def _func_wrapper(self, func: Callable):
        func(self)

    def start(self) -> None:
        self._func_thread.start()

    def join(self) -> None:
        self._func_thread.join()

    def abort(self) -> None:
        self._abort.set()

    def pause(self) -> None:
        self._pause.set()

    def unpause(self) -> None:
        self._pause.clear()


class Autosequence:
    """
    An autosequence which is a wrapper of phases and a way to run them
    Also contains the configuration, channel mappings, and optional command terminal
    """

    # Public members
    name: str
    client: sy.Synnax  # Synnax connection
    ctrl: Controller

    phases: list[Phase]
    config: Config
    global_abort: Callable | None
    abort_flag: threading.Event  # Thread-safe flag

    # Private members
    _has_released: bool
    _background_thread: threading.Thread | None = None
    _interface_thread: threading.Thread | None = None
    _prompt_session: PromptSession | None = None

    # Constuctor
    def __init__(
        self,
        name: str,
        cluster: str,
        config: Config,
        global_abort: Callable | None = None,
        background_thread: Callable | None = None,
    ):
        self.name: str = name
        self.config: Config = config
        self.phases: list[Phase] = []
        self.global_abort: Callable | None = global_abort
        self.abort_flag: threading.Event = threading.Event()
        self.abort_flag.clear()  # Make sure flag is cleared initially

        # Try to login
        self.client: sy.Synnax = self.synnax_login(cluster)

        # Take control with autosequence
        self.ctrl: Controller = self.client.control.acquire(
            name=name,
            write_authorities=1,  # 1 is the default console authority (NOTE: This might/should be higher)
            write=self.config.get_vlvs(),
            read=self.config.get_sensors() + self.config.get_states(),
        )
        self._has_released = False

        # Error if not all channels were found / defined
        channels: list[str] = self.config.get_sensors() + self.config.get_states()
        defined: bool = self.ctrl.wait_until_defined(
            channels=channels,  # type: ignore
            timeout=5,
        )
        if not defined:
            self.release()
            raise Exception(
                "Some channels defined in the autosequence config are not defined in Synnax, are all drivers running?"
            )

        # Setup background thread if provided
        if background_thread is not None:
            self._background_thread = threading.Thread(
                name="Autosequence Background",
                target=background_thread,
                args=(self,),
            )

    # Destructor, make sure to release control!
    def __del__(self) -> None:
        if not self._has_released:
            self.release()
            self._has_released = True  # Object should be deleted atp but just in case

    def init_valves(self) -> None:
        # Set every valve to closed state initially
        for vlv in self.config.get_vlvs():
            is_nc: bool = self.config.is_vlv_nc(vlv)
            state = self.ctrl.get(vlv.replace("vlv", "state"))
            confirm = "y"
            if state == True:
                if is_nc:
                    confirm: str = input(f"Valve {vlv} is currently OPEN, should it be closed? (y/n): ")
                    if confirm.lower() == "y" or confirm.lower() == "yes":
                        log(f"Closing valve {vlv} on autosequence start")
                        close_vlv(self.ctrl, vlv)
            else:
                if not is_nc:
                    confirm: str = input(f"Valve {vlv} is currently OPEN, should it be closed? (y/n): ")
                    if confirm.lower() == "y" or confirm.lower() == "yes":
                        log(f"Closing valve {vlv} on autosequence start")
                        open_vlv(self.ctrl, vlv) # "open" is actually closing for NO valves

    def synnax_login(self, cluster: str) -> sy.Synnax:
        try:
            client = sy.Synnax(
                host=cluster,
                port=9090,
                username="synnax",
                password="seldon",
            )
        except Exception:
            raise Exception(
                f"Could not connect to Synnax at {cluster}, are you sure you're connected?"
            )
        return client

    def add_phase(self, phase: Phase) -> None:
        self.phases.append(phase)

    def raise_abort(self) -> None:
        self.abort_flag.set()

    def release(self) -> None:
        if not self._has_released:
            self.ctrl.release()
            log("Autosequence has released control")
            self._has_released = True

    def get_phase(self, phase_name: str) -> Phase | None:
        for phase in self.phases:
            if phase_name == phase.name.lower():
                return phase
        return None

    # Run command interface thread & main listener thread
    def run(self) -> None:
        with patch_stdout():  # Fix print statements with command interface
            # Run background thread if provided
            if self._background_thread is not None:
                self._background_thread.start()
            # Run command interface thread
            self._interface_thread = threading.Thread(
                name="Autosequence Interface",
                target=self._interface_func,
            )
            self._interface_thread.start()
            while True:
                # Listen for abort signal
                if self.abort_flag.is_set():
                    # Kill the command interface thread
                    if (self._prompt_session is not None) and (self._prompt_session.app.is_running):
                        self._prompt_session.app.exit()
                    if (self._interface_thread is not None) and (self._interface_thread.is_alive()):
                        self._interface_thread.join()
                    time.sleep(0.1)  # give a small amount of time for thread to close
                    for phase in self.phases:
                        phase.abort()
                        if phase._func_thread.is_alive():
                            phase.join()
                    time.sleep(0.1)
                    if self.global_abort is not None:
                        self.global_abort(self)
                    # Kill the background thread if it exists
                    if (self._background_thread is not None) and (self._background_thread.is_alive()):
                        self._background_thread.join()
                    self.release()
                    log("Autosequence aborted successfully")
                    return
                time.sleep(0.01)  # Yield thread

    def _interface_func(self) -> None:
        # TODO: only allow some state / phase transitions
        try:
            printf(f"Welcome to the {self.name}!", color="green", bold=True)
            printf("Valid commands:", color="green", bold=True)
            printf(" > start <phase>", color="light_green")
            printf(" > abort <phase>", color="light_green")
            printf(" > pause <phase>", color="light_green")
            printf(" > unpause <phase>", color="light_green")
            printf(" > quit", color="light_green")
            printf("Valid phases:", color="green", bold=True)
            for phase_name in self.phases:
                printf(f" - {phase_name.name}", color="light_green")

            self._prompt_session = PromptSession()
            while not self.abort_flag.is_set():  # Parse input
                user_input: str = self._prompt_session.prompt(" > ")
                if self.abort_flag.is_set():
                    return  # exit if abort flag set during prompt
                parts: list[str] = (
                    user_input.strip().lower().split(maxsplit=1)
                )  # Get command and phase
                if len(parts) == 0:
                    print(" > Please input a command")
                    continue
                command: str = parts[0]
                if (len(parts) == 1) and (parts[0] != "quit") and (parts[0] != "exit"):
                    print(" > Please specify a phase name")
                    continue
                if (command == "quit") or (command == "exit"):
                    print(" > Exiting autosequence interface...")
                    self.raise_abort()
                    return
                phase: Phase | None = self.get_phase(phase_name=parts[1])
                if phase is None:
                    print(" > Phase not recognized, please try again")
                    continue
                match command:
                    case "start":
                        phase.start()
                    case "abort":
                        phase.abort()
                    case "pause":
                        phase.pause()
                    case "unpause":
                        phase.unpause()
                    case _:
                        print(" > Unrecognized command, please try again")
                        continue
        except KeyboardInterrupt:
            log("Keyboard interrupt detected, aborting!")
            self.raise_abort()
        except EOFError:
            log("Keyboard interrupt detected, aborting!")
            self.raise_abort()
        return
