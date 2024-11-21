# import click
# import math
import pandas as pd
# from dataclasses import dataclass
# import gspread
import synnax as sy
from synnax.hardware.ni import types
# from synnax.hardware.ni import AnalogReadTask, DigitalReadTask, DigitalWriteTask, DigitalReadConfig, DigitalWriteConfig, AnalogReadTaskConfig, DOChan, DIChan, AIChan
# from rich.prompt import Prompt, Confirm
# import os
# from rich import print
# from mcnugget.client import client
import numpy as np

# class Item:
#     def __init__(
#         self, 
#         name: str, 
#         test: int, 
#         sensor_type: str, 
#         port: int, 
#         channel: int, 
#         volt: int, 
#         max_press: int = 0, 
#         slope: int = 0, 
#         nat_open: bool = False, 
#         power: int = 0, 
#         tc_type: str = "",
#     ):
#         self.name = name
#         self.test = test
#         self.sensor_type = sensor_type
#         self.port = port
#         self.channel = channel
#         self.volt = volt
#         self.max_press = max_press
#         self.slope = slope
#         self.nat_open = nat_open
#         self.power = power
#         self.tc_type = tc_type
    
#     def __repr__(self):
#         return (
#             f"Item(name={self.name}, test={self.test}, sensor_type={self.sensor_type}, "
#             f"port={self.port}, channel={self.channel}, volt={self.volt}, "
#             f"max_press={self.max_press}, slope={self.slope}, nat_open={self.nat_open}, "
#             f"power={self.power}, tc_type={self.tc_type})"
#         )
    
ar_task = types.AnalogReadTask(
    name = "Analog Read Task",
    device = "PCI-6225", 
    sample_rate = 10,# CONFIRM
    stream_rate = 5,# CONFIRM
    data_saving = True,
    channels = []
)

dr_task = types.DigitalReadTask(
    name = "Digital Read Task",
    device = "PCI-6514", 
    sample_rate = 10,# CONFIRM
    stream_rate = 5,# CONFIRM
    data_saving = True,
    channels = []
)

dw_task = types.DigitalWriteTask(
    name = "Digital Write Task",
    device = "PCI-6514", 
    state_rate = 50, # CONFIRM
    data_saving = True,
    channels = []
)   


def main():
    NUMBER_OF_ITEMS = 4 #change to take in input and then put into the function
    input_excel(r"C:\Users\ruchi\mcnugget\archive\cli\testing.xlsx", NUMBER_OF_ITEMS) #change to take in input and then put into the function

def input_excel(file_path: str, item_num: int):
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print("Exception 1 caught: ", e)
    
    df = df.drop('Type', axis=1)
    df_new = df.head(item_num) 
    print("Excel file succesfully read.")
    process_excel(df_new)

def process_excel(file: pd.DataFrame):
    # print("Input DF: ")
    # print_df(file)
    # print("Processing DataFrame into Items...")
    # print("Columns in DataFrame:", file.columns)

    for x, row in file.iterrows():
        try:
            # new_item = Item(
            #     name = row["Name"],
            #     test = row["Test"],
            #     sensor_type = row["Sensor Type"],
            #     port = row["Port"],
            #     channel = row["Channel"],
            #     volt = row["Supply Voltage (V)"],
            #     max_press = row["Max Pressure"],
            #     slope = row["Calibration Slope (mV/psig)"],
            #     nat_open = row["NO/NC"].strip().upper() == "NO",
            #     power = row["Power (W)"],
            #     tc_type = row["TC Type"],
            # )
            # items.append(new_item)
            if row["Sensor Type"] == "VLV":
                populate_digital(row)
            elif row["Sensor Type"] in ["PT", "TC", "LC"]:
                populate_analogue(row)
            else:
                print("Check Sensor Type in Sheet")
        except Exception as e:
            print(f"Error processing row {row}: {e}")

def populate_digital(row):
    # print("Making DI/DO channels")
    port = int(row["Port"])
    channel = int(row["Channel"])

    vlv_di_channel = types.DIChan()
    vlv_di_channel.channel = channel
    vlv_di_channel.port = channel / 8
    vlv_di_channel.line = channel % 8
    dr_task.config.channels.append(vlv_di_channel)

    vlv_do_channel = types.DOChan()
    vlv_do_channel.cmd_channel = channel
    vlv_do_channel.state_channel = channel
    vlv_do_channel.port =  (channel / 8) + 4
    vlv_do_channel.line = channel % 8
    dw_task.config.channels.append(vlv_do_channel)
    # print("Added VLV channel")

def populate_analogue(row):
    # print("Making AI Channels")   
    if row["Sensor Type"] == ["TC"]:
        volt_lst, temp_lst = process_tc_poly()
        tc_channel = types.AIVoltageChan()
        tc_channel.units = "Volts"
        tc_channel.custom_scale = types.TableScale(
            pre_scaled_vals = volt_lst, # Volts list
            scaled_vals = temp_lst, # Temperatures list
            pre_scaled_units = "Volts",
        )
        ar_task.config.channels.append(tc_channel)
        # print("Added TC channel")
    elif row["Sensor Type"] == ["PT"]:
        pt_channel = types.AIVoltageChan()
        pt_channel.units = "Volts" 
        pt_channel.custom_scale = types.LinScale(
            slope = row["Calibration Slope (mV/psig)"] * .0001, 
            y_intercept = row["Calibration Offset (V)"],
            pre_scaled_units = types.UnitsVolts,
            scaled_units = types.UnitsLbsPerSquareInch
        )
        ar_task.config.channels.append(pt_channel)
        # print("Added PT channel")
    elif row["Sensor Type"] == ["LC"]:
        lc_channel = types.AIStrainGageChan()  # i assume the lcs use strain like the physics qty
        lc_channel.strain_config = "full-bridge-I"  # CONFIRM
        lc_channel.voltage_excit_source = "External"  # CONFIRM
        lc_channel.voltage_excit_val = row["Supply Voltage (V)"]
        lc_channel.gage_factor = 2.0  # CONFIRM, app 2.0 is common. also its spelt guage smh synnax people
        lc_channel.nominal_gage_resistance = 120.0  # CONFIRM. this what i found online as an option
        lc_channel.poisson_ratio = 0.3  # CONFIRM, dep. on metal apparently
        lc_channel.lead_wire_resistance = 0.0  # NO CLUE CONFIRM
        lc_channel.initial_bridge_voltage = 0.0  # CONFIRM i think this is irl offset
        #lc_channel.custom_scale = NoScale()  ---> idk if we need this
        ar_task.config.channels.append(lc_channel)
        print("Added PT channel")

def process_tc_poly():
    # WE DONT NEED TO MAKE SHEETS
    # We convert directly expression -> lists

    # choose expression for each TC (by channel? id?)
    # conv to list and return (alr have this logic)

    a, b, c = 10, 5, 0
    voltage_range = (0, 0.05)
    num_points = 10

    voltages = np.linspace(voltage_range[0], voltage_range[1], num_points)
    volt_lst = list(voltages)

    temp_lst = []
    for v in voltages:
        temperature = a * v**2 + b * v + c
        temp_lst.append(temperature)

    return volt_lst, temp_lst



        




































# FOR DEBUGGING PURPOSES
def print_df(file: pd.DataFrame):
    print(file.to_string())

    # print("The Name Row: ")
    # print(file["Name"])

    # print("Row 1: ")
    # print(file.loc[1])






    



























if __name__ == "__main__":
    main()

