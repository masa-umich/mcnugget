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
import math


#CHANGEABLE CONSTANTS
REFRESH_RATE: int = 50  # Hz


# CLI argument parser
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="The autosequence for preparing Limeight for launch!"
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
        config.get_vlv("ox_vent"),
        config.get_vlv("fuel_vent"),
    ]

    valves_to_close: list[str] = [
        config.get_vlv("ox_mpv"),
        config.get_vlv("fuel_mpv"),
        config.get_vlv("Press_Iso_1"),
        config.get_vlv("Press_Iso_2"),
        config.get_vlv("Press_Iso_3"),
        config.get_vlv("Press_Iso_4"),
        config.get_vlv("ox_fill_valve"),
        config.get_vlv("ox_dome_iso"),
        config.get_vlv("fuel_dome_iso"),
    ]

    press_fill_vent: str = config.get_vlv("Press_Fill_Vent")
    press_fill_iso: str = config.get_vlv("Press_Fill_Iso")
    press_fill_vent_time: int = config.get_var("press_fill_vent_time")

    copv_vent: str = config.get_vlv("COPV_Vent")

    confirm: str = "" 

    try:
        for valve in valves_to_close:
            if config.is_vlv_nc(valve):
                ctrl[valve] = False
            else:
                ctrl[valve] = True

        for vent in vents:
            if config.is_vlv_nc(vent):
                ctrl[vent] = True
            else:
                ctrl[vent] = False

        log(f"Please wait {press_fill_vent_time} seconds to vent press fill safely...")
        log("Or, press Ctrl+C again to close press fill iso immediately")
        open_vlv(ctrl, press_fill_vent)
        try:
            time.sleep(press_fill_vent_time)
        except KeyboardInterrupt:
            log("Ctrl+C during press fill vent delay — continuing abort")

        close_vlv(ctrl, press_fill_iso)

        try:
            confirm = input("Vent COPV? Y/N: ").lower()
        except KeyboardInterrupt:
            log("Taking Ctrl+C as confirmation to vent")

    finally:
        if confirm in ("y", "yes"):
            open_vlv(ctrl, copv_vent)
            log("COPV Vent opened.")


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
        config.get_vlv("Press_Iso_4"),
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


def press_iteration(
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

    # Make sure that any remaining time has elapsed before starting the next iteration
    phase.wait_until(cond=lambda c: sy.TimeStamp.now() >= target_time)
    phase.log(f"  Cooldown time elapsed, moving to next iteration")


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
        config.get_vlv("Press_Iso_4"),
    ]

    bottle_pts: list[str] = [
        config.get_pt("Bottle_1_PT"),
        config.get_pt("Bottle_2_PT"),
        config.get_pt("Bottle_3_PT"),
        config.get_pt("Bottle_4_PT"),
    ]

    copv_pressure = average_ch(
        window=REFRESH_RATE / 2
    )  # 0.5 second window (NOTE: adjust as needed depending on acceptable lag)

    phase.log(f"Starting press fill for bottle {bottle}")

    phase.log(f"Opening press fill iso")
    open_vlv(ctrl, press_fill_iso)

    # Press rate 1 fill
    for i in range(press_rate_1_ittrs):
        phase.log(f" Pressurizing at rate 1 (iteration {i + 1})")
        press_iteration(
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
        phase.log(f" Pressurizing at rate 2 (iteration {press_rate_2_ittrs})")

        press_iteration(
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
            phase.log("  Bottle equalization reached, ending pressurization", "green", True)
            phase.log(f"Closing press fill iso")
            close_vlv(ctrl, press_fill_iso)
            phase.log(f"Completed press fill for bottle {bottle}")
            return False
        else:
            phase.log("  Bottle not yet equalized, continuing pressurization")
        # Check for COPV pressure target reached
        if copv_current_pressure >= (copv_pressure_target - copv_pressure_margin):
            phase.log("  COPV pressure target reached, ending pressurization", "green", True)
            phase.log(f"Closing press fill iso")
            close_vlv(ctrl, press_fill_iso)
            return True


def press_fill_1(phase: Phase) -> None:
    press_fill(phase=phase, bottle=1)


def press_fill_2(phase: Phase) -> None:
    press_fill(phase=phase, bottle=2)

def press_fill_3(phase: Phase) -> None:
    press_fill(phase=phase, bottle=3)

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
            phase.log(f"COPV below target pressure, opening Press Iso 4 & Press Fill Iso to TPC")
            open_vlv(ctrl, config.get_vlv("Press_Iso_4")) #NOTE: change if we have 3 bottles vs 4
            open_vlv(ctrl, config.get_vlv("Press_Fill_Iso"))
        elif current_pressure >= copv_pressure_target:
            phase.log(f"COPV at or above target pressure, closing Press Iso 4 & Press Fill Iso")
            close_vlv(ctrl, config.get_vlv("Press_Iso_4"))
            close_vlv(ctrl, config.get_vlv("Press_Fill_Iso"))
        phase.sleep(0.1)


def press_fill_4(phase: Phase) -> None:
    tpc: bool = press_fill(phase=phase, bottle=4)
    if tpc:
        phase.log("COPV filled to target pressure, now continuing TPC of COPV")
        tpc_copv(phase=phase)

def press_fill_abort(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    press_fill_iso: str = config.get_vlv("Press_Fill_Iso")
    press_isos: list[str] = [
        config.get_vlv("Press_Iso_1"),
        config.get_vlv("Press_Iso_2"),
        config.get_vlv("Press_Iso_3"),
        config.get_vlv("Press_Iso_4"),
    ]

    phase.log("Halting press fill, closing all relevant valves")
    close_vlv(ctrl, press_fill_iso)
    for press_iso in press_isos:
        close_vlv(ctrl, press_iso)
    return

def ox_fill(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    ox_fill_target = config.get_var("ox_fill_target")
    ox_fill_margin = config.get_var("ox_fill_margin")
    ox_fill_lower_bound = ox_fill_target - ox_fill_margin
    ox_fill_upper_bound = ox_fill_target + ox_fill_margin
    ox_fill = config.get_vlv("ox_fill_valve")
    ox_level_sensor = config.get_pt("ox_level_sensor")

    ox_level = average_ch(
        window=REFRESH_RATE / 2
    )  # 0.5 second window (NOTE: adjust as needed depending on acceptable lag)
    ox_level.add(ctrl.get(ox_level_sensor)) # initialize current level

    while True:
        ox_level.add(ctrl.get(ox_level_sensor)) # update current level
        if ox_level.get() < ox_fill_lower_bound:
            phase.log(f"Current Ox level of {ox_level.get()} psid < {ox_fill_lower_bound} psid lower bound")
            open_vlv(ctrl, ox_fill)
            phase.log(f"Opening Ox Fill Valve until Ox Level >= {ox_fill_upper_bound} psid")

            # Wait until we have reached the target level
            while ox_level.add_and_get(ctrl.get(ox_level_sensor)) <= ox_fill_upper_bound:
                phase.sleep(0.10) # yield thread
                if open_vlv(ctrl, ox_fill):
                    phase.log(f"Re-opening Ox Fill Valve, resuming filling...")

            phase.log(f"Target Ox level reached: {ox_level.get()}, closing Ox Fill Valve")
            close_vlv(ctrl, ox_fill)
            phase.log("Continuing to monitor Ox level...")
        phase.sleep(0.01) # yield thread
        
def ox_fill_safe(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config
    ox_fill: str = config.get_vlv("ox_fill_valve")

    phase.log("Safing Ox Fill Phase - Closing Ox Fill Valve")
    close_vlv(ctrl, ox_fill)
    return

def pre_press(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    ox_pre_press_target = config.get_var("ox_pre_press_target")
    ox_pre_press_margin = config.get_var("ox_pre_press_margin")
    ox_pre_press_lower_bound = ox_pre_press_target - ox_pre_press_margin
    ox_pre_press_upper_bound = ox_pre_press_target + ox_pre_press_margin
    
    ox_pre_press = config.get_vlv("ox_pre_press")

    ox_tank_pts: list[str] = [
        config.get_pt("ox_tank_pt_1"),
        config.get_pt("ox_tank_pt_2"),
    ]
    
    ox_tank_pressure = average_ch(
        window=REFRESH_RATE / 2
    )  # 0.5 second window (NOTE: adjust as needed depending on acceptable lag)

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
            while True:
                current_pressure = ox_tank_pressure.add_and_get(
                    value=sensor_vote(ctrl=ctrl, channels=ox_tank_pts, threshold=50)
                )
                if current_pressure >= ox_pre_press_upper_bound:
                    break
                phase.sleep(0.10)  # yield thread
                if open_vlv(ctrl, ox_pre_press):
                    phase.log("Re-opening Ox Pre-Press Valve, resuming pressurization...")
            
            phase.log(f"Upper Bound Ox pressure reached: {current_pressure}, closing Ox Pre-Press")
            close_vlv(ctrl, ox_pre_press)
            phase.log("Continuing to monitor Ox pressure...")
        phase.sleep(0.01) # yield thread


def pre_press_safe(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config
    ox_pre_press = config.get_vlv("ox_pre_press")

    close_vlv(ctrl, ox_pre_press)
    phase.log("Safing Pre-Press Phase - Closing Ox Pre-Press Valve")

def qd_disconnect(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    ox_fill_qd_pilot: str = config.get_vlv("ox_fill_qd_pilot")
    ox_pre_press_qd_pilot: str = config.get_vlv("ox_pre_press_qd_pilot")
    copv_fill_qd_pilot: str = config.get_vlv("copv_fill_qd_pilot")

    press_fill_vent_time: int = config.get_var("press_fill_vent_time")

    press_isos: list[str] = [
        config.get_vlv("Press_Iso_1"),
        config.get_vlv("Press_Iso_2"),
        config.get_vlv("Press_Iso_3"),
        config.get_vlv("Press_Iso_4"),
    ]
    press_fill_iso: str = config.get_vlv("Press_Fill_Iso")
    press_fill_vent: str = config.get_vlv("Press_Fill_Vent")

    phase.log("Input enter to disconnect ox fill QD")
    phase.wait_for_input()
    while(phase._wait.is_set()):
        phase.sleep(0.1)
    open_vlv(ctrl, ox_fill_qd_pilot)
    phase.log("Ox fill QD disconnected")
    phase.log("Input enter to disconnect ox pre-press QD") #NOTE: add venting then wait before QD
    phase.wait_for_input()
    while(phase._wait.is_set()):
        phase.sleep(0.1)
    open_vlv(ctrl, ox_pre_press_qd_pilot)
    phase.log("Ox pre-press QD disconnected")
    phase.log("Input enter to initiate COPV fill QD disconnect sequence")
    phase.wait_for_input()
    while(phase._wait.is_set()):
        phase.sleep(0.1)
    phase.log("Closing all press isos...")
    for iso in press_isos:
        close_vlv(ctrl, iso)
    phase.log("Opening press fill iso...")
    open_vlv(ctrl, press_fill_iso)
    phase.log(f"Opening press fill vent for {press_fill_vent_time} seconds...")
    open_vlv(ctrl, press_fill_vent)
    phase.sleep(press_fill_vent_time)  # wait 5 seconds to ensure full venting
    phase.log("Closing press fill vent and iso...")
    close_vlv(ctrl, press_fill_vent)
    close_vlv(ctrl, press_fill_iso)
    phase.log("Disconnecting COPV fill QD...")
    open_vlv(ctrl, copv_fill_qd_pilot)
    phase.log("COPV fill QD disconnected")
    phase.log("QD disconnection phase complete","green",True)
    return


def coldflow(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    handoff: str = config.get_vlv("handoff")

    phase.log("Hit 'enter' to start coldflow sequence")
    phase.wait_for_input()
    
    while(phase._wait.is_set()):
        phase.sleep(0.1)
    phase.log("Beginning coldflow sequence...","green",True)
    
    target_time: sy.TimeStamp = sy.TimeStamp.now() + sy.TimeSpan.from_seconds(8.0) #time of handoff
    igniter_start_time: sy.TimeStamp = target_time - sy.TimeSpan.from_seconds(4.0) #time to prompt for igniter light
    times_shown = set()
    igniter_prompted: bool = False
    while True:
        phase.sleep(0)
        now: sy.TimeStamp = sy.TimeStamp.now()
        if now >= target_time and phase._wait.is_set():
            phase.log("T-2")
            phase.log("Coldflow aborted. No ignition.","red",True)
            phase.stop_waiting_for_input()
            #NOTE: global abort
            break
        elif now>= target_time:
            phase.log("Ignition confirmed. Handing off...","green",True)
            phase.log("Opening handoff valve...")
            open_vlv(ctrl, handoff)
            phase.log("Launch autosequence complete.","green",True)
            break
        if now >= igniter_start_time and not igniter_prompted:
            phase.log("Press 'enter' to confirm smoke...","yellow",True)
            phase.wait_for_input()
            igniter_prompted = True
        remaining_span = sy.TimeSpan(target_time - now)
        remaining_seconds: float | None = sy.TimeSpan.to_seconds(remaining_span)
        remaining_seconds_int = int(math.ceil(remaining_seconds))
        if remaining_seconds_int not in times_shown:
            phase.log(f"T-{remaining_seconds_int + 2}")
            times_shown.add(remaining_seconds_int)
    return

def coldflow_full(phase: Phase) -> None:
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    first_mpv_time: float = config.get_var("first_mpv_time")  # seconds before ignition to open first mpv
    first_mpv: str = config.get_var("first_mpv") # Which MPV to open first, ox or fuel
    ox_iso_time: float = config.get_var("ox_iso_time")  # seconds before ignition to open ox iso
    fuel_iso_time: float = config.get_var("fuel_iso_time")  # seconds before ignition to open fuel iso

    if(first_mpv.lower() == "ox"):
        second_mpv: str = "fuel" # Which MPV to open second, ox or fuel
    elif (first_mpv.lower() == "fuel"):
        second_mpv: str = "ox" # Which MPV to open second, ox or fuel
    else:
        phase.log(f"Invalid first_mpv value: {first_mpv}. Must be 'ox' or 'fuel'. Aborting coldflow.","red",True)
        #NOTE: What to do here?
        return
    
    #track state variables
    times_shown = set() # to track which times have been shown in countdown
    first_mpv_opened: bool = False
    second_mpv_opened: bool = False
    igniter_prompted: bool = False
    igniter_confirmed: bool = False
    first_iso_opened: bool = False
    second_iso_opened: bool = False

    phase.log("Hit 'enter' to start coldflow sequence")
    phase.wait_for_input()
    
    while(phase._wait.is_set()):
        phase.sleep(0.1)
    phase.log("Beginning coldflow sequence...","green",True)
    
    target_time: sy.TimeStamp = sy.TimeStamp.now() + sy.TimeSpan.from_seconds(10.0) #time of ignition
    igniter_start_time: sy.TimeStamp = target_time - sy.TimeSpan.from_seconds(6.0) #time to prompt for igniter light
    igniter_end_time: sy.TimeStamp = target_time - sy.TimeSpan.from_seconds(2.0) #time to stop waiting for igniter light
    first_mpv_open_time: sy.TimeStamp = target_time - sy.TimeSpan.from_seconds(first_mpv_time)

    #Figure out iso open times
    first_iso_open_time: sy.TimeStamp
    second_iso_open_time: sy.TimeStamp
    if first_mpv == "ox":
        first_iso_open_time = first_mpv_open_time - sy.TimeSpan.from_seconds(ox_iso_time)
        second_iso_open_time = target_time - sy.TimeSpan.from_seconds(fuel_iso_time)
    else: #first_mpv == "fuel"
        first_iso_open_time = first_mpv_open_time - sy.TimeSpan.from_seconds(fuel_iso_time)
        second_iso_open_time = target_time - sy.TimeSpan.from_seconds(ox_iso_time)

    while True:
        phase.sleep(0)
        now: sy.TimeStamp = sy.TimeStamp.now()

        if now >= igniter_end_time and phase._wait.is_set():
            phase.log("T-2")
            phase.log("Coldflow aborted. No ignition.","red",True)
            phase.stop_waiting_for_input()
            #NOTE: global abort
            break
        elif now>= igniter_end_time and not igniter_confirmed:
            phase.log("Ignition confirmed. Continuing with coldflow...","green",True)
            igniter_confirmed = True

        if now >= igniter_start_time and not igniter_prompted:
            phase.log("Press 'enter' to confirm smoke...","yellow",True)
            phase.wait_for_input()
            igniter_prompted = True

        if now >= first_iso_open_time and not first_iso_opened:
            phase.log(f"Opening {first_mpv.upper()} ISO...")
            open_vlv(ctrl, config.get_vlv(f"{first_mpv}_dome_iso"))
            first_iso_opened = True

        if now >= second_iso_open_time and not second_iso_opened:
            phase.log(f"Opening {second_mpv.upper()} ISO...")
            open_vlv(ctrl, config.get_vlv(f"{second_mpv}_dome_iso"))
            second_iso_opened = True

        if now >= first_mpv_open_time and not first_mpv_opened:
            phase.log(f"Opening {first_mpv.upper()} MPV...")
            open_vlv(ctrl, config.get_vlv(f"{first_mpv}_mpv"))
            first_mpv_opened = True

        if now >= target_time and not second_mpv_opened:
            phase.log(f"Opening {second_mpv.upper()} MPV...")
            open_vlv(ctrl, config.get_vlv(f"{second_mpv}_mpv"))
            second_mpv_opened = True
            phase.log("IGNITION.","red",True)
            post_ignition_sequence(phase)
            phase.log("Launch autosequence complete.","green",True)
            break

        remaining_span = sy.TimeSpan(target_time - now)
        remaining_seconds: float | None = sy.TimeSpan.to_seconds(remaining_span)
        remaining_seconds_int = int(math.ceil(remaining_seconds))
        if remaining_seconds_int not in times_shown:
            phase.log(f"T-{remaining_seconds_int}")
            times_shown.add(remaining_seconds_int)
                  
    return

def post_ignition_sequence(phase: Phase) -> None:
    
    ctrl: Controller = phase.ctrl
    config: Config = phase.config

    vents: list[str] = [
        config.get_vlv("Press_Fill_Vent"),
        config.get_vlv("ox_vent"),
        config.get_vlv("fuel_vent"),
    ]

    valves_to_close: list[str] = [
        config.get_vlv("ox_dome_iso"),
        config.get_vlv("fuel_dome_iso"),
        config.get_vlv("ox_mpv"),
        config.get_vlv("fuel_mpv"),
    ]

    duration: int = config.get_var("duration")  # Duration to keep MPVs open after ignition in seconds

    coldflow_start_time: sy.TimeStamp = sy.TimeStamp.now()
    last_shown: int = -1

    end_time = coldflow_start_time + sy.TimeSpan.from_seconds(duration)

    coldflow_start_time: sy.TimeStamp = sy.TimeStamp.now()
    last_shown: int = -1
    
    # Calculate the end time once
    end_time = coldflow_start_time + sy.TimeSpan.from_seconds(duration)

    while sy.TimeStamp.now() < end_time:
        phase.sleep(0.05) 
  
        now: sy.TimeStamp = sy.TimeStamp.now() 
        span_passed = sy.TimeSpan(now - coldflow_start_time)
        seconds_passed_float: float | None = sy.TimeSpan.to_seconds(span_passed)
        seconds_passed_int = int(seconds_passed_float)
        
        if seconds_passed_int != last_shown:
            phase.log(f"T+{seconds_passed_int}")
            last_shown = seconds_passed_int

    phase.log("Duration elapsed, safing system...","yellow")

    for valve in valves_to_close:
        if config.is_vlv_nc(valve):
            ctrl[valve] = False
        else:
            ctrl[valve] = True

    for vent in vents:
        if config.is_vlv_nc(vent):
            ctrl[vent] = True
        else:
            ctrl[vent] = False

    phase.log("System safed.","green",True)

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
    press_fill_1_phase: Phase = Phase(
        name="Press Fill 1", ctrl=auto.ctrl, config=config, main_func=press_fill_1, safe_func=press_fill_abort
    )
    auto.add_phase(press_fill_1_phase)

    press_fill_2_phase: Phase = Phase(
        name="Press Fill 2", ctrl=auto.ctrl, config=config, main_func=press_fill_2, safe_func=press_fill_abort
    )
    auto.add_phase(press_fill_2_phase)

    press_fill_3_phase: Phase = Phase(
        name="Press Fill 3", ctrl=auto.ctrl, config=config, main_func=press_fill_3, safe_func=press_fill_abort
    )
    auto.add_phase(press_fill_3_phase)

    press_fill_4_phase: Phase = Phase(
        name="Press Fill 4", ctrl=auto.ctrl, config=config, main_func=press_fill_4, safe_func=press_fill_abort
    )
    auto.add_phase(press_fill_4_phase)

    ox_fill_phase: Phase = Phase(
        name="Ox Fill", ctrl=auto.ctrl, config=config, main_func=ox_fill, safe_func=ox_fill_safe
    )
    auto.add_phase(ox_fill_phase)    

    pre_press_phase: Phase = Phase(
        name="Pre Press", ctrl=auto.ctrl, config=config, main_func=pre_press, safe_func=pre_press_safe
    )
    auto.add_phase(pre_press_phase)

    qd_disconnect_phase: Phase = Phase(
        name="QD", ctrl=auto.ctrl, config=config, main_func=qd_disconnect
    )
    auto.add_phase(qd_disconnect_phase)

    # coldflow_phase: Phase = Phase(
    #     name="Coldflow", ctrl=auto.ctrl, config=config, main_func=coldflow
    # )
    # auto.add_phase(coldflow_phase)

    coldflow_full_phase: Phase = Phase(
        name="Coldflow Full", ctrl=auto.ctrl, config=config, main_func=coldflow_full
    )
    auto.add_phase(coldflow_full_phase)

    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports and setup

    # auto.init_valves() # initialize valves to default states

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
