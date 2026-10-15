import argparse
from pathlib import Path

import synnax as sy
from mclib import (
    Autosequence,
    Config,
    Phase,
    close_vlv,
    open_vlv,
    sensor_vote_values,
    write_logs_to_file,
)


def parse_args() -> argparse.Namespace: #gotten from old torch.py
    parser = argparse.ArgumentParser(description="Torch igniter countdown autosequence")
    parser.add_argument(
        "-m",
        "--config",
        help="Config file with variables and channel mappings",
        default=str(Path(__file__).parent / "config.yaml"),
        type=str,
    )
    parser.add_argument(
        "-c",
        "--cluster",
        help="Synnax cluster to connect to",
        default="localhost",
        type=str,
    )
    parser.add_argument(
        "-l",
        "--log",
        help="File to append the autosequence logs to when it exits",
        default=None,
        type=str,
    )
    return parser.parse_args()

#Autosequence layout:
#as of 10/4
#T-X1 - Energize spark plug
#T-X2 - Open Torch Ox MPV
#T-X3 - Open Torch Fuel MPV
#T-X4 - De-energize spark plug
#T-X5 - Begin ignition detection
#T-X6 - End ignition detection
#T-X7 - Open Spectre Ox MPV
#T-X8 - Open Spectre Fuel MPV
#T-0 - Engine ignition
#T+X9 - Close Torch MPVs and open Torch Post-MPV Vents

def evaluate_ignition(readings: list[float], vote_threshold: float, lower: float, upper: float) -> tuple[bool, float | None]:
    # this should votes the torch PT readings and checks them against the ignition bounds
    voted: float | None = sensor_vote_values(readings, vote_threshold)
    if voted is None:          
        return False, None
    return (lower <= voted <= upper), voted
    

def countdown(phase: Phase) -> None:
    # Grab the Synnax controller and config from the phase object
    ctrl: sy.Controller = phase.ctrl
    config: Config = phase.config
    
    # Grab the different configuration variables and channel names this phase will need from the config
    countdown_duration: float = config.get_var("countdown_duration")
    spark_on_time: float = config.get_var("spark_on_time")
    fuel_mpv_time: float = config.get_var("fuel_mpv_time")
    ox_mpv_time: float = config.get_var("ox_mpv_time")
    spark_off_time: float = config.get_var("spark_off_time")
    ignition_detection_start: float = config.get_var("ignition_detection_start")
    ignition_detection_end: float = config.get_var("ignition_detection_end")
    torch_off_time: float = config.get_var("torch_off_time")
    burn_duration: float = config.get_var("burn_duration")
    fuel_mpv_ch: str = config.get_vlv("fuel_mpv")
    ox_mpv_ch: str = config.get_vlv("ox_mpv")
    igniter_ch: str = config.get_vlv("igniter")
    ox_post_mpv_vent: str = config.get_vlv("ox_post_mpv_vent")
    fuel_post_mpv_vent: str = config.get_vlv("fuel_post_mpv_vent")
    using_ox: bool = config.get_var("using_ox")
    using_fuel: bool = config.get_var("using_fuel")
    using_spectre: bool = config.get_var("using_spectre")
    lower: float = config.get_var("ignition_lower_threshold")
    upper: float = config.get_var("ignition_upper_threshold")
    vote_threshold: float = config.get_var("vote_threshold")
    enable_ignition_detection_aborts: bool = config.get_var("enable_ignition_detection_aborts")
    torch_pts: list[str] = [
        config.get_pt("torch_pt1"),
        config.get_pt("torch_pt2"),
        config.get_pt("torch_pt3"),
    ]

    order: list[float] = [spark_on_time, ox_mpv_time, fuel_mpv_time, spark_off_time, ignition_detection_start, ignition_detection_end]
    if order != sorted(order) or not (ignition_detection_end < 0 <= torch_off_time):
        phase.log("Timeline out of order, quitting", color="red")
        return
    if torch_off_time - fuel_mpv_time > burn_duration:
        phase.log("Torch burn longer than burn_duration, quitting", color="red")
        return
    if -spark_on_time >= countdown_duration:
        phase.log("spark_on_time is before the countdown starts, quitting", color="red")
        return

    #setting todo of what to turn on + time before T-0
    events: list[tuple[float, str, str, str]] = [(spark_on_time, "Spark plug ON", igniter_ch, "open")]
    if using_ox:
        events.append((ox_mpv_time, "Torch Ox MPV", ox_mpv_ch, "open"))
    else:
        phase.log("using_ox is false, Ox MPV will stay closed")
    if using_fuel:
        events.append((fuel_mpv_time, "Torch Fuel MPV", fuel_mpv_ch, "open"))
    else:
        phase.log("using_fuel is false, Fuel MPV will stay closed")
    events.append((spark_off_time, "Spark plug OFF", igniter_ch, "close"))
    if using_spectre:
        events.append((config.get_var("spectre_ox_mpv_time"), "Spectre Ox MPV", config.get_vlv("spectre_ox_mpv"), "open"))
        events.append((config.get_var("spectre_fuel_mpv_time"), "Spectre Fuel MPV", config.get_vlv("spectre_fuel_mpv"), "open"))
    events.append((torch_off_time, "Torch Ox MPV", ox_mpv_ch, "close"))
    events.append((torch_off_time, "Torch Fuel MPV", fuel_mpv_ch, "close"))
    events.append((torch_off_time, "Ox Post-MPV Vent", ox_post_mpv_vent, "open"))
    events.append((torch_off_time, "Fuel Post-MPV Vent", fuel_post_mpv_vent, "open"))

    # When making a phase, remember to always use the "phase" version of blocking events!
    phase.log("Hit 'enter' to start countdown sequence") #SOP doc says it should be enter
    phase.wait_for_input()
    while phase._wait.is_set():
        phase.sleep(0) # Wait until input is received

    # It is best practice to use the Synnax controller for timing events because it has a high-precision clock 
    t_zero = sy.TimeStamp.now() + sy.TimeSpan.from_seconds(countdown_duration)
    t_ignition_detection_start = t_zero + sy.TimeSpan.from_seconds(ignition_detection_start)
    t_ignition_detection_end   = t_zero + sy.TimeSpan.from_seconds(ignition_detection_end)
    schedule: list[tuple[sy.TimeStamp, str, str, str]] = [(t_zero + sy.TimeSpan.from_seconds(t), name, channel, action) for t, name, channel, action in events]
      
    #keep track of which events we've done
    #opened: set[str] = set()
    done: set[int] = set() 
    last_logged_second: int | None = None #keeping track of countdown display
    ignition_detection_started: bool = False
    ignition_detection_finished: bool = False
    ignition_detection_failing: bool = False
    pc_min: float = float("inf")
    pc_max: float = float("-inf")

    while True:
        phase.sleep(0) # Always add a phase.sleep(0) if you're making a loop!
        now: sy.TimeStamp = sy.TimeStamp.now()

        # Log the countdown on every second
        t_seconds = (int(now) - int(t_zero)) // int(sy.TimeSpan.SECOND)        
        if t_seconds != last_logged_second:
            phase.log(f"T{t_seconds:+d}")
            last_logged_second = t_seconds

        #actually turning on/open/close something if it's time (condendsed the checks below)
        for i, (t_event, name, channel, action) in enumerate(schedule):
            if (now >= t_event) and (i not in done):
                if action == "open":
                    open_vlv(ctrl, config, channel)
                else:
                    close_vlv(ctrl, config, channel)
                phase.log(f"{name}: {action} ({channel})", color="green")
                done.add(i)
        
        # If it is time for one of the valves to open and it hasn't yet, open them 
        #if (now >= t_fuel) and (ctrl[fuel_mpv_ch] == CLOSED):
        #    phase.log(f"Opening {fuel_mpv_ch}")
        #    ctrl[fuel_mpv_ch] = OPEN
        #if (now >= t_ox) and (ctrl[ox_mpv_ch] == CLOSED):
        #    phase.log(f"Opening {ox_mpv_ch}")
        #    ctrl[ox_mpv_ch] = OPEN
        #if (now >= t_igniter) and (ctrl[igniter_ch] == CLOSED):
        #    phase.log(f"Activating {igniter_ch}")
        #    ctrl[igniter_ch] = OPEN
        
        # If we are at or have exceeded the target time, close valves and return
        if t_ignition_detection_start <= now < t_ignition_detection_end:
            if not ignition_detection_started:
                phase.log("Ignition detection started")
                ignition_detection_started = True
            readings: list[float] = [v for v in (ctrl.get(ch) for ch in torch_pts) if v is not None]
            ok, pc = evaluate_ignition(readings, vote_threshold, lower, upper)
            pc_text: str = "no data" if pc is None else f"{pc:.1f}"
            if pc is not None:
                pc_min = min(pc_min, pc)
                pc_max = max(pc_max, pc)
            if not ok and enable_ignition_detection_aborts:
                phase.log(f"Ignition NOT detected (Pc = {pc_text} psig, bounds {lower}-{upper}), aborting", color="red", bold=True)
                countdown_safe(phase)  # same safing as a manual abort (SOP 3.202)
                return
            if not ok and not ignition_detection_failing:  # only warn when it changes, not every loop
                phase.log(f"Pc = {pc_text} psig out of bounds (aborts disabled)", color="yellow")
            ignition_detection_failing = not ok
        elif now >= t_ignition_detection_end and not ignition_detection_finished:
            phase.log(f"Ignition detection ended, Pc min/max = {pc_min:.1f}/{pc_max:.1f} psig")
            ignition_detection_finished = True

        if len(done) == len(schedule):
            phase.log("Torch sequence complete", color="green", bold=True)
            return

def countdown_safe(phase: Phase) -> None: #this part is for if its aborted or errors out, needs to close all prop paths to torch + turn off spark plug
    ctrl: sy.Controller = phase.ctrl
    config: Config = phase.config

    channels_to_close: list[str] = [
        config.get_vlv("fuel_mpv"),
        config.get_vlv("ox_mpv"),
        config.get_vlv("igniter"),   
    ]
    channels_to_open: list[str] = [
        config.get_vlv("fuel_post_mpv_vent"),
        config.get_vlv("ox_post_mpv_vent") 
    ]

    for channel in channels_to_close:
        phase.log(f"Closing {channel}")
        ctrl[channel] = not config.is_vlv_nc(channel) # did it this way to prevent accidental reopening

    for channel in channels_to_open:
        phase.log(f"Opening {channel}")
        ctrl[channel] = config.is_vlv_nc(channel)

def main() -> None:
    args: argparse.Namespace = parse_args()
    config: Config = Config(filepath=args.config)
    
    # Make Autosequence object, also connects to Synnax & other checks
    auto: Autosequence = Autosequence(
        name="Torch Igniter Autosequence",
        cluster=args.cluster,
        config=config,
    )

    countdown_phase: Phase = Phase(
        name="Countdown",
        ctrl=auto.ctrl,
        config=config,
        main_func=countdown,
        auto=auto,
        safe_func=countdown_safe,
    )
    auto.add_phase(countdown_phase)
    auto.run() # Starts the autosequence CLI

    if args.log is not None:
        write_logs_to_file(filepath=args.log)

if __name__ == "__main__":
    main()