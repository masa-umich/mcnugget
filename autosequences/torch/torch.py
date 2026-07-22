#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax==0.49.0",
#     "yaspin",
#     "termcolor",
#     "pyyaml",
#     "prompt-toolkit",
#     "mclib",
# ]
# [tool.uv]
# reinstall-package = ["mclib"]
# [tool.uv.sources]
# mclib = { path = "../../mclib" }
# ///

from termcolor import colored
from yaspin import yaspin

# fun spinner while we load packages
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

# our modules
from mclib import (
    Phase,
    Autosequence,
    Config,
    log,
    write_logs_to_file,
    open_vlv,
    close_vlv,
)


# standard modules
import argparse

# CLI argument parser
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Torch ignition autosequence (manual, interactive)"
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
        default="141.212.192.160",
        type=str,
    )
    parser.add_argument(
        "-l",
        "--log",
        help="Specify a log file to write logs to at the end of the autosequence",
        default="torch-autosequence.log",
        type=str,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Should the program output extra debugging information",
        action="store_true",
    )
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


def global_abort(auto: Autosequence) -> None:
    ctrl = auto.ctrl
    config = auto.config

    spark_plug = config.get_vlv("spark_plug")
    methane_mpv = config.get_vlv("methane_mpv")
    gox_mpv = config.get_vlv("gox_mpv")

    log("\n\nManual abort, safing system", color="red")
    log("Closing all valves", color="red")
    
    close_vlv(ctrl, config, spark_plug)
    close_vlv(ctrl, config, gox_mpv)
    close_vlv(ctrl, config, methane_mpv)
    log("Terminated", color="red")


def torch_ignite_safe(phase: Phase) -> None:
    phase.log("Manual abort, safing system", color="red")
    phase.log("Closing all valves", color="red")
    ctrl = phase.ctrl
    config = phase.config
    close_vlv(ctrl, config, config.get_vlv("spark_plug"))
    close_vlv(ctrl, config, config.get_vlv("gox_mpv"))
    close_vlv(ctrl, config, config.get_vlv("methane_mpv"))
    phase.log("Terminated", color="red")


def torch_ignite(phase: Phase) -> None:
    ctrl = phase.ctrl
    config = phase.config
    
    methane_mpv_lead_time = config.get_var("methane_mpv_lead_time")
    burn_duration = config.get_var("burn_duration")
    
    spark_plug = config.get_vlv("spark_plug")
    methane_mpv = config.get_vlv("methane_mpv")
    gox_mpv = config.get_vlv("gox_mpv")
    
    methane_state = config.get_state("methane_mpv")
    gox_state = config.get_state("gox_mpv")

    phase.log("Starting Igniter Autosequence. Setting initial system state.")

    if ctrl.get(methane_state) == 1:
        phase.log("Methane MPV is open, press Enter to safely close it")
        phase.wait_for_input()
        while phase._wait.is_set():
            phase.sleep(0.1)
        phase.log("Closing methane MPV")
        close_vlv(ctrl, config, methane_mpv)
    else:
        phase.log("Methane MPV was not prompted to close, moving on with the sequence")

    if ctrl.get(gox_state) == 1:
        phase.log("GOX MPV is open, press Enter to safely close it")
        phase.wait_for_input()
        while phase._wait.is_set():
            phase.sleep(0.1)
        phase.log("Closing GOX MPV")
        close_vlv(ctrl, config, gox_mpv)
    else:
        phase.log("GOX MPV was not prompted to close, moving on with the sequence")

    phase.log("Press Enter to commence ignition sequence with a 5 second countdown ")
    phase.wait_for_input()
    while phase._wait.is_set():
        phase.sleep(0.1)

    phase.log("5")
    phase.sleep(1)
    phase.log("4")
    phase.sleep(1)
    phase.log("3")
    phase.sleep(1)
    phase.log("2")
    phase.sleep(1)
    phase.log("1")
    phase.log("Energizing Spark Plug")
    open_vlv(ctrl, config, spark_plug)
    phase.sleep(0.75)
    open_vlv(ctrl, config, methane_mpv)
    phase.sleep(methane_mpv_lead_time)
    phase.log("Commencing ignition sequence")
    phase.log("Opening GOX mpv")
    open_vlv(ctrl, config, gox_mpv)

    phase.log("Torch ignited")
    phase.sleep(burn_duration)
    phase.log("Closing MPVs and de-energizing spark plug")
    close_vlv(ctrl, config, gox_mpv)
    close_vlv(ctrl, config, methane_mpv)
    close_vlv(ctrl, config, spark_plug)
    phase.log("Terminating Autosequence")
    phase.log("Terminated")
    phase.sleep(1)


def main():
    args: argparse.Namespace = parse_args()
    config: Config = Config(filepath=args.config)
    cluster: str = args.cluster

    # Make Autosequence object, also connects to Synnax & other checks
    auto: Autosequence = Autosequence(
        name="Torch Ignition Autosequence",
        cluster=cluster,
        config=config,
        global_abort=global_abort,
    )

    ignite_phase: Phase = Phase(
        name="Ignite",
        ctrl=auto.ctrl,
        config=config,
        main_func=torch_ignite,
        auto=auto,
        safe_func=torch_ignite_safe,
    )
    auto.add_phase(ignite_phase)

    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports

    # Run the autosequence
    auto.run()

    log("Autosequence has terminated, have a great flight!")

    if args.log != "":
        write_logs_to_file(filepath=args.log)
    return


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # make sure we stop the spinner on any exception (it prevents the program from exiting cleanly)
        spinner.stop()
        raise