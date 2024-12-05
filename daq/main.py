import pandas as pd
import synnax as sy
from synnax.hardware.ni.types import *
import numpy as np
from synnax.hardware.device import Device
import ast
from pt_configuration import configure_pt_channel
from tc_configuration import configure_tc_channel, process_tc_poly
from lc_configuration import configure_lc_channel

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
        configure_tc_channel(analog_task, row, analog_card)
        print("Added TC channel")
    elif row["Sensor Type"] == "PT":
        configure_pt_channel(analog_task, row, analog_card)
    elif row["Sensor Type"] == "LC":
        configure_lc_channel(analog_task, row, analog_card)

if __name__ == "__main__":
    main()
