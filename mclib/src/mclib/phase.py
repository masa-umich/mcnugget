from __future__ import annotations
from typing import Callable, TYPE_CHECKING
import threading
import time
import synnax as sy
from synnax.control.controller import Controller
from mclib.config import Config
from mclib.logger import log
from mclib.average import average_ch, sensor_vote

if TYPE_CHECKING:
    from mclib.autosequence import Autosequence

# Global shared state
parent_range: sy.Range | None = None


class SequenceAborted(Exception):
    pass


class SequenceExited(Exception):
    pass


class Phase:
    name: str

    ctrl: Controller
    config: Config

    auto: "Autosequence"

    phase_start_time: sy.TimeStamp | None = None

    _abort: threading.Event  # Thread-safe flag
    _quit: threading.Event  # Thread-safe flag
    _pause: threading.Event  # Thread-safe flag
    _wait: threading.Event  # Thread-safe flag for waiting for input
    _stop_wait: threading.Event  # Thread-safe flag for stopping wait for input

    _func_thread: threading.Thread  # Thread wrapper
    _safe_func: Callable | None = None  # Optional safe function to run on abort

    _refresh_rate: int  # Hz
    _refresh_period: float

    def __init__(
        self,
        name: str,
        ctrl: Controller,
        config: Config,
        main_func: Callable,
        auto: "Autosequence",
        safe_func: Callable | None = None,
        refresh_rate: int = 50,
    ):
        self.name: str = name

        self.ctrl: Controller = ctrl
        self.config: Config = config
        self.auto: Autosequence = auto

        self._refresh_rate: int = refresh_rate
        self._refresh_period: float = 1.0 / (2.0 * self._refresh_rate)

        self._safe_func: Callable | None = safe_func
        self._func_thread = threading.Thread(
            name=self.name,
            target=self._func_wrapper,
            args=(main_func,),
        )

        self._pause = threading.Event()
        self._pause.clear()  # Make sure flag is cleared initially

        self._abort = threading.Event()
        self._abort.clear()  # Make sure flag is cleared initially

        self._wait = threading.Event()
        self._wait.clear()  # Make sure flag is cleared initially

        self._quit = threading.Event()
        self._quit.clear()  # Make sure flag is cleared initially

    # Checks for abort or pause signals. Blocks if paused
    def _check_signals(self) -> None:
        if self._abort.is_set():
            raise SequenceAborted("Sequence Aborted")

        if self._pause.is_set():
            if self._safe_func is not None:
                self._safe_func(self)

            while self._pause.is_set():
                if self._abort.is_set():
                    raise SequenceAborted("Sequence Aborted during pause")
                if self._quit.is_set():
                    raise SequenceExited()
                time.sleep(self._refresh_period)  # Sleep and yield thread

        if self._quit.is_set():
            raise SequenceExited()

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

    # A function wrapper to be able to do threading stuff and abort handling
    def _func_wrapper(self, main_func: Callable) -> None:
        try:
            main_func(self)
        except:
            if self._safe_func is not None:
                self._safe_func(self)
        finally:
            if parent_range is not None:
                parent_range.create_child_range(
                    name=self.name,
                    time_range=sy.TimeRange(self.phase_start_time, sy.TimeStamp.now()),
                    color="#7849E5",
                )

    def start(self) -> None:
        if self._func_thread.ident is None:
            # Record the phase start time before starting the worker thread to avoid
            # a race where the thread's finally block runs before this is set.
            self.phase_start_time = sy.TimeStamp.now()
            self._func_thread.start()
        else:
            log(f"Phase {self.name} already started")

    def join(self) -> None:
        self._func_thread.join()

    def abort(self) -> None:
        self._abort.set()

    def quit(self) -> None:
        self._quit.set()

    def pause(self) -> None:
        self._pause.set()

    def unpause(self) -> None:
        self._pause.clear()

    def wait_for_input(self) -> None:
        self._wait.set()
        self._check_signals()

    def stop_waiting_for_input(self) -> None:
        self._wait.clear()
