from __future__ import annotations
from typing import Callable, List, Dict
import threading
import time
import synnax as sy
from synnax.control.controller import Controller
from mclib.config import Config
from mclib.logger import log, printf
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.patch_stdout import patch_stdout

from mclib.phase import Phase


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

    start_time: sy.TimeStamp
    aliases: Dict[int | str, str]

    # Private members
    _has_released: bool
    _background_thread: threading.Thread | None = None
    _interface_thread: threading.Thread | None = None
    _prompt_session: PromptSession | None = None
    _has_clean_quit: threading.Event

    # Constructor
    def __init__(
        self,
        name: str,
        cluster: str,
        config: Config,
        global_abort: Callable | None = None,
        background_thread: Callable | None = None,
    ):
        self._has_released = False
        self.start_time = sy.TimeStamp.now()
        self.name: str = name
        self.config: Config = config
        self.phases: List[Phase] = []
        self.global_abort: Callable | None = global_abort
        self.abort_flag: threading.Event = threading.Event()
        self.abort_flag.clear()  # Make sure flag is cleared initially
        self._has_clean_quit: threading.Event = threading.Event()
        self._has_clean_quit.clear()

        # Try to login
        self.client: sy.Synnax = self.synnax_login(cluster)

        # Make range
        day: str = sy.TimeStamp.now().datetime().strftime("%m/%d")
        run: int = len(self.client.ranges.search(term=f"{self.name} {day} run")) + 1

        import mclib.phase

        mclib.phase.parent_range = self.client.ranges.create(
            name=f"{self.name} {day} run {run}",
            time_range=sy.TimeRange(sy.TimeStamp.now(), sy.TimeStamp.now()),
        )

        # join all dicts together
        all_channels: Dict[str, str] = (
            self.config.pts | self.config.tcs | self.config.vlvs
        )
        # swap keys and values for correct synnax alias format
        self.aliases: Dict[int | str, str] = {
            value: key for key, value in all_channels.items()
        }
        # replace underscores in aliases with spaces
        self.aliases: Dict[int | str, str] = {
            alias: name.replace("_", " ") for alias, name in self.aliases.items()
        }
        # apply aliases
        mclib.phase.parent_range.set_alias(self.aliases)

        # Take control with autosequence
        self.ctrl: Controller = self.client.control.acquire(
            name=name,
            write_authorities=255,  # 1 is the default console authority (NOTE: This might/should be higher)
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
        # Update the parent range to end at the end of the autosequence
        import mclib.phase

        if mclib.phase.parent_range is not None:
            mclib.phase.parent_range = self.client.ranges.create(
                name=mclib.phase.parent_range.name,  # type: ignore
                key=mclib.phase.parent_range.key,  # type: ignore
                time_range=sy.TimeRange(self.start_time, sy.TimeStamp.now()),
                color="#00ff1e",
            )

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
        self.start_time = sy.TimeStamp.now()

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
                    if (self._prompt_session is not None) and (
                        self._prompt_session.app.is_running
                    ):
                        self._prompt_session.app.exit()
                    if (self._interface_thread is not None) and (
                        self._interface_thread.is_alive()
                    ):
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
                    if (self._background_thread is not None) and (
                        self._background_thread.is_alive()
                    ):
                        self._background_thread.join()
                    self.release()
                    log("Autosequence aborted successfully")
                    return
                elif self._has_clean_quit.is_set():
                    if (self._interface_thread is not None) and (
                        self._interface_thread.is_alive()
                    ):
                        self._interface_thread.join()
                    time.sleep(0.1)
                    for phase in self.phases:
                        phase.quit()
                        if phase._func_thread.is_alive():
                            phase.join()
                    if (self._background_thread is not None) and (
                        self._background_thread.is_alive()
                    ):
                        self._background_thread.join()
                    self.release()
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
            for phase in self.phases:
                printf(f" - {phase.name}", color="light_green")

            completer_phases = [phase.name for phase in self.phases]
            complete_cmds = {
                "start": {p: None for p in completer_phases},
                "pause": {p: None for p in completer_phases},
                "unpause": {p: None for p in completer_phases},
                "abort": {p: None for p in completer_phases},
                "quit": None,
            }
            completer = NestedCompleter.from_nested_dict(complete_cmds)
            completer.ignore_case = True
            self._prompt_session = PromptSession(
                completer=completer,
                complete_while_typing=True,
                complete_style=CompleteStyle.COLUMN,
            )
            while not self.abort_flag.is_set():  # Parse input
                user_input: str = self._prompt_session.prompt(" > ")
                if self.abort_flag.is_set():
                    return  # exit if abort flag set during prompt
                parts: list[str] = (
                    user_input.strip().lower().split(maxsplit=1)
                )  # Get command and phase
                if len(parts) == 0:
                    for p in self.phases:
                        if p._wait.is_set():
                            p.stop_waiting_for_input()
                    continue
                command: str = parts[0]
                if (len(parts) == 1) and (parts[0] != "quit") and (parts[0] != "exit"):
                    print(" > Please specify a phase name")
                    continue
                if (command == "quit") or (command == "exit"):
                    print(" > Exiting autosequence interface...")
                    self._has_clean_quit.set()
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
