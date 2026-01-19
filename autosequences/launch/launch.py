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
    log,
    sensor_vote,
    write_logs_to_file,
    open_vlv,
    close_vlv,
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
        "-l",
        "--log",
        help="Specify a log file to write logs to at the end of the autosequence",
        default="",
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


# Abort case which is ran under any abort - is the last thing ran under Ctrl+C
def global_abort(auto: Autosequence) -> None:
    ctrl: Controller = auto.ctrl
    config: Config = auto.config

    vents: list[str] = [
        config.get_vlv("COPV_Vent"),
        config.get_vlv("Press_Fill_Vent"),
    ]

    confirm: str = ""
    try:
        confirm = input("Vent? Y/N: ").lower()
    except KeyboardInterrupt:
        log("Taking Ctrl+C as confirmation to vent")
        confirm = "y"
    finally:  # in any case
        if confirm == "y" or confirm == "yes":
            log("Venting...")
            for vent in vents:
                if config.is_vlv_nc(vent):
                    ctrl[vent] = True
                else:
                    ctrl[vent] = False
            log("Vents opened")
    return


# Background task to always check for certain abort cases
def background_thread(auto: Autosequence) -> None:
    log("Background task started")
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
            log("COPV Exceeding max pressure! Aborting...")
            auto.raise_abort()
            # Some of these conditions may already happen in the phase aborts, but just to be safe
            ctrl[press_fill_iso] = False  # close fill iso
            for press_iso in press_isos:  # close all bottles
                ctrl[press_iso] = False
            return


def press_itteration(
        phase: Phase,
        press_rate: float,
        copv_pressure: average_ch,
        press_iso: str,
        ) -> None:

    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    averaging_time: float = config.get_var("averaging_time")
    copv_cooldown_time: float = config.get_var("copv_cooldown_time")

    copv_pts: list[str] = [
        config.get_pt("COPV_PT_1"),
        config.get_pt("COPV_PT_2"),
        config.get_pt("Fuel_TPC_Inlet_PT"),
    ]

    phase.log(f"  Measuring COPV starting pressure for {averaging_time:.2f} seconds")
    starting_pressure: float = phase.avg_and_vote_for(
        ctrl=ctrl,
        channels=copv_pts,
        threshold=press_rate,
        averaging_time=averaging_time,
    )
    target_pressure: float = starting_pressure + press_rate
    phase.log(f"  Starting pressure: {starting_pressure:.2f} psi")
    phase.log(f"  Target pressure: {target_pressure:.2f} psi")

    target_time: sy.TimeStamp = (
        sy.TimeStamp.now() + sy.TimeSpan.from_seconds(copv_cooldown_time)
    )

    open_vlv(ctrl, press_iso)
    phase.log(f"  Opened {press_iso}")
    
    # Wait until the averaged COPV pressure reaches the target pressure OR it has been more than 1 minute
    phase.wait_until(
        cond=lambda c: copv_pressure.add_and_get(
            value=sensor_vote(
                ctrl=c, channels=copv_pts, threshold=press_rate
            )
        )
        >= target_pressure
        or sy.TimeStamp.now() >= target_time
    )

    phase.log(f"  Target pressure reached or timeout elapsed, final COPV pressure: {copv_pressure.get():.2f} psi")
    close_vlv(ctrl, press_iso)
    phase.log(f"  Closed {press_iso}")

    # Make sure that any remaining time has elapsed before starting the next itteration
    phase.wait_until(cond=lambda c: sy.TimeStamp.now() >= target_time)
    phase.log(f"  Cooldown time elapsed, moving to next itteration")


def press_fill(phase: Phase, bottle: int) -> bool:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    press_rate_1: float = config.get_var("press_rate_1")
    press_rate_2: float = config.get_var("press_rate_2")
    press_rate_1_ittrs: int = config.get_var("press_rate_1_ittrs")
    bottle_equalization_threshold: float = config.get_var("bottle_equalization_threshold")
    copv_pressure_target: float = config.get_var("copv_pressure_target")
    copv_pressure_margin: float = config.get_var("copv_pressure_margin")

    press_fill_iso: str = config.get_vlv("Press_Fill_Iso")
    press_isos: list[str] = [
        config.get_vlv("Press_Iso_1"),
        config.get_vlv("Press_Iso_2"),
        config.get_vlv("Press_Iso_3"),
    ]

    bottle_pts: list[str] = [
        config.get_pt("Bottle_1_PT"),
        config.get_pt("Bottle_2_PT"),
        config.get_pt("Bottle_3_PT"),
    ]

    copv_pressure = average_ch(
        window=REFRESH_RATE / 2
    )  # 0.5 second window (NOTE: adjust as needed depending on acceptable lag)

    phase.log(f"Starting press fill for bottle {bottle}")

    phase.log(f"Opening press fill iso")
    open_vlv(ctrl, press_fill_iso)

    # Press rate 1 fill
    for i in range(press_rate_1_ittrs):
        phase.log(f" Pressurizing at rate 1 (itteration {i + 1})")
        press_itteration(
            phase=phase,
            press_rate=press_rate_1,
            copv_pressure=copv_pressure,
            press_iso=press_isos[bottle - 1]
        )

    phase.log("Completed first pressurization stage, moving to rate 2")

    # Until bottle equalization
    press_rate_2_ittrs: int = 0
    while True:
        press_rate_2_ittrs += 1
        phase.log(f" Pressurizing at rate 2 (itteration {press_rate_2_ittrs})")

        press_itteration(
            phase=phase,
            press_rate=press_rate_2,
            copv_pressure=copv_pressure,
            press_iso=press_isos[bottle - 1]
        )

        # Check for bottle equalization
        phase.log(f"  Checking for bottle equalization")
        bottle_pressure: float = phase.avg_and_vote_for(
            ctrl=phase.ctrl,
            channels=[bottle_pts[bottle - 1]],
            threshold=press_rate_2,
            averaging_time=1.0,
        )
        copv_current_pressure: float = copv_pressure.get()
        phase.log(f"  Bottle pressure: {bottle_pressure:.2f} psi")
        phase.log(f"  COPV pressure: {copv_current_pressure:.2f}")
        if abs(copv_current_pressure - bottle_pressure) <= bottle_equalization_threshold:
            phase.log("  Bottle equalization reached, ending pressurization")
            phase.log(f"Closing press fill iso")
            close_vlv(ctrl, press_fill_iso)
            phase.log(f"Completed press fill for bottle {bottle}")
            return False
        else:
            phase.log("  Bottle not yet equalized, continuing pressurization")
        # Check for COPV pressure target reached
        if copv_current_pressure >= (copv_pressure_target - copv_pressure_margin):
            phase.log("  COPV pressure target reached, ending pressurization")
            phase.log(f"Closing press fill iso")
            close_vlv(ctrl, press_fill_iso)
            return True


def press_fill_1(phase: Phase) -> None:
    try:  # Normal operation
        press_fill(phase=phase, bottle=1)
    except Exception as e:  # Abort case
        phase.log(f"Aborting due to exception: {e}")
        press_fill_abort(phase=phase)
    return


def press_fill_2(phase: Phase) -> None:
    try:  # Normal operation
        press_fill(phase=phase, bottle=2)
    except Exception as e:  # Abort case
        phase.log(f"Aborting due to exception: {e}")
        press_fill_abort(phase=phase)
    return


def tpc_copv(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    copv_pts: list[str] = [
        config.get_pt("COPV_PT_1"),
        config.get_pt("COPV_PT_2"),
        config.get_pt("Fuel_TPC_Inlet_PT"),
    ]

    copv_pressure_target: float = config.get_var("copv_pressure_target")
    copv_pressure_margin: float = config.get_var("copv_pressure_margin")

    copv_pressure = average_ch(
        window=REFRESH_RATE / 2
    )  # 0.5 second window (NOTE: adjust as needed depending on acceptable lag)

    # Try to keep COPV at target pressure
    while True:
        current_pressure: float = copv_pressure.add_and_get(
            value=sensor_vote(
                ctrl=ctrl, channels=copv_pts, threshold=1.0
            )
        )
        if current_pressure < (copv_pressure_target - copv_pressure_margin):
            phase.log(f"COPV below target pressure, opening Press Iso 3 & Press Fill Iso to TPC")
            open_vlv(ctrl, config.get_vlv("Press_Iso_3"))
            open_vlv(ctrl, config.get_vlv("Press_Fill_Iso"))
        elif current_pressure >= copv_pressure_target:
            phase.log(f"COPV at or above target pressure, closing Press Iso 3 & Press Fill Iso")
            close_vlv(ctrl, config.get_vlv("Press_Iso_3"))
            close_vlv(ctrl, config.get_vlv("Press_Fill_Iso"))
        phase.sleep(1.0)  # wait 1 second before checking again


def press_fill_3(phase: Phase) -> None:
    try:  # Normal operation
        tpc: bool = press_fill(phase=phase, bottle=3)
        if tpc:
            phase.log("COPV filled to target pressure, now continuing TPC of COPV")
            tpc_copv(phase=phase)
    except Exception as e:  # Abort case
        phase.log(f"Aborting due to exception: {e}")
        press_fill_abort(phase=phase)
    return


def press_fill_abort(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    press_fill_iso: str = config.get_vlv("Press_Fill_Iso")
    press_isos: list[str] = [
        config.get_vlv("Press_Iso_1"),
        config.get_vlv("Press_Iso_2"),
        config.get_vlv("Press_Iso_3"),
    ]

    phase.log("Aborting press fill, closing all relevant valves")
    close_vlv(ctrl, press_fill_iso)
    for press_iso in press_isos:
        close_vlv(ctrl, press_iso)
    return

def ox_fill(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    ox_fill_target = config.get_var("ox_fill_target")
    ox_fill_lower_bound = config.get_var("ox_fill_lower_bound")
    ox_fill = config.get_vlv("ox_fill_valve")
    ox_vent = config.get_vlv("ox_vent")
    fuel_vent = config.get_vlv("fuel_vent")
    ox_level_sensor = config.get_pt("ox_level_sensor")
    ox_level = average_ch(
        window=REFRESH_RATE / 2
    )  # 0.5 second window (NOTE: adjust as needed depending on acceptable lag)
    ox_level.add(ctrl.get(ox_level_sensor)) # initialize current level
    
    try: # Normal operation
        while True:
            ox_level.add(ctrl.get(ox_level_sensor)) # update current level
            if ox_level.get() < ox_fill_lower_bound:
                phase.log(f"Current Ox level of {ox_level.get()} psid < {ox_fill_lower_bound} psid lower bound")
                open_vlv(ctrl, ox_fill)
                phase.log(f"Opening Ox Fill Valve until Ox Level >= {ox_fill_target} psid")

                # Wait until we have reached the target level
                phase.wait_until(cond=lambda ctrl: ox_level.add_and_get(ctrl.get(ox_level_sensor)) >= ox_fill_target)

                phase.log(f"Target Ox level reached: {ox_level.get()}, closing Ox Fill Valve")
                close_vlv(ctrl, ox_fill)
                phase.log("Continuing to monitor Ox level...")
            phase.sleep(0.01) # yield thread
    except:
        close_vlv(ctrl, ox_fill)
        open_vlv(ctrl, ox_vent)
        open_vlv(ctrl, fuel_vent)
        phase.log(f"Ox level: {ox_level.get()} psid")
        phase.log("Aborted, ox fill valve closed, ox vent and fuel vent opened")
        
def pre_press(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    ox_pre_press_target = config.get_var("ox_pre_press_target")
    ox_pre_press_lower_bound = config.get_var("ox_pre_press_lower_bound")
    
    averaging_time: float = config.get_var("averaging_time")

    ox_pre_press = config.get_vlv("ox_pre_press")
    ox_vent = config.get_vlv("ox_vent")
    fuel_vent = config.get_vlv("fuel_vent")

    ox_tank_pts: list[str] = [
        config.get_pt("ox_tank_pt_1"),
        config.get_pt("ox_tank_pt_2"),
    ]
    
    ox_tank_pressure = average_ch(
        window=REFRESH_RATE / 2
    )  # 0.5 second window (NOTE: adjust as needed depending on acceptable lag)

    try: # Normal operation
        while True:
            current_pressure: float = ox_tank_pressure.add_and_get(
                value=sensor_vote(
                    ctrl=ctrl, channels=ox_tank_pts, threshold=1.0
                )
            )
            if current_pressure < ox_pre_press_lower_bound:
                phase.log(f"Current Ox pressure of {current_pressure} psid < {ox_pre_press_lower_bound} psid lower bound")
                open_vlv(ctrl, ox_pre_press)
                phase.log(f"Opening Ox Pre-Press until Ox Pressure >= {ox_pre_press_target} psid")

                # Wait until we have reached the target level
                phase.wait_until(
                    cond=lambda c: ox_tank_pressure.add_and_get(
                        value=sensor_vote(
                            ctrl=c, channels=ox_tank_pts, threshold=50
                        )
                    )
                    >= ox_pre_press_target
                )
                
                phase.log(f"Target Ox pressure reached: {current_pressure}, closing Ox Pre-Press")
                close_vlv(ctrl, ox_pre_press)
                phase.log("Continuing to monitor Ox pressure...")
            phase.sleep(0.01) # yield thread
    except:
        close_vlv(ctrl, ox_pre_press)
        open_vlv(ctrl, ox_vent)
        open_vlv(ctrl, fuel_vent)
        phase.log(f"Ox Tank Pressure: {ox_tank_pressure.get()} psid")
        phase.log("Aborted, ox pre-press valve closed, ox vent and fuel vent opened")

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
    press_fill_1_phase: Phase = Phase(
        name="Press Fill 1", func=press_fill_1, ctrl=auto.ctrl, config=config
    )
    auto.add_phase(press_fill_1_phase)

    press_fill_2_phase: Phase = Phase(
        name="Press Fill 2", func=press_fill_2, ctrl=auto.ctrl, config=config
    )
    auto.add_phase(press_fill_2_phase)

    press_fill_3_phase: Phase = Phase(
        name="Press Fill 3", func=press_fill_3, ctrl=auto.ctrl, config=config
    )
    auto.add_phase(press_fill_3_phase)

    ox_fill_phase: Phase = Phase(
        name="Ox Fill", func=ox_fill, ctrl=auto.ctrl, config=config
    )
    auto.add_phase(ox_fill_phase)    

    pre_press_phase: Phase = Phase(
        name="Pre Press", func=pre_press, ctrl=auto.ctrl, config=config
    )
    auto.add_phase(pre_press_phase)

    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports and setup

    auto.init_valves() # initialize valves to default states

    # Run the autosequence
    auto.run()

    log("Autosequence has terminated, have a great flight!")

    if args.log != "":
        write_logs_to_file(filepath=args.log)
    return


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # make sure we stop the spinner on any exception (it prevents the program from exiting cleanly)
        spinner.stop()
        raise (e)
