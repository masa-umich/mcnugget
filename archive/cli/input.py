import pandas as pd
import synnax as sy
from synnax.hardware.ni import types
# from mcnugget.client import client
import numpy as np
from synnax.hardware.device import Device

client = sy.Synnax()

"""
- query synnax for devices
- query synnax for tasks based on devices
- 
"""

analog_card = client.hardware.devices.retrieve(name="PCI-6225")
digital_card = client.hardware.devices.retrieve(name="PCI-6514")
print("analog_card = ", analog_card)
print("digital_card = ", digital_card)

ar_task = types.AnalogReadTask(
    name = "Analog Read Task",
    # device = "01875AD0", 
    sample_rate = sy.Rate.HZ * 50,
    stream_rate = sy.Rate.HZ * 10,
    data_saving = True,
    channels = []
)


dr_task = types.DigitalReadTask(
    name = "Digital Read Task",
    device = digital_card.key, 
    sample_rate = sy.Rate.HZ * 50,
    stream_rate = sy.Rate.HZ * 10,
    data_saving = True,
    channels = []
)

dw_task = types.DigitalWriteTask(
    name = "Digital Write Task",
    device = digital_card.key, 
    state_rate = sy.Rate.HZ * 50,
    data_saving = True,
    channels = []
)   

pt_channel = types.AIVoltageChan(port=4, channel=4, device=analog_card.key)
ar_task.config.channels.append(pt_channel)
print("appended pt_channel", pt_channel.port, pt_channel.channel, pt_channel.device)

sy_ar_task = client.hardware.tasks.create([ar_task])[0]
print("sy_ar_task = ", sy_ar_task)
sy_dr_task = client.hardware.tasks.create([dr_task])[0]
print("sy_dr_task = ", sy_dr_task)
sy_dw_task = client.hardware.tasks.create([dw_task])[0]
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
    print("Added VLV channel")

def populate_analogue(row):
    if row["Sensor Type"] == "TC":
        volt_lst, temp_lst = process_tc_poly()

        tc_channel = types.AIVoltageChan(port=row["Port"], channel=row["Channel"], device=analog_card.key)
        tc_channel.units = "Volts"
        tc_channel.custom_scale = types.TableScale(
            pre_scaled_vals = volt_lst,
            scaled_vals = temp_lst,
            pre_scaled_units = "Volts",
        )
   
        ar_task.config.channels.append(tc_channel)
        # print("Added TC channel")
    elif row["Sensor Type"] == "PT":
        pt_channel = types.AIVoltageChan(port=row["Port"], channel=row["Channel"], device=analog_card.key)
        pt_channel.units = "Volts"
        pt_channel.custom_scale = types.LinScale(
            slope = row["Calibration Slope (mV/psig)"] * .0001, 
            y_intercept = row["Calibration Offset (V)"],
            pre_scaled_units = "Volts",
            scaled_units = "PoundsPerSquareInch"
        )
        ar_task.config.channels.append(pt_channel)
        print("Added PT channel", pt_channel.port, pt_channel.channel, pt_channel.device)
    elif row["Sensor Type"] == "LC":
        print("LC channels not yet supported")

def process_tc_poly():
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













if __name__ == "__main__":
    main()

