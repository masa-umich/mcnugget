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
                    tc_temp = computeTemperature(tc_raw)
                    real_temp = tc_temp + therm_offset
                    thermocouple_data[thermocouple_write_channels[i]] = real_temp
                writer.write(thermocouple_data)


def calculate_thermistor_offset(supply, signal):
    pass


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
