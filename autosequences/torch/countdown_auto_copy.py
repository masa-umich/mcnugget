from mclib import Phase, Autosequence, Config
import synnax as sy
from typing import Final

# Alias for boolean state of a valve to make things easier to read
OPEN: Final[bool] = True
CLOSED: Final[bool] = False

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
    burn_time: float = config.get_var("burn_time")
    fuel_mpv_start_time: float = config.get_var("fuel_mpv_start_time")
    ox_mpv_start_time: float = config.get_var("ox_mpv_start_time")
    ignite_point_time: float = config.get_var("ignite_point_time")
    fuel_mpv_ch: str = config.get_vlv("fuel_mpv")
    ox_mpv_ch: str = config.get_vlv("ox_mpv")
    igniter_ch: str = config.get_vlv("igniter")

    # When making a phase, remember to always use the "phase" version of blocking events!
    phase.log("Hit 'enter' to start countdown sequence") #SOP doc says it should be enter
    phase.wait_for_input()
    while phase._wait.is_set():
        phase.sleep(0) # Wait until input is received

    # It is best practice to use the Synnax controller for timing events because it has a high-precision clock 
    t_start: sy.TimeStamp = sy.TimeStamp.now()
    t_zero: sy.TimeStamp = t_start + sy.TimeSpan.from_seconds(countdown_duration)
    t_end: sy.TimeStamp = t_zero + sy.TimeSpan.from_seconds(burn_time)
    t_fuel: sy.TimeStamp = t_zero - sy.TimeSpan.from_seconds(fuel_mpv_start_time)
    t_ox: sy.TimeStamp = t_zero - sy.TimeSpan.from_seconds(ox_mpv_start_time)
    t_igniter: sy.TimeStamp = t_zero - sy.TimeSpan.from_seconds(ignite_point_time)
    last_logged_second: int | None = None # Used to keep track of the countdown display

    while True:
        phase.sleep(0) # Always add a phase.sleep(0) if you're making a loop!
        now: sy.TimeStamp = sy.TimeStamp.now()

        # Log the countdown on every second
        t_seconds = (int(now) - int(t_zero)) // int(sy.TimeSpan.SECOND)        
        if t_seconds != last_logged_second:
            phase.log(f"T{t_seconds:+d}")
            last_logged_second = t_seconds
        
        # If it is time for one of the valves to open and it hasn't yet, open them 
        if (now >= t_fuel) and (ctrl[fuel_mpv_ch] == CLOSED):
            phase.log(f"Opening {fuel_mpv_ch}")
            ctrl[fuel_mpv_ch] = OPEN
        if (now >= t_ox) and (ctrl[ox_mpv_ch] == CLOSED):
            phase.log(f"Opening {ox_mpv_ch}")
            ctrl[ox_mpv_ch] = OPEN
        if (now >= t_igniter) and (ctrl[igniter_ch] == CLOSED):
            phase.log(f"Activating {igniter_ch}")
            ctrl[igniter_ch] = OPEN
        # If we are at or have exceeded the target time, close valves and return
        if now >= t_end:
            phase.log(f"Burn duration met or exceeded, closing valves")
            ctrl[fuel_mpv_ch] = CLOSED
            ctrl[ox_mpv_ch] = CLOSED
            ctrl[igniter_ch] = CLOSED
            return

def countdown_safe(phase: Phase) -> None:
    ctrl: sy.Controller = phase.ctrl
    config: Config = phase.config

    channels_to_close: list[str] = [
        config.get_vlv("fuel_mpv"),
        config.get_vlv("ox_mpv"),
        config.get_vlv("igniter"),   
    ]
    for channel in channels_to_close:
        phase.log(f"Closing {channel}")
        ctrl[channel] = CLOSED


def main() -> None:
    config: Config = Config(filepath="example-config.yaml")
    
    # Make Autosequence object, also connects to Synnax & other checks
    auto: Autosequence = Autosequence(
        name="Limelight Launch Autosequence",
        cluster="localhost",
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

if __name__ == "__main__":
    main()