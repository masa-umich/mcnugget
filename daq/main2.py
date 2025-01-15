import synnax as sy
from synnax.hardware import ni
import pandas as pd

client = sy.Synnax(
    host="masasynnax.ddns.net", port=9090, username="synnax", password="seldon"
)

analog_card = client.hardware.devices.retrieve(name="PCI-6225")
digital_card = client.hardware.devices.retrieve(name="PCI-6514")

# Timestamp channel
gse_ai_time = client.channels.create(
    name="gse_ai_time",
    is_index=True,
    data_type=sy.DataType.TIMESTAMP,
    retrieve_if_name_exists=True,
)

# create analog read task
analog_task = ni.AnalogReadTask(
    name="Analog Read Task",
    sample_rate=sy.Rate.HZ * 50,
    stream_rate=sy.Rate.HZ * 10,
    data_saving=True,
    channels=[],
)

# create digital read task
digital_read_task = ni.DigitalReadTask(
    name="Digital Read Task",
    device=digital_card.key,
    sample_rate=sy.Rate.HZ * 50,
    stream_rate=sy.Rate.HZ * 10,
    data_saving=True,
    channels=[],
)

# Create digital write task
digital_write_task = ni.DigitalWriteTask(
    name="Digital Write Task",
    device=digital_card.key,
    state_rate=sy.Rate.HZ * 50,
    data_saving=True,
    channels=[],
)

client.hardware.tasks.configure(analog_task)
client.hardware.tasks.configure(digital_read_task)
client.hardware.tasks.configure(digital_write_task)


def main():
    NUMBER_OF_ITEMS = 4  # change to take in input and then put into the function
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

    df_new = df.head(item_num)
    print("Excel file succesfully read.")
    process_excel(df_new)


def process_excel(file: pd.DataFrame):
    print(f"reading {len(file)} rows")
    for _, row in file.iterrows():
        ai_0 = client.channels.create(
            name="ai_0",
            # Pass in the index key here to associate the channel with the index channel.
            index=gse_ai_time.key,
            data_type=sy.DataType.FLOAT32,
            retrieve_if_name_exists=True,
        )
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
