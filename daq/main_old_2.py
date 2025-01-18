import synnax as sy
from synnax.hardware import ni
import pandas as pd

client = sy.Synnax(
    host="masasynnax.ddns.net", port=9090, username="synnax", password="seldon"
)

analog_card = client.hardware.devices.retrieve(name="Analog")
digital_card = client.hardware.devices.retrieve(name="Digital")

# Timestamp channel
gse_ai_time = client.channels.create(
    name="gse_ai_time",
    is_index=True,
    data_type=sy.DataType.TIMESTAMP,
    retrieve_if_name_exists=True,
)

ai_voltage_time = client.channels.create(
    name="gse_ai_time",
    is_index=True,
    data_type=sy.DataType.TIMESTAMP,
    retrieve_if_name_exists=True,
)

ai_voltage_synnax_channel = client.channels.create(
    name="ai_voltage_chan",
    index=ai_voltage_time.key,
    data_type=sy.DataType.FLOAT32,
    retrieve_if_name_exists=True,
)

ai_voltage_chan = ni.AIVoltageChan(
    channel=ai_voltage_synnax_channel.key,
    device=analog_card.key,
    port=13,
    custom_scale=ni.LinScale(
        slope=2e4,
        y_intercept=50,
        pre_scaled_units="Volts",
        scaled_units="Volts",
    ),
)

# create analog read task
analog_task = ni.AnalogReadTask(
    name="Analog Read Task",
    sample_rate=sy.Rate.HZ * 50,
    stream_rate=sy.Rate.HZ * 10,
    data_saving=True,
    channels=[ai_voltage_chan],
)

do_1_cmd = client.channels.create(
    name="do_1_cmd",
    data_type=sy.DataType.UINT8,
    retrieve_if_name_exists=True,
    virtual=True,
)

do_state_time = client.channels.create(
    name="do_state_time",
    is_index=True,
    data_type=sy.DataType.TIMESTAMP,
    retrieve_if_name_exists=True,
)

do_1_state = client.channels.create(
    name="do_1_state",
    index=do_state_time.key,
    data_type=sy.DataType.UINT8,
    retrieve_if_name_exists=True,
)

magic_chan = ni.DOChan(
    channel=do_1_cmd.key,
    cmd_channel=do_1_cmd.key,
    state_channel=do_1_state.key,
    port=6,
    line=7,
)

# # Create digital write task
digital_write_task = ni.DigitalWriteTask(
    name="Digital Write Task",
    device=digital_card.key,
    state_rate=sy.Rate.HZ * 50,
    data_saving=True,
    channels=[magic_chan],
)
print(digital_write_task.config)

client.hardware.tasks.configure(digital_write_task)
client.hardware.tasks.configure(analog_task)


# def main():
#     NUMBER_OF_ITEMS = 4  # change to take in input and then put into the function
#     # input_excel(r"C:\Users\ruchi\mcnugget\archive\cli\testing.xlsx", NUMBER_OF_ITEMS) #change to take in input and then put into the function
#     input_excel("/Users/evanhekman/masa/testing.xlsx", 4)


# def input_excel(file_path: str, item_num: int):
#     try:
#         df = pd.read_excel(file_path)
#     except FileNotFoundError as e:
#         print("File not found:", e)
#         return
#     except ValueError as e:
#         print("Invalid Excel file or format:", e)
#         return
#     except Exception as e:
#         print("Check sheet read in:", e)
#         return

#     df_new = df.head(item_num)
#     print("Excel file succesfully read.")
#     process_excel(df_new)


# def process_excel(file: pd.DataFrame):
#     print(f"reading {len(file)} rows")
#     for _, row in file.iterrows():
#         ai_0 = client.channels.create(
#             name="ai_0",
#             # Pass in the index key here to associate the channel with the index channel.
#             index=gse_ai_time.key,
#             data_type=sy.DataType.FLOAT32,
#             retrieve_if_name_exists=True,
#         )
#         print(len(row), row)
#         try:
#             if row["Sensor Type"] == "VLV":
#                 populate_digital(row)
#             elif row["Sensor Type"] in ["PT", "TC", "LC"]:
#                 populate_analogue(row)
#             else:
#                 print("Check Sensor Type in Sheet")
#         except KeyError as e:
#             print(f"Missing column in row: {e}")
#             return
#         except Exception as e:
#             print(f"Error populating tasks: {e}")
