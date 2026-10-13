from mclib import Phase, Autosequence, Config
import synnax as sy

def measure_baseline(phase: Phase) -> None:
    ctrl: sy.Controller = phase.ctrl
    config: Config = phase.config

    averaging_time: float = config.get_var("averaging_time")
    vote_threshold: float = config.get_var("sensor_vote_threshold")
    pressure_channels: list[str] = [
        config.get_pt("chamber_pt_1"),
        config.get_pt("chamber_pt_2"),
        config.get_pt("chamber_pt_3"),
    ]

    phase.log(f"Measuring chamber pressure baseline for {averaging_time} seconds")

    # Vote across the sensors on each sample, then smooth the voted readings.
    # This method yields internally, so pause and abort still work while sampling.
    baseline: float = phase.avg_and_vote_for(
        ctrl=ctrl,
        channels=pressure_channels,
        threshold=vote_threshold,
        averaging_time=averaging_time,
    )

    phase.log(f"Chamber pressure baseline: {baseline:.2f} psi")

def main() -> None:
    config: Config = Config(filepath="example-config.yaml")

    auto: Autosequence = Autosequence(
        name="Pressure Baseline Example",
        cluster="localhost",
        config=config,
    )

    baseline_phase: Phase = Phase(
        name="Baseline",
        ctrl=auto.ctrl,
        config=config,
        main_func=measure_baseline,
        auto=auto,
    )
    auto.add_phase(baseline_phase)
    auto.run()  # Starts the autosequence CLI; use "start baseline".

if __name__ == "__main__":
    main()
