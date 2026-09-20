#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax==0.49.8",
#     "yaspin",
#     "termcolor",
#     "pyyaml",
#     "mclib",
# ]
# [tool.uv]
# reinstall-package = ["mclib"]
# [tool.uv.sources]
# mclib = { path = "../../mclib" }
# ///

#
# torch.py
# Torch Igniter Autosequence
#
#
#   - The T-5 countdown step is GONE. Sequence now goes straight from
#     "fire" input to energizing the spark plug at T-0.
#   - Step 3.107 (previously #REF!) is now just "wait for MPV delay" --
#     the mystery gap is resolved, it was never anything more than that.
#   - NO MORE RETRY LOOP. No-light now hard-aborts (jumps straight into
#     the same close/vent/de-energize sequence as a manual abort) --
#     there's no "retry?" prompt in the current SOP text at all.
#   - Normal shutdown and abort are now THE SAME ACTION: both close both
#     MPVs, open BOTH vents, and de-energize spark. Previously normal
#     shutdown didn't open vents. This let me collapse both into one
#     shared shutdown_torch() helper below.
#   - Ignition detection is no longer a percentage-of-samples-above-a-
#     single-threshold vote. It's now a [Lower, Upper] psig RANGE
#     (165-242 psig, both real, filled-in values) held for a
#     confirmation debounce time.
#   - "Spark Attempt Duration" (3s, now a REAL value) turns out to BE
#     the total ignition-confirmation timeout -- the "[T+3]" label on
#     the no-light-abort step lines up exactly with it. That's the
#     answer to "abort if ignition not confirmed after X seconds" from
#     the last meeting's notes: X = 3s, and it's no longer a guess.
#   - MPV Order is LITERALLY marked "Unknown / Unknown" (1st and 2nd)
#     in System_Parameters now -- not ambiguous phrasing, an admitted
#     open question in the SOP itself. Both MPVs are opened together
#     below as a placeholder; order still needs to be decided.
#
# NOT changed / still open:
#   - MPV Delay is still "XX ms" -- unset.
#   - Ignition Confirmation Time is still "XX ms" -- unset.
#   - Spark Plug still has NO Channel assigned at all in the
#     Instrumentation sheet (not just NO/NC -- no channel number).
#   - NO/NC is still blank for every valve.
#   - Torch PT 3 (channel 15) now exists in Instrumentation but isn't
#     used below -- only PT 1/2 are referenced, matching "tee off to
#     two PTs" from the CDR. Confirm whether PT 3 should be involved.
#   - The "igniter armed/disarmed" checks in the SOP's Section 0
#     (0.407-0.408, 0.416-0.417) read as a physical/manual safety
#     interlock, not a Synnax channel -- nothing to implement for it
#     here, just something to physically verify before running this.
#   - The two-test (fixed-timer / detection-gated) split from the
#     meeting notes isn't reflected in this SOP revision -- Section 3
#     now describes exactly one canonical sequence. That informal test
#     plan may have been superseded by this rewrite, or may still be
#     wanted as an extra pre-hotfire validation layer -- worth
#     confirming which before assuming either way.
#   - The overpressure abort discussed in the same meeting also isn't
#     in this SOP revision yet -- background_thread() below is still a
#     stub for it, not a real implementation.
#

from termcolor import colored
from yaspin import yaspin

spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

import synnax as sy
from synnax.control.controller import Controller

from mclib import (
    Phase,
    Autosequence,
    Config,
    open_vlv,
    close_vlv,
    write_logs_to_file,
)

import argparse


REFRESH_RATE: int = 50  # Hz


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Torch Igniter Autosequence (Spectre Hotfire SOP Rev A, Section 3)"
    )
    parser.add_argument("-m", "--config", default="config.yaml", type=str)
    parser.add_argument("-c", "--cluster", default="synnax.masa.engin.umich.edu", type=str)
    parser.add_argument("-l", "--log", default="torch-autosequence.log", type=str)
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# 3.112 / 3.202: close both MPVs, open both vents, de-energize spark.
# Shared by normal completion AND abort.
# ---------------------------------------------------------------------------
def shutdown_torch(ctrl: Controller, config: Config) -> None:
    close_vlv(ctrl, config, config.get_vlv("torch_gox_mpv"))
    close_vlv(ctrl, config, config.get_vlv("torch_methane_mpv"))
    open_vlv(ctrl, config, config.get_vlv("torch_gox_post_mpv_vent"))
    open_vlv(ctrl, config, config.get_vlv("torch_methane_post_mpv_vent"))
    ctrl[config.get_vlv("torch_spark_plug")] = False


def global_abort(auto: Autosequence) -> None:
    ctrl: Controller = auto.ctrl
    config: Config = auto.config
    try:
        shutdown_torch(ctrl, config)
        print(colored("ABORT: spark off, MPVs closed, vents open.", "green", attrs=["bold"]))
    except Exception as e:
        print(colored(f"Error during torch abort: {e}", "red", attrs=["bold"]))


def background_thread(auto: Autosequence) -> None:
    # TODO: overpressure abort was discussed in the worksession but is not yet part of latest SOP revision.
    print(colored("Background task started", "cyan"))


# ---------------------------------------------------------------------------
# 3.109: Check for successful light.
#
# Ignition is confirmed if the torch PTs read within [165, 242] psig,
# held continuously for `ignition_confirmation_time`. Called repeatedly
# from firing_sequence() until either it returns True, or the total
# `spark_attempt_duration` timeout (3s, real value) elapses -- that
# outer timeout is what actually triggers the [T+3] abort in 3.110, not
# this function itself.
#
# TODO: requiring BOTH Torch PT 1 and PT 2 to agree (via `all()` below)
# is a guess at the intended redundancy logic. I guess it could equally be
# "either one is enough" (OR) depending on whether the two PTs are meant
# to catch a bad sensor (favor OR) or catch sensor noise (favor AND).
# Confirm which before trusting this.
# ---------------------------------------------------------------------------
def check_for_light(ctrl: Controller, config: Config) -> bool:
    lower: float = config.get_var("ignition_lower_threshold")  # 165 psig, real
    upper: float = config.get_var("ignition_upper_threshold")  # 242 psig, real
    confirmation_time_ms: float = config.get_var("ignition_confirmation_time")  # TODO: still "XX ms"

    channels: list[str] = [
        config.get_pt("torch_pt_1"),
        config.get_pt("torch_pt_2"),
    ]

    confirmation_time_s: float = confirmation_time_ms / 1000
    needed_samples: int = max(1, int(confirmation_time_s * REFRESH_RATE))
    consecutive_in_range: int = 0

    while True:
        in_range: bool = all(lower <= ctrl[ch] <= upper for ch in channels)
        if in_range:
            consecutive_in_range += 1
            if consecutive_in_range >= needed_samples:
                return True
        else:
            consecutive_in_range = 0
        sy.sleep(1 / REFRESH_RATE)


def wait_for_ignition(ctrl: Controller, config: Config, timeout_s: float) -> bool:
    """Repeats check_for_light-style polling until confirmed or timeout_s elapses."""
    start = sy.TimeStamp.now()
    end = start + sy.TimeSpan.from_seconds(timeout_s)
    lower: float = config.get_var("ignition_lower_threshold")
    upper: float = config.get_var("ignition_upper_threshold")
    channels: list[str] = [config.get_pt("torch_pt_1"), config.get_pt("torch_pt_2")]
    confirmation_time_ms: float = config.get_var("ignition_confirmation_time")  # TODO
    needed_samples: int = max(1, int((confirmation_time_ms / 1000) * REFRESH_RATE))
    consecutive_in_range: int = 0

    while sy.TimeStamp.now() < end:
        in_range: bool = all(lower <= ctrl[ch] <= upper for ch in channels)
        if in_range:
            consecutive_in_range += 1
            if consecutive_in_range >= needed_samples:
                return True
        else:
            consecutive_in_range = 0
        sy.sleep(1 / REFRESH_RATE)
    return False


# ---------------------------------------------------------------------------
# 3.101-3.113: Firing sequence, single canonical path per the SOP rewrite.
# No retry loop so if no-light hard-aborts.
# ---------------------------------------------------------------------------
def firing_sequence(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    spark: str = config.get_vlv("torch_spark_plug")
    gox_mpv: str = config.get_vlv("torch_gox_mpv")
    methane_mpv: str = config.get_vlv("torch_methane_mpv")

    mpv_delay: float = config.get_var("mpv_delay") / 1000  # TODO: still "XX ms" in SOP
    spark_attempt_duration: float = config.get_var("spark_attempt_duration")  # 3s, real -- also the ignition-confirm timeout
    burn_duration: float = config.get_var("burn_duration")  # 3s, real

    # 3.104-3.105: wait for fire input
    phase.log("Press 'enter' to fire the torch...")
    phase.wait_for_input()
    while phase._wait.is_set():
        phase.sleep(0.1)

    # 3.106: [T-0] energize spark plug (no countdown step anymore)
    ctrl[spark] = True
    phase.log("[T-0] Spark plug energized.", "yellow", True)

    # 3.107: wait for MPV delay
    phase.sleep(mpv_delay)

    # 3.108: open GOx MPV and Methane MPV - order is "Unknown" in the SOP itself.
    # Currently opening together as a placeholder; I need to confirm real order.
    open_vlv(ctrl, config, gox_mpv)
    open_vlv(ctrl, config, methane_mpv)
    phase.log("GOx MPV and Methane MPV open (order TBD).", "yellow", True)

    # 3.109-3.110: check for light; [T+3] hard abort if not confirmed
    # within spark_attempt_duration
    ignition_confirmed: bool = wait_for_ignition(ctrl, config, spark_attempt_duration)

    if not ignition_confirmed:
        phase.log(
            f"[T+{spark_attempt_duration:.0f}s] No light -- aborting.", "red", True
        )
        shutdown_torch(ctrl, config)
        return  # 3.203: terminate

    phase.log("Ignition confirmed.", "green", True)

    # 3.111: wait for burn duration
    phase.sleep(burn_duration)

    # 3.112: close MPVs, open vents, de-energize spark
    shutdown_torch(ctrl, config)
    phase.log("Burn complete. Valves closed, vents open, spark de-energized.", "green", True)
    # 3.113: terminate (phase returns)


def firing_sequence_safe(phase: Phase) -> None:
    """Safe state if this phase is interrupted mid-sequence (e.g. Ctrl-C)."""
    shutdown_torch(phase.ctrl, phase.config)


def main() -> None:
    args: argparse.Namespace = parse_args()
    config: Config = Config(filepath=args.config)

    auto: Autosequence = Autosequence(
        name="Torch Igniter Autosequence",
        cluster=args.cluster,
        config=config,
        global_abort=global_abort,
        background_thread=background_thread,
    )

    fire_phase: Phase = Phase(
        name="Firing Sequence",
        ctrl=auto.ctrl,
        config=config,
        main_func=firing_sequence,
        auto=auto,
        safe_func=firing_sequence_safe,
    )
    auto.add_phase(fire_phase)

    spinner.stop()
    auto.run()

    print(colored("Torch autosequence has terminated.", "green"))
    if args.log:
        write_logs_to_file(filepath=args.log)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("Keyboard interrupt -- see abort handling above.", "red"))
    except Exception as e:
        spinner.stop()
        raise e

# ---------------------------------------------------------------------------
# config.yaml entries -- real channel numbers now exist for most of these
# (per the updated Instrumentation sheet), filled in where known:
#
#   torch:
#     valves:
#       torch_gox_mpv: 1                     # NO/NC: TBD
#       torch_gox_post_mpv_vent: 2           # NO/NC: TBD
#       torch_methane_mpv: 3                 # NO/NC: TBD
#       torch_methane_post_mpv_vent: 4       # NO/NC: TBD
#       torch_spark_plug: <TBD -- no channel # assigned yet at all>
#     pts:
#       torch_pt_1: 7
#       torch_pt_2: 8
#       torch_pt_3: 15   # exists now, unused above -- purpose/role TBD
#     tcs:
#       methane_pre_injector_tc: 1  # Torch Body
#       gox_pre_injector_tc: 2      # Torch Plate
#
#   variables:
#     mpv_delay                  # ms -- still "XX", unset
#     spark_attempt_duration: 3  # s -- REAL, also doubles as ignition-confirm timeout
#     burn_duration: 3           # s -- REAL
#     ignition_lower_threshold: 165  # psig -- REAL
#     ignition_upper_threshold: 242  # psig -- REAL
#     ignition_confirmation_time     # ms -- still "XX", unset
# ---------------------------------------------------------------------------