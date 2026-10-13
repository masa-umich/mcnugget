from mclib import Phase, Autosequence, Config, average_ch
import synnax as sy
from typing import Final

REFRESH_RATE: Final[int] = 10  # Samples per second.

def monitor_pressure(phase: Phase) -> None:
    ctrl: sy.Controller = phase.ctrl
    config: Config = phase.config

    averaging_time: float = config.get_var("averaging_time")
    pressure_ch: str = config.get_pt("ox_tank_pt_1")

    # The window counts samples, so convert the desired time using our sample rate.
    # average_ch is an exponentially weighted average, not a fixed sliding window.
    pressure_average = average_ch(window=round(REFRESH_RATE * averaging_time))

    while True:
        phase.sleep(1.0 / REFRESH_RATE)  # Set the sample rate and check phase signals.
        pressure: float | None = ctrl.get(pressure_ch)
        if pressure is None:
            continue  # Wait for a reading before initializing or updating the average.

        # The first sample seeds the average; each later sample updates it.
        # add_and_get(pressure) is a shortcut for the two calls below.
        pressure_average.add(pressure)
        smoothed_pressure: float = pressure_average.get()
        phase.log(f"Raw: {pressure:.2f} psi; smoothed: {smoothed_pressure:.2f} psi")

def main() -> None:
    config: Config = Config(filepath="example-config.yaml")

    auto: Autosequence = Autosequence(
        name="Pressure Average Example",
        cluster="localhost",
        config=config,
    )

    average_phase: Phase = Phase(
        name="Average",
        ctrl=auto.ctrl,
        config=config,
        main_func=monitor_pressure,
        auto=auto,
        refresh_rate=REFRESH_RATE,
    )
    auto.add_phase(average_phase)
    auto.run()  # Starts the autosequence CLI; use "start average", then "abort average".

if __name__ == "__main__":
    main()
