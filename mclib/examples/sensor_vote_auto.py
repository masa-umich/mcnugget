from mclib import Phase, Autosequence, Config, sensor_vote_values, sensor_vote
import synnax as sy

def vote_pressure(phase: Phase) -> None:
    ctrl: sy.Controller = phase.ctrl
    config: Config = phase.config

    vote_threshold: float = config.get_var("sensor_vote_threshold")
    pressure_channels: list[str] = [
        config.get_pt("chamber_pt_1"),
        config.get_pt("chamber_pt_2"),
        config.get_pt("chamber_pt_3"),
    ]

    # Use sensor_vote_values when you already have the readings in a list.
    pressure_values: list[float] = []
    for channel in pressure_channels:
        pressure: float | None = ctrl.get(channel)
        if pressure is not None:
            pressure_values.append(pressure)

    # Keep values within the threshold of the median, then average those values.
    # For example, [420, 422, 900] with a threshold of 10 returns 421.
    voted_values: float | None = sensor_vote_values(
        pressure_values, threshold=vote_threshold
    )
    phase.log(f"Readings: {pressure_values}; voted pressure: {voted_values} psi")

    # sensor_vote reads the channels and skips missing values for you.
    # This takes a fresh sample, so it may differ from the vote above.
    voted_channels: float | None = sensor_vote(
        ctrl=ctrl, channels=pressure_channels, threshold=vote_threshold
    )
    if voted_channels is None:
        phase.log("No chamber pressure readings are available")
        return

    phase.log(f"Voted channel pressure: {voted_channels:.2f} psi")

def main() -> None:
    config: Config = Config(filepath="example-config.yaml")

    auto: Autosequence = Autosequence(
        name="Sensor Vote Example",
        cluster="localhost",
        config=config,
    )

    vote_phase: Phase = Phase(
        name="Vote",
        ctrl=auto.ctrl,
        config=config,
        main_func=vote_pressure,
        auto=auto,
    )
    auto.add_phase(vote_phase)
    auto.run()  # Starts the autosequence CLI; use "start vote".

if __name__ == "__main__":
    main()
