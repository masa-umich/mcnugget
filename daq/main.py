import synnax as sy
from synnax.hardware import ni
import pandas as pd
from daq.processing import process_vlv, process_pt, process_tc, process_lc, process_raw

client = sy.Synnax()


def main():
    data = input_excel("Phoenix Torch Igniter Hotfire SOP.xlsx")
    analog_task, digital_task, analog_card = create_tasks()
    process_excel(data, analog_task, digital_task, analog_card)
    if analog_task.config.channels != []:  # only configure if there are channels
        print("Attempting to configure analog task")
        client.hardware.tasks.configure(
            task=analog_task, timeout=60
        )  # long timeout cause our NI hardware is dumb
        print("Successfully configured analog task")
    if digital_task.config.channels != []:
        print("Attempting to configure digital task")
        client.hardware.tasks.configure(task=digital_task, timeout=5)
        print("Successfully configured digital task")
    print("jubilate")


def create_tasks():
    analog_card = client.hardware.devices.retrieve(name="Analog")
    digital_card = client.hardware.devices.retrieve(name="Digital")
    analog_task = ni.AnalogReadTask(
        name="Analog Input",
        sample_rate=sy.Rate.HZ * 50,
        stream_rate=sy.Rate.HZ * 25,
        data_saving=True,
        channels=[],
    )
    digital_task = ni.DigitalWriteTask(
        name="Valve Control",
        device=digital_card.key,
        state_rate=sy.Rate.HZ * 50,
        data_saving=True,
        channels=[],
    )
    return analog_task, digital_task, analog_card


def input_excel(file_path: str):
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

    print("Excel file succesfully read.")
    return df.head(300)


def process_excel(
    file: pd.DataFrame,
    analog_task: ni.AnalogReadTask,
    digital_task: ni.DigitalWriteTask,
    analog_card: sy.Device,
):
    print(f"reading {len(file)} rows")
    setup_thermistor = False

    for _, row in file.iterrows():
        try:
            if row["Sensor Type"] == "VLV":
                process_vlv(row, digital_task)
            elif row["Sensor Type"] == "PT":
                process_pt(row, analog_task, analog_card)
            elif row["Sensor Type"] == "TC":
                if not setup_thermistor:
                    thermistor(analog_task, analog_card)
                    setup_thermistor = True
                process_tc(row, analog_task, analog_card)
            elif row["Sensor Type"] == "LC":
                process_lc(row, analog_task, analog_card)
            # elif (
            #     row["Sensor Type"] == "RAW"
            # ):  # for thermister and other raw voltage data
            #     process_raw(row, analog_task, analog_card)
            else:
                print(f"Sensor type {row["Sensor Type"]} not recognized")
        except KeyError as e:
            print(f"Missing column in row: {e}")
            return
        except Exception as e:
            print(f"Error populating tasks: {e}")


def thermistor(analog_task: ni.AnalogReadTask, analog_card: sy.Device):
    gse_ai_time = client.channels.create(
        name="gse_ai_time",
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
        is_index=True,
    )
    therm_supply = client.channels.create(
        name="gse_thermistor_supply",
        data_type=sy.DataType.FLOAT32,
        index=gse_ai_time.key,
        retrieve_if_name_exists=True,
    )
    therm_signal = client.channels.create(
        name="gse_thermistor_signal",
        data_type=sy.DataType.FLOAT32,
        index=gse_ai_time.key,
        retrieve_if_name_exists=True,
    )
    analog_task.config.channels.append(
        ni.AIVoltageChan(
            channel=therm_supply.key,
            device=analog_card.key,
            port=79,
            min_val=-10,
            max_val=10,
            terminal_config="RSE",
        ),
    )
    analog_task.config.channels.append(
        ni.AIVoltageChan(
            channel=therm_signal.key,
            device=analog_card.key,
            port=78,
            min_val=0,
            max_val=5,
            terminal_config="RSE",
        ),
    )
    print("created thermistor signal and supply channels")


main()
