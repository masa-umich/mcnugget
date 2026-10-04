from mclib import Phase, Autosequence, Config
import synnax as sy

def wait_for_pressure(phase: Phase) -> None:
    # Grab the Synnax controller and config from the phase object.
    ctrl: sy.Controller = phase.ctrl
    config: Config = phase.config

    pressure_target: float = config.get_var("pressure_target")
    pressure_timeout: float = config.get_var("pressure_timeout")
    pressure_ch: str = config.get_pt("ox_tank_pt_1")

    # The condition receives the controller and returns True when we can proceed.
    def pressure_reached(ctrl: sy.Controller) -> bool:
        pressure: float | None = ctrl.get(pressure_ch)
        return pressure is not None and pressure >= pressure_target

    phase.log(f"Waiting for {pressure_ch} to reach {pressure_target} psi")

    # Use the phase version so the wait responds to pause, abort, and quit.
    reached: bool = phase.wait_until(pressure_reached, timeout=pressure_timeout)
    if not reached:
        phase.log(f"Pressure target was not reached within {pressure_timeout} seconds")
        return

    phase.log(f"Pressure target reached: {ctrl.get(pressure_ch)} psi")

def main() -> None:
    config: Config = Config(filepath="example-config.yaml")

    # Connect to Synnax and acquire the channels defined in the config.
    auto: Autosequence = Autosequence(
        name="Pressure Wait Example",
        cluster="localhost",
        config=config,
    )

    pressure_phase: Phase = Phase(
        name="Pressure Wait",
        ctrl=auto.ctrl,
        config=config,
        main_func=wait_for_pressure,
        auto=auto,
    )
    auto.add_phase(pressure_phase)
    auto.run()  # Starts the autosequence CLI; use "start pressure wait".

if __name__ == "__main__":
    main()
