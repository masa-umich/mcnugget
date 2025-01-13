import pandas as pd
import synnax as sy
# from synnax.hardware.ni import types
from synnax.hardware.ni.types import *
import numpy as np
from synnax.hardware.device import Device
import ast

client = sy.Synnax()

DEBUG = False


### finding cards
analog_card = client.hardware.devices.retrieve(name="PCI-6225")
digital_card = client.hardware.devices.retrieve(name="PCI-6514")
if DEBUG:
    print("analog_card = ", analog_card)
    print("digital_card = ", digital_card)
if not analog_card or not digital_card:
    print("One or both cards not found, please configure them manually.")
    exit(1)

### creating analog task
analog_read_task = None
try:
    analog_task = client.hardware.tasks.retrieve(name="Analog Read Task")
except:
    analog_task = None
if analog_task is None:
    print("new analog read task will be created")
    analog_task = AnalogReadTask(
        name = "Analog Read Task",
        # device = analog_card.key,  # on channels instead 
        sample_rate = sy.Rate.HZ * 50,
        stream_rate = sy.Rate.HZ * 10,
        data_saving = True,
        channels = []
    )
    client.hardware.tasks.create([analog_task])
if DEBUG:
    print("analog_task = ", analog_task)

### creating digital read task
digital_read_task = None
try:
    digital_read_task = client.hardware.tasks.retrieve(name="Digital Read Task")
except:
    digital_read_task = None
if digital_read_task is None:
    print("new digital read task will be created")
    digital_read_task = DigitalReadTask(
        name = "Digital Read Task",
        device = digital_card.key, 
        sample_rate = sy.Rate.HZ * 50,
        stream_rate = sy.Rate.HZ * 10,
        data_saving = True,
        channels = []
    )
    client.hardware.tasks.create([digital_read_task])
if DEBUG:
    print("digital_read_task = ", digital_read_task)

# creating digital write task
digital_write_task = None
try:
    digital_write_task = client.hardware.tasks.retrieve(name="Digital Write Task")
except:
    digital_write_task = None
if digital_write_task is None:
    print("new digital write task will be created")
    digital_write_task = DigitalWriteTask(
        name = "Digital Write Task",
        device = digital_card.key, 
        state_rate = sy.Rate.HZ * 50,
        data_saving = True,
        channels = []
    )
    client.hardware.tasks.create([digital_write_task])
if DEBUG:
    print("digital_write_task = ", digital_write_task)

# new_pt_channel = AIVoltageChan(port=6, channel=6, device=analog_card.key, data_type="float64")
# new_pt_channel = AIVoltageChan(port=6, channel=6, device=analog_card.key, type="ai_voltage", data_type="float64")
channel_channel = client.channels.retrieve("gse_ai_ai_5").key
new_pt_channel = AIVoltageChan(port=5, channel=channel_channel, device=analog_card.key, type="ai_voltage")
# index = client.channels.retrieve("gse_ai_time").key
# client.channels.create(sy.Channel(
#     name = "Dev1/ai6",
#     data_type = "float64",
#     index=index
# ), retrieve_if_name_exists=True)
sy_analog_task = AnalogReadTask(client.hardware.tasks.retrieve(name="Analog Read Task"))
print("configured base task")
sy_analog_task.config.channels.append(new_pt_channel)
print(sy_analog_task)
print(sy_analog_task.config)
client.hardware.tasks.configure(sy_analog_task, timeout=30)
# client.hardware.tasks.create([sy_analog_task])
# print("created new")
print("configured")
exit(1)
# print(sy_analog_task)
# print(sy_analog_task.config)
# print(type(sy_analog_task.config))
# config = eval(sy_analog_task.config)
# print(config)
# config["channels"].append(new_pt_channel)
sy_analog_task.config = json.dumps(config, default=lambda o: o.__dict__)
client.hardware.tasks.configure(sy_analog_task)

"""
    - query synnax for devices (done)
    - query synnax for tasks based on devices (done)
    - read in excel file 
    - populate tasks based on excel file
    - configure tasks with new channels
    - create/configure tasks in synnax
"""

exit(1)

# pt_channel = AIVoltageChan(port=4, channel=4, device=analog_card.key)
# analog_task.config.channels.append(pt_channel)
# print("appended pt_channel", pt_channel.port, pt_channel.channel, pt_channel.device)

sy_ar_task = client.hardware.tasks.create([analog_task])[0]
print("sy_ar_task = ", sy_ar_task)
sy_dr_task = client.hardware.tasks.create([digital_read_task])[0]
print("sy_dr_task = ", sy_dr_task)
sy_dw_task = client.hardware.tasks.create([digital_write_task])[0]
print("sy_dw_task = ", sy_dw_task)

exit(1)

def main():
    NUMBER_OF_ITEMS = 4 #change to take in input and then put into the function
    # input_excel(r"C:\Users\ruchi\mcnugget\archive\cli\testing.xlsx", NUMBER_OF_ITEMS) #change to take in input and then put into the function
    input_excel("/Users/evanhekman/masa/testing.xlsx", 4)

def input_excel(file_path: str, item_num: int):
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError as e:
        print("File not found:", e)
        return
    except ValueError as e:
        print("Invalid Excel file or format:", e)
        return
    except Exception as e:
        print("Check sheet read in:", e)
        return
    
    df = df.drop('Type', axis=1)
    df_new = df.head(item_num) 
    print("Excel file succesfully read.")
    process_excel(df_new)

def process_excel(file: pd.DataFrame):
    print(f"reading {len(file)} rows")
    for _, row in file.iterrows():
        print(len(row), row)
        try:
            if row["Sensor Type"] == "VLV":
                populate_digital(row)
            elif row["Sensor Type"] in ["PT", "TC", "LC"]:
                populate_analogue(row)
            else:
                print("Check Sensor Type in Sheet")
        except KeyError as e:
            print(f"Missing column in row: {e}")
            return
        except Exception as e:
            print(f"Error populating tasks: {e}")
            # return

def populate_digital(row):
    port = int(row["Port"])
    channel = int(row["Channel"])

    vlv_di_channel = DIChan()
    vlv_di_channel.channel = channel
    vlv_di_channel.port = channel / 8
    vlv_di_channel.line = channel % 8
    digital_read_task.config.channels.append(vlv_di_channel)

    vlv_do_channel = DOChan()
    vlv_do_channel.cmd_channel = channel
    vlv_do_channel.state_channel = channel
    vlv_do_channel.port =  (channel / 8) + 4
    vlv_do_channel.line = channel % 8
    digital_write_task.config.channels.append(vlv_do_channel)
    print("Added VLV channel")

def populate_analogue(row):
    if row["Sensor Type"] == "TC":
        volt_lst, temp_lst = process_tc_poly()

        tc_channel = AIVoltageChan(port=row["Port"], channel=row["Channel"], device=analog_card.key)
        tc_channel.units = "Volts"
        tc_channel.custom_scale = TableScale(
            pre_scaled_vals = volt_lst,
            scaled_vals = temp_lst,
            pre_scaled_units = "Volts",
        )
   
        analog_task.config.channels.append(tc_channel)
        # print("Added TC channel")
    elif row["Sensor Type"] == "PT":
        pt_channel = AIVoltageChan(port=row["Port"], channel=row["Channel"], device=analog_card.key)
        pt_channel.units = "Volts"
        pt_channel.custom_scale = LinScale(
            slope = row["Calibration Slope (mV/psig)"] * .0001, 
            y_intercept = row["Calibration Offset (V)"],
            pre_scaled_units = "Volts",
            scaled_units = "PoundsPerSquareInch"
        )
        analog_task.config.channels.append(pt_channel)
        print("Added PT channel", pt_channel.port, pt_channel.channel, pt_channel.device)
    elif row["Sensor Type"] == "LC":
        print("LC channels not yet supported")

def process_tc_poly():
    # choose expression for each TC (read in voltage)
    # dep on voltage, we compute polynomials
    # conv to list and return (alr have this logic)

    mv = 1.234    
    range_values = {
        (-6.3, -4.648): { 
            "T0": -192.43000, "V0": -5.4798963,
            "p1": 59.572141, "p2": 1.9675733, "p3": -78.176011, "p4": -10.963280,
            "q1": 0.27498092, "q2": -1.3768944, "q3": -0.45209805
        },
        (-4.648, 0.0): {
            "T0": -60.000000, "V0": -2.1528350,
            "p1": 30.449332, "p2": -1.2946560, "p3": -3.0500735, "p4": -0.19226856,
            "q1": 0.0069877863, "q2": -0.10596207, "q3": -0.010774995
        },
        (0.0, 9.288): {
            "T0": 135.00000, "V0": 5.9588600,
            "p1": 20.325591, "p2": 3.3013079, "p3": 0.12638462, "p4": -0.00082883695,
            "q1": 0.17595577, "q2": 0.0079740521, "q3": 0.0   
        },
        (9.288, 20.872): {
            "T0": 300.00000, "V0": 14.861780,
            "p1": 17.214707, "p2": -0.93862713, "p3": -0.073509066, "p4": 0.0002957614,
            "q1": -0.048095795, "q2": -0.0047352054, "q3": 0.0
        }
    }

    
    mv_vals = None
    for r in range_values.keys():
        if r[0] <= mv and mv < r[1]:
            mv_vals = range_values[r]

    # if mv_vals is not None:
    #     mvv0 = mv - mv_vals["V0"]
    #     numerator = mvv0 * (mv_vals["p1"] + mvv0 * (mv_vals["p2"] + mvv0 * (mv_vals["p3"] + mv_vals["p4"] * mvv0)))
    #     denominator = 1 + mvv0 * (mv_vals["q1"] + mvv0 * (mv_vals["q2"] + (mv_vals["q3"] * mvv0)))
    #     celsius = mv_vals["T0"] + (numerator / denominator)
        
    voltage_range = (-6.3, 20.872)
    num_points = 1000

    voltages = np.linspace(voltage_range[0], voltage_range[1], num_points)
    volt_lst = list(voltages)

    temp_lst = []
    for v in voltages:
        if mv_vals is not None:
            mvv0 = mv - mv_vals["V0"]
            numerator = mvv0 * (mv_vals["p1"] + mvv0 * (mv_vals["p2"] + mvv0 * (mv_vals["p3"] + mv_vals["p4"] * mvv0)))
            denominator = 1 + mvv0 * (mv_vals["q1"] + mvv0 * (mv_vals["q2"] + (mv_vals["q3"] * mvv0)))
            celsius = mv_vals["T0"] + (numerator / denominator)
        temp_lst.append(celsius)

    return volt_lst, temp_lst


# syn_ar_task = client.hardware.tasks.create([ar_task])[0]
# print("z")
# print("ar_task = ", syn_ar_task)
# print("ar_task = ", ar_task)
# client.hardware.tasks.configure(syn_ar_task)

# client.hardware.tasks.create([dr_task])
# client.hardware.tasks.create([dw_task])

# FOR DEBUGGING PURPOSES
def print_df(file: pd.DataFrame):
    print(file.to_string())

    # print("The Name Row: ")
    # print(file["Name"])

    # print("Row 1: ")
    # print(file.loc[1])