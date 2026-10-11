from mclib import Phase, Autosequence, Config, close_vlv, open_vlv, write_logs_to_file
import synnax as sy
from typing import Final
import argparse

# Alias for boolean state of a valve to make things easier to read
#OPEN: Final[bool] = True
#CLOSED: Final[bool] = False

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


def countdown(phase: Phase) -> None:
    # Grab the Synnax controller and config from the phase object
    ctrl: sy.Controller = phase.ctrl
    config: Config = phase.config
    
    # Grab the different configuration variables and channel names this phase will need from the config
    countdown_duration: float = config.get_var("countdown_duration")
    burn_duration: float = config.get_var("burn_duration")
    fuel_mpv_offset_time: float = config.get_var("fuel_mpv_offset_time")
    ox_mpv_offset_time: float = config.get_var("ox_mpv_offset_time")
    igniter_offset_time: float = config.get_var("igniter_offset_time")
    fuel_mpv_ch: str = config.get_vlv("fuel_mpv")
    ox_mpv_ch: str = config.get_vlv("ox_mpv")
    igniter_ch: str = config.get_vlv("igniter")
    ox_post_mpv_vent: str = config.get_vlv("ox_post_mpv_vent")
    fuel_post_mpv_vent: str = config.get_vlv("fuel_post_mpv_vent")
    using_ox: bool = config.get_var("using_ox")
    using_fuel: bool = config.get_var("using_fuel")

    #doucle checking valid offsets
    for name, offset in [("ox_mpv_offset_time", ox_mpv_offet_time), ("fuel_mpv_offset_time", fuel_mpv_offset_time), ("igniter_offset_time", igniter_offset_time)]:
        if not(0 <= offset < countdown_duration):
            phase.log(f"{name} = {offset} must be between 0 and countdown_duration ({countdown_duration}), aborting")
            return

    #setting todo of what to turn on + time before T-0
    events: list[tuple[str, str, float]] =[]
    if using_ox:
        events.append(("Ox MPV", ox_mpv_ch, ox_mpv_offset_time))
    else:
        phase.log("using_ox is false, Ox MPV will stay closed")
    if using_fuel:
        events.append(("Fuel MPV", fuel_mpv_ch, fuel_mpv_offset_time))
    else:
        phase.log("using_fuel is false, Fuel MPV will stay closed")
    events.append(("Igniter", igniter_ch, igniter_offset_time))

    # When making a phase, remember to always use the "phase" version of blocking events!
    phase.log("Hit 'enter' to start countdown sequence") #SOP doc says it should be enter
    phase.wait_for_input()
    while phase._wait.is_set():
        phase.sleep(0) # Wait until input is received

    # It is best practice to use the Synnax controller for timing events because it has a high-precision clock 
    t_start: sy.TimeStamp = sy.TimeStamp.now()
    t_zero: sy.TimeStamp = t_start + sy.TimeSpan.from_seconds(countdown_duration)
    t_end: sy.TimeStamp = t_zero + sy.TimeSpan.from_seconds(burn_duration)
    schedule: list[tuple[str, str, sy.TimeStamp]] = [(name, channel, t_zero - sy.TimeSpan.from_seconds(offset)) for name, channel, offset, in events]
    #t_fuel: sy.TimeStamp = t_zero - sy.TimeSpan.from_seconds(fuel_mpv_start_time)
    #t_ox: sy.TimeStamp = t_zero - sy.TimeSpan.from_seconds(ox_mpv_start_time)
    #t_igniter: sy.TimeStamp = t_zero - sy.TimeSpan.from_seconds(ignite_point_time)
    #last_logged_second: int | None = None # Used to keep track of the countdown display

    #keep track of commands we've done ourselves
    opened: set[str] = set()
    last_logged_second = int | None = none #keeping track of countdown display

    while True:
        phase.sleep(0) # Always add a phase.sleep(0) if you're making a loop!
        now: sy.TimeStamp = sy.TimeStamp.now()

        # Log the countdown on every second
        t_seconds = (int(now) - int(t_zero)) // int(sy.TimeSpan.SECOND)        
        if t_seconds != last_logged_second:
            phase.log(f"T{t_seconds:+d}")
            last_logged_second = t_seconds

        #actually turning on/open/close something if it's time (condendsed the checks below)
        for name, channel, t_open in schedule:
            if (now >= t_open) and (channel not in opened):
                phase.log(f"Opening {name} ({channel})", color="green")
                open_vlv(ctrl, config, channel)
                opened.add(channel)
        
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
        if now >= t_end:
            phase.log(f"Burn duration met or exceeded, closing valves")
            ctrl[fuel_mpv_ch] = CLOSED
            ctrl[ox_mpv_ch] = CLOSED
            ctrl[igniter_ch] = CLOSED
            open_vlv(ctrl, config, ox_post_mpv_vent)
            open_vlv()
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
        channel: str = config.get_vlv(name)
        phase.log(f"Closing {name} ({channel})")
        ctrl[channel] = not config.is_vlv_nc(channel) # did it this way to prevent accidental reopening

    for channel in channels_to_open:
        channel: str = config.get_vlv(name)
        phase.log(f"Opening {name} ({channel})")
        ctrl[channel] = config.is_vlv_nc(channel)

def main() -> None:
    args: argparse.Namespace = parse_args()
    config: Config = Config(filepath="args.config")
    
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