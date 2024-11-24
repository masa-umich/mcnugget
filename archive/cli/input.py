import pandas as pd
import synnax as sy
from synnax.hardware.ni import types
# from mcnugget.client import client
import numpy as np

client = sy.Synnax()

# print(client.hardware.tasks.retrieve().name)
# print(client.hardware.tasks.retrieve().key)
# print(client.hardware.tasks.retrieve().config)
# print(client.hardware.devices.retrieve(location="Dev1"))
ar_task = types.AnalogReadTask(
    name = "Analog Read Task",
    device = "01875AD0", 
    sample_rate = sy.Rate.HZ * 50,
    stream_rate = sy.Rate.HZ * 10,
    data_saving = True,
    channels = []
)


dr_task = types.DigitalReadTask(
    name = "Digital Read Task",
    device = "PCI-6514", 
    sample_rate = sy.Rate.HZ * 50,
    stream_rate = sy.Rate.HZ * 10,
    data_saving = True,
    channels = []
)

dw_task = types.DigitalWriteTask(
    name = "Digital Write Task",
    device = "PCI-6514", 
    state_rate = sy.Rate.HZ * 50, # CONFIRM
    data_saving = True,
    channels = []
)   


def main():
    NUMBER_OF_ITEMS = 4 #change to take in input and then put into the function
    input_excel(r"C:\Users\ruchi\mcnugget\archive\cli\testing.xlsx", NUMBER_OF_ITEMS) #change to take in input and then put into the function

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
    for _, row in file.iterrows():
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

        tc_channel = types.AIVoltageChan(port=row["Port"], channel=row["Channel"])
        tc_channel.units = "Volts"
        tc_channel.custom_scale = types.TableScale(
            pre_scaled_vals = volt_lst,
            scaled_vals = temp_lst,
            pre_scaled_units = "Volts",
        )
   
        ar_task.config.channels.append(tc_channel)
        # print("Added TC channel")
    elif row["Sensor Type"] == "PT":
        pt_channel = types.AIVoltageChan(port=row["Port"], channel=row["Channel"])
        pt_channel.units = "Volts"
        pt_channel.custom_scale = types.LinScale(
            slope = row["Calibration Slope (mV/psig)"] * .0001, 
            y_intercept = row["Calibration Offset (V)"],
            pre_scaled_units = "Volts",
            scaled_units = "PoundsPerSquareInch"
        )
        ar_task.config.channels.append(pt_channel)
        print("Added PT channel")
    elif row["Sensor Type"] == "LC":
        print("Added LC channel")

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


syn_ar_task = client.hardware.tasks.create([ar_task])[0]
print("z")
print("ar_task = ", syn_ar_task)
print("ar_task = ", ar_task)
client.hardware.tasks.configure(syn_ar_task)


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

