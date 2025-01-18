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

import synnax as sy
from synnax.hardware import ni
import pandas as pd
import datetime
import time
import math


THERM_R2 = 10000

# Steinhardt-Hart coefficients, see config/sh_calculations.py
SH1 = 0.001125256672107591  # 0 degrees celsius
SH2 = 0.0002347204472978222  # 25 degrees celsius
SH3 = 8.563052731505164e-08  # 50 degrees celsius


def generate_tc_data():
    # grab channels from synnax
    client = sy.Synnax(
        host="masasynnax.ddns.net",
        port=9090,
        username="synnax",
        password="seldon",
    )
    thermocouple_channels = []
    thermocouple_write_channels = []
    thermocouple_data = {}
    # 2 arrays and a dict because writing as a dict is synnax's favorite format

    # channel creation/retrieval
    gse_ai_time = client.channels.create(
        name="gse_ai_time",
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
        is_index=True,
    )
    for i in range(14):
        tc_channel = client.channels.create(
            name=f"gse_tc_{i}_raw",
            data_type=sy.DataType.FLOAT32,
            index=gse_ai_time.key,
            retrieve_if_name_exists=True,
        )
        thermocouple_channels[i] = tc_channel
        tc_write_channel = client.channels.create(
            name=f"gse_tc_{i}",
            data_type=sy.DataType.FLOAT32,
            index=gse_ai_time.key,
            retrieve_if_name_exists=True,
        )
        thermocouple_write_channels[i] = tc_write_channel

    thermistor_supply = client.channels.create(
        name="gse_thermistor_supply",
        data_type=sy.DataType.FLOAT32,
        index=gse_ai_time.key,
        retrieve_if_name_exists=True,
    )
    thermistor_signal = client.channels.create(
        name="gse_thermistor_signal",
        data_type=sy.DataType.FLOAT32,
        index=gse_ai_time.key,
        retrieve_if_name_exists=True,
    )

    # TODO: check that there are data points for each channel in the last 5 minutes before starting the loop

    # stream TC data, calculating thermistor each iteration
    with client.open_streamer(
        channels=[thermistor_signal, thermistor_supply] + thermocouple_channels
    ) as streamer:
        with client.open_writer(channels=thermocouple_write_channels) as writer:
            while True:
                frame = streamer.read(timeout=5)
                if frame is None:
                    print(
                        f"missed frame at {datetime.now()}, trying again in 5 seconds"
                    )
                    time.sleep(5)
                therm_supply = frame[thermistor_supply.key]
                therm_signal = frame[thermistor_signal.key]
                therm_offset = calculate_thermistor_offset(therm_supply, therm_signal)
                for i in range(len(thermocouple_channels)):
                    tc = thermocouple_channels[i]
                    tc_raw = frame[tc.key]
                    tc_temp = computeTemperature(tc_raw + therm_offset)
                    thermocouple_data[thermocouple_write_channels[i]] = tc_temp
                writer.write(thermocouple_data)


def calculate_thermistor_offset(supply, signal):
    # voltage drop across thermistor is proportional to resistance
    resistance = ((supply - signal) * THERM_R2) / signal
    inverse_kelvin = SH1 + SH2 * math.log(resistance) + SH3 * math.log(resistance) ** 3
    return 1 / inverse_kelvin - 273.15


def computeTemperature(mv):
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

    numerator = (mv - V0) * (p1 + (mv - V0) * (p2 + (mv - V0) * (p3 + p4 * (mv - V0))))
    denominator = 1 + (mv - V0) * (q1 + (mv - V0) * (q2 + q3 * (mv - V0)))
    return T0 + (numerator / denominator)


def compute_mv(celsius):
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
