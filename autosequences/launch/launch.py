#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax==0.46.0",
#     "yaspin",
#     "termcolor",
#     "pyyaml",
#     "prompt-toolkit",
# ]
# ///

from termcolor import colored
from yaspin import yaspin

# fun spinner while we load packages
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

# 3rd party modules
from synnax.control.controller import Controller
import synnax as sy

# our modules
from autosequence_utils import (
    Phase,
    Autosequence,
    Config,
    average_ch,
    SequenceAborted,
    sensor_vote,
)

# standard modules
import argparse
import time

REFRESH_RATE: int = 50  # Hz


# CLI argument parser
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="The autosequence for preparring Limeight for launch!"
    )
    parser.add_argument(
        "-m",
        "--config",
        help="The file to use for channel config",
        default="config.yaml",
        type=str,
    )
    parser.add_argument(
        "-c",
        "--cluster",
        help="Specify a Synnax cluster to connect to",
        default="synnax.masa.engin.umich.edu",
        type=str,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Shold the program output extra debugging information",
        action="store_true",
    )  # Positional argument
    args: argparse.Namespace = parser.parse_args()
    # check that if there was an alternate config file given, that it is at least a .yaml file
    if args.config != "config.yaml":
        if args.config.endswith(".yaml"):
            if args.verbose:
                print(colored(f"Using config from file: {args.config}", "yellow"))
        else:
            raise Exception(
                f"Invalid specified config file: {args.config}, must be .yaml file"
            )
    return args


# Background task to always check for certain abort cases
def background_thread(auto: Autosequence) -> None:
    print(" > Background task started...")
    ctrl: Controller = auto.ctrl
    config: Config = auto.config

    copv_pts: list[str] = [
        config.get_pt("COPV_PT_1"),
        config.get_pt("COPV_PT_2"),
        config.get_pt("Fuel_TPC_Inlet_PT"),
    ]

    press_fill_iso: str = config.get_vlv("Press_Fill_Iso")
    press_isos: list[str] = [
        config.get_vlv("Press_Iso_1"),
        config.get_vlv("Press_Iso_2"),
        config.get_vlv("Press_Iso_3"),
    ]

    copv_abort_threshold: float = config.get_var("copv_pressure_max")

    copv_pressure = average_ch(
        window=REFRESH_RATE / 2
    )  # 0.5 second window (NOTE: adjust as needed depending on acceptable lag)

    while not auto.abort_flag.is_set():
        time.sleep(0.1)  # yeild thread 
        # NOTE: using time.sleep() is fine because we have no conditions to check like in phases
        copv_pressure.add(
            value=sensor_vote(
                ctrl=ctrl,
                channels=copv_pts,
                threshold=50,  # arbitrary threshold for voting
            )
        )
        if copv_pressure.get() >= copv_abort_threshold:
            print(" > COPV Exceeding max pressure! Aborting...")
            auto.raise_abort()
            # Some of these conditions may already happen in the phase aborts, but just to be safe
            ctrl[press_fill_iso] = False  # close fill iso
            for press_iso in press_isos:  # close all bottles
                ctrl[press_iso] = False
            return


# Press fill phase
def press_fill(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    press_fill_iso: str = config.get_vlv("Press_Fill_Iso")
    press_isos: list[str] = [
        config.get_vlv("Press_Iso_1"),
        config.get_vlv("Press_Iso_2"),
        config.get_vlv("Press_Iso_3"),
    ]

    copv_pts: list[str] = [
        config.get_pt("COPV_PT_1"),
        config.get_pt("COPV_PT_2"),
        config.get_pt("Fuel_TPC_Inlet_PT"),
    ]

    copv_pressure = average_ch(
        window=REFRESH_RATE / 2
    )  # 0.5 second window (NOTE: adjust as needed depending on acceptable lag)

    bottle_pts: list[str] = [
        config.get_pt("Bottle_1_PT"),
        config.get_pt("Bottle_2_PT"),
        config.get_pt("Bottle_3_PT"),
    ]

    press_rate_1: float = config.get_var("press_rate_1")
    press_rate_2: float = config.get_var("press_rate_2")
    press_rate_1_ittrs: int = config.get_var("press_rate_1_ittrs")
    copv_cooldown_time: float = config.get_var("copv_cooldown_time")

    # TODO: Make most prints in verbose output mode only

    try:  # Normal operation
        print(" > Starting press fill phase...")
        ctrl[press_fill_iso] = True

        # For each bottle
        for i in range(len(bottle_pts)):
            print(f"  > Filling from bottle {i + 1}")

            # Press rate 1 fill
            for j in range(press_rate_1_ittrs):
                print(f"   > Pressurizing at rate 1, itteration {j + 1}...")

                starting_pressure: float = phase.avg_and_vote_for(
                    ctrl=ctrl,
                    channels=copv_pts,
                    threshold=press_rate_1,
                    averaging_time=1.0,
                )
                target_pressure: float = starting_pressure + press_rate_1
                print(f"    > Starting pressure: {starting_pressure:.2f} psi")
                print(f"    > Target pressure: {target_pressure:.2f} psi")

                target_time: sy.TimeStamp = (
                    sy.TimeStamp.now() + sy.TimeSpan.from_seconds(copv_cooldown_time)
                )

                ctrl[press_isos[i]] = True  # open bottle iso

                # Wait until the averaged COPV pressure reaches the target pressure OR it has been more than 1 minute
                phase.wait_until(
                    cond=lambda c: copv_pressure.add_and_get(
                        value=sensor_vote(
                            ctrl=c, channels=copv_pts, threshold=press_rate_1
                        )
                    )
                    >= target_pressure
                    or sy.TimeStamp.now() >= target_time
                )

                ctrl[press_isos[i]] = False  # close bottle iso

                # Make sure that any remaining time has elapsed before starting the next itteration
                phase.wait_until(cond=lambda c: sy.TimeStamp.now() >= target_time)

            # Until bottle equalization
            while True:
                print("TBD")
                phase.sleep(1)
                pass

        ctrl[press_fill_iso] = False  # close fill iso

    except Exception as e:  # Abort case
        print("\n > Aborting press fill phase due to exception:", e)
        ctrl[press_fill_iso] = False  # close fill iso
        for press_iso in press_isos:  # close all bottles
            ctrl[press_iso] = False
    return


# Example used for automated abort cases, obviously don't include in final release
def bad_press_fill(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    press_fill_iso: str = config.get_vlv("Press_Fill_Iso")
    press_isos: list[str] = [
        config.get_vlv("Press_Iso_1"),
        config.get_vlv("Press_Iso_2"),
        config.get_vlv("Press_Iso_3"),
    ]

    try:  # Normal operation
        while True:
            phase.sleep(0.1)
            ctrl[press_fill_iso] = True
            for i in range(len(press_isos)):
                ctrl[press_isos[i]] = True  # open bottle iso
    except Exception as e:  # Abort case
        print(" > Aborting press fill phase due to exception:", e)
        ctrl[press_fill_iso] = False  # close fill iso
        for press_iso in press_isos:  # close all bottles
            ctrl[press_iso] = False


# Abort case which is ran under any abort - is the last thing ran under Ctrl+C
def global_abort(auto: Autosequence) -> None:
    ctrl: Controller = auto.ctrl
    config: Config = auto.config

    copv_vent: str = config.get_vlv("COPV_Vent")
    press_fill_vent: str = config.get_vlv("Press_Fill_Vent")

    confirm: str = ""
    try:
        confirm = input("Vent? Y/N: ").lower()
    except KeyboardInterrupt:
        print("\n > Taking Ctrl+C as confirmation to vent")
        confirm = "y"
    finally:  # in any case
        if confirm == "y" or confirm == "yes":
            print(" > Venting...")
            ctrl[copv_vent] = True  # open vent
            ctrl[press_fill_vent] = True  # open vent
    return


def main() -> None:
    args: argparse.Namespace = parse_args()
    config: Config = Config(filepath=args.config)
    cluster: str = args.cluster

    # Make Autosequence object, also connects to Synnax & other checks
    auto: Autosequence = Autosequence(
        name="Limelight Launch Autosequence",
        cluster=cluster,
        config=config,
        global_abort=global_abort,
        background_thread=background_thread,
    )

    # Define and add each phase to the autosequence
    press_fill_phase: Phase = Phase(
        name="Press Fill", func=press_fill, ctrl=auto.ctrl, config=config
    )

    auto.add_phase(press_fill_phase)

    bad_press_fill_phase: Phase = Phase(
        name="Bad Press Fill", func=bad_press_fill, ctrl=auto.ctrl, config=config
    )

    auto.add_phase(bad_press_fill_phase)

    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports and setup

    # Run the autosequence
    auto.run()

    print(" > Autosequence has terminated, have a great flight!")
    return


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # make sure we stop the spinner on any exception (it prevents the program from exiting cleanly)
        spinner.stop()
        raise (e)
