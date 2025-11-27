#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax==0.46.0",
#     "pandas",
#     "termcolor",
#     "yaspin",
# ]
# ///

"""
This is a file that reads in the raw voltages that have been linearly scaled
with Synnax and compares them with thermistor values to derive the temperature
readings in Celsius, which are then written to the tc channels.

Conversion Process
1. Read in thermistor supply + signal voltages
2. Compute resistance from voltage drop
3. Compute temperature from resistance
4. Read in linearly scaled TC values from fake TC channels
5. Convert linearly scaled TC values to temperature
6. Use thermistor temperature combined with TC temperature to derive final temperature
7. Write final temperature to actual TC channels

Actual Script
1. Imports/Setup/Cluster connection
2. Verify channel existence
3. Loop
    i. Read in all available values (gse_tc_{i}_raw + gse_tc_thermistor_{supply|signal})
    ii. Recompute thermistor
    iii. Compute TC values
    iv. Write to real TC channels (gse_tc_{i})


"""

from termcolor import colored
from yaspin import yaspin

# fun spinner while we load packages
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

import argparse
import synnax as sy
from synnax.hardware import ni
import pandas as pd
import datetime
from typing import List
import time
import math

THERM_R2 = 10000

# Steinhardt-Hart coefficients, see config/sh_calculations.py
SH1 = 0.001125256672107591  # 0 degrees celsius
SH2 = 0.0002347204472978222  # 25 degrees celsius
SH3 = 8.563052731505164e-08  # 50 degrees celsius

verbose: bool = False # global setting (default = False)

class TC_Channels:
    # Retrieved channels (read from)
    gse_sensor_time: sy.Channel
    tc_raw_chs: List[sy.Channel]
    thermistor_supply_ch: sy.Channel
    thermistor_signal_ch: sy.Channel
    # Created channels (written to)
    gse_tc_time: sy.Channel
    tc_chs: List[sy.Channel]

    @yaspin(text=colored("Setting up channels...", "yellow"))
    def __init__(self, client: sy.Synnax) -> None:
        # initialize lists
        self.tc_raw_chs = []
        self.tc_chs = []
        # retrieve channels (we should never have to make these)
        self.gse_sensor_time = client.channels.retrieve("gse_sensor_time")
        self.thermistor_signal_ch = client.channels.retrieve("gse_thermistor_signal")
        self.thermistor_supply_ch = client.channels.retrieve("gse_thermistor_supply")

        for i in range(14):
            try:
                tc_raw_ch = client.channels.retrieve(f"gse_tc_{i + 1}_raw")
            except:
                if (verbose):
                    print(colored(f"Raw TC Channel {i} not found, skipping.", "yellow"))
                continue # skip invalid TC channels
            self.tc_raw_chs.append(tc_raw_ch)

        # create channels if they don't already exist
        self.gse_tc_time = client.channels.create(
            name="gse_tc_time",
            data_type=sy.DataType.TIMESTAMP,
            retrieve_if_name_exists=True,
            is_index=True,
        )

        # only make channels for the raw channels we retrieved
        for i in range(len(self.tc_raw_chs)):
            tc_raw_ch_name = self.tc_raw_chs[i].name
            tc_ch_name = tc_raw_ch_name.replace("_raw", "")
            tc_ch = client.channels.create(
                name=tc_ch_name,
                data_type=sy.DataType.FLOAT32,
                retrieve_if_name_exists=True,
                index=self.gse_tc_time.key,
            )
            self.tc_chs.append(tc_ch)
    
    def get_read_channels(self) -> List[str]:
        read_channels: List[str] = [
            self.gse_sensor_time.name,
            self.thermistor_signal_ch.name,
            self.thermistor_supply_ch.name
        ]
        for tc_raw_ch in self.tc_raw_chs:
            read_channels.append(tc_raw_ch.name)
        return read_channels
        
    def get_write_channels(self) -> List[str]:
        write_channels: List[str] = [self.gse_tc_time.name]
        
        for tc_ch in self.tc_chs:
            write_channels.append(tc_ch.name)
        return write_channels


# helper function to raise pretty errors
def error_and_exit(message: str, error_code: int = 1, exception=None) -> None:
    spinner.stop()  # incase it's running
    if exception != None:  # exception is an optional argument
        print(exception)
    print(colored(message, "red", attrs=["bold"]))
    print(colored("Exiting", "red", attrs=["bold"]))
    exit(error_code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="The autosequence for preparring Limeight for launch!"
    )
    parser.add_argument(
        "-c",
        "--cluster",
        help="Specify a Synnax cluster to connect to",
        type=str,
        default="synnax.masa.engin.umich.edu"
    )
    parser.add_argument(
        "-f",
        "--frequency",
        help="Specify a frequency to read & write data at (Hertz)",
        type=int,
        default=50
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Shold the program output extra debugging information",
        action="store_true"
    )  # Positional argument
    args = parser.parse_args()
    if (args.verbose):
        verbose = True # set global
    return args


@yaspin(text=colored("Logging onto Synnax cluster...", "yellow"))
def synnax_login(cluster: str) -> sy.Synnax:
    try:
        client = sy.Synnax(
            host=cluster,
            port=9090,
            username="synnax",
            password="seldon",
        )
    except Exception as e:
        error_and_exit(
            f"Could not connect to Synnax at {cluster}, are you sure you're connected?"
        )
    return client  # type: ignore
                        
def calculate_thermistor_offset(supply, signal):
    try:
        # voltage drop across thermistor is proportional to resistance
        # convert mV to celsius
        resistance = ((supply - signal) * THERM_R2) / signal
        inverse_kelvin = SH1 + SH2 * math.log(resistance) + SH3 * math.log(resistance) ** 3
        celsius = 1 / inverse_kelvin - 273.15
        # convert celsius back to mV
        offset = compute_mv_from_temperature(celsius)
        return offset, celsius
    except ValueError:
        print("Thermistor had a math domain error")
        return 0.0, 0.0


def compute_mv_from_temperature(celsius):
    # compute mV representation of temperature
    # uses SCIENTIFIC notation
    c = [0] * 15
    if -270 <= celsius < 0:
        c[0] = 0.0 * 10**0
        c[1] = 3.8748106364 * 10**1
        c[2] = 4.4194434347 * 10**-2
        c[3] = 1.1844323105 * 10**-4
        c[4] = 2.0032973554 * 10**-5
        c[5] = 9.0138019559 * 10**-7
        c[6] = 2.2651156593 * 10**-8
        c[7] = 3.6071154205 * 10**-10
        c[8] = 3.8493939883 * 10**-12
        c[9] = 2.8213521925 * 10**-14
        c[10] = 1.4251594779 * 10**-16
        c[11] = 4.8768662286 * 10**-19
        c[12] = 1.0795539270 * 10**-21
        c[13] = 1.3945027062 * 10**-24
        c[14] = 7.9795153927 * 10**-28
    elif 0 <= celsius <= 400:
        c[0] = 0.0 * 10**0
        c[1] = 3.8748106364 * 10**1
        c[2] = 3.3292227880 * 10**-2
        c[3] = 2.0618243404 * 10**-4
        c[4] = -2.1882256846 * 10**-6
        c[5] = 1.0996880928 * 10**-8
        c[6] = -3.0815758772 * 10**-11
        c[7] = 4.5479135290 * 10**-14
        c[8] = -2.7512901673 * 10**-17
    else:
        return -1

    volts = 0
    for i in range(15):
        volts += c[i] * celsius**i
    return volts / 1000


def compute_temperature_from_mv(mv):
    if -6.3 <= mv < -4.648:
        constants = [
            -192.43000,
            -5.4798963,
            59.572141,
            1.9675733,
            -78.176011,
            -10.963280,
            0.27498092,
            -1.3768944,
            -0.45209805,
        ]
    elif -4.648 <= mv < 0.0:
        constants = [
            -60.0,
            -2.1528350,
            30.449332,
            -1.2946560,
            -3.0500735,
            -0.19226856,
            0.0069877863,
            -0.10596207,
            -0.010774995,
        ]
    elif 0.0 <= mv < 9.288:
        constants = [
            135.0,
            5.9588600,
            20.325591,
            3.3013079,
            0.12638462,
            -0.00082883695,
            0.17595577,
            0.0079740521,
            0.0,
        ]
    elif 9.288 <= mv < 20.872:
        constants = [
            300.0,
            14.861780,
            17.214707,
            -0.93862713,
            -0.073509066,
            0.0002957614,
            -0.048095795,
            -0.0047352054,
            0.0,
        ]
    else:
        return -1

    T0, V0, p1, p2, p3, p4, q1, q2, q3 = constants
    # print(T0, V0, p1, p2, p3, p4, q1, q2, q3)

    numerator = (mv - V0) * (p1 + (mv - V0) * (p2 + (mv - V0) * (p3 + p4 * (mv - V0))))
    denominator = 1 + (mv - V0) * (q1 + (mv - V0) * (q2 + q3 * (mv - V0)))
    return T0 + (numerator / denominator)


#@yaspin(text=colored("Converting values...", "green"))
def driver(tc_channels: TC_Channels, streamer: sy.Streamer, writer: sy.Writer, frequency: int) -> None:
    loop = sy.Loop(sy.Rate.HZ * frequency)
    while loop.wait():
        frame = streamer.read()
        if frame is None:
            if verbose:
                print(colored("Getting frame timed out"))
            continue

        # Get raw data
        therm_supply_value = frame[tc_channels.thermistor_supply_ch.name][-1]
        therm_signal_value = frame[tc_channels.thermistor_signal_ch.name][-1]
        gse_sensor_time = frame[tc_channels.gse_sensor_time.name][-1]
        tc_raw_values = {}

        for i in range(len(tc_channels.tc_raw_chs)):
            tc_raw_values[tc_channels.tc_raw_chs[i].name] = frame[tc_channels.tc_raw_chs[i].name][-1]

        # Calculate thermistor offset for CJC
        therm_offset, _ = calculate_thermistor_offset(therm_supply_value, therm_signal_value)

        # Prepare values to write
        write_data = {}
        # Convert TC values
        for i in range(len(tc_raw_values)):
            raw_tc_value = tc_raw_values[tc_channels.tc_raw_chs[i].name]
            tc_temp = compute_temperature_from_mv(raw_tc_value + therm_offset)
            write_data[tc_channels.tc_chs[i].name] = tc_temp
        
        write_data[tc_channels.gse_tc_time.name] = gse_sensor_time # Get the time we're writing at
        writer.write(write_data)


def main() -> None:
    args = parse_args()
    client = synnax_login(args.cluster)
    tc_channels = TC_Channels(client)
    write_chs = tc_channels.get_write_channels()
    read_chs = tc_channels.get_read_channels()
    if verbose:
        print(colored(f"Write channels: {write_chs}", "light_blue"))
        print(colored(f"Read channels: {read_chs}", "light_blue"))
    with client.open_streamer(channels=read_chs) as streamer:
        with client.open_writer(start=sy.TimeStamp.now(), channels=write_chs) as writer:
            driver(tc_channels, streamer, writer, args.frequency)
    print(colored("Thermo-magic script ended. Have a great day!"))


if __name__ == "__main__":
    spinner.stop()  # stop the "initializing..." spinner since we're done loading all the imports
    try:
        main()
    except KeyboardInterrupt:  # Abort cases also rely on this, but Python takes the closest exception catch inside nested calls
        error_and_exit("Keyboard interrupt detected")
    # except Exception as e:  # catch-all uncaught errors
        # error_and_exit("Uncaught exception!", exception=e)
