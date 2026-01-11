#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pandas",
#     "synnax==0.46.0",
#     "termcolor",
#     "yaspin",
#     "openpyxl"
# ]
# ///

#
# How do I run this script?!
# 1. Install the program "uv" from this link:
#    https://docs.astral.sh/uv/getting-started/installation/
# 2. Navigate to the `mcnugget/auto-channels` directory
# 3. Download the ICD (or another valid sheet) as a .xlsx file
# 4. Type `./auto_channels.py` in your terminal and press enter
# 5. Follow the prompts and enjoy!
# If you have any problems, report to Jack on Slack
# 

#
# auto-channels.py
# 
# Last updated: Nov 27, 2025
# Author: jackmh
#

import argparse
from termcolor import colored
from yaspin import yaspin
# Adds a fun spinner :)
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

# making this seperate because just importing packages in python can take a while and we want to show the spinner
import pandas as pd
import synnax as sy
import json
import time
from synnax.hardware import ni

verbose: bool = False # global setting (default = False)
analog_task_name: str = "Sensors"
analog_card_model: str = "PCI-6225"

digital_task_name: str = "Valves"
digital_card_model: str = "PCI-6514"

calibration_read_time: int = 5

@yaspin(text=colored("Logging onto Synnax cluster...", "yellow"))
def synnax_login(cluster: str) -> sy.Synnax:
    try:
        client = sy.Synnax(
            host=cluster,
            port=9090,
            username="synnax",
            password="seldon",
        )
    except Exception as e:
        raise(
            f"Could not connect to Synnax at {cluster}, are you sure you're connected?"
        )
    return client  # type: ignore

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="The autosequence for preparring Limeight for launch!"
    )
    parser.add_argument(
        "-c",
        "--cluster",
        help="Specify a Synnax cluster to connect to",
        type=str,
        default="synnax.masa.engin.umich.edu"
    )
    parser.add_argument(
        "-i",
        "--icd",
        help="Specify an ICD or instrumentation file to use",
        type=str,
        default=""
    )
    parser.add_argument(
        "-f",
        "--frequency",
        help="Specify a frequency to read & write data at (Hertz)",
        type=int,
        default=50
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Shold the program output extra debugging information",
        action="store_true"
    )  # Positional argument
    args = parser.parse_args()
    if (args.verbose):
        verbose = True # set global
    return args

def main():
    args = parse_args()
    client = synnax_login(args.cluster)
    analog_task, digital_task, analog_card = create_tasks(client, args.frequency)
    if (args.icd == ""):
        file_path = input(colored("Path to instrumentation sheet or URL to ICD: ", "cyan"))
    else:
        file_path = args.icd
    sheet = get_sheet(file_path)
    channels = process_sheet(sheet)
    setup_channels(client, channels, analog_task, digital_task, analog_card)
    calibrations = handle_calibrations(prompt_calibrations(client), client, channels, analog_task, args.frequency)
    apply_calibrations(calibrations, analog_task)
    configure_tasks(client, analog_task, digital_task)

def create_tasks(client: sy.Synnax, frequency: int):
    spinner.text = "Creating tasks..."
    spinner.write(colored(" > Scanning for cards...", "cyan"))
    time.sleep(0.1)
    try:
        analog_card = client.hardware.devices.retrieve(model=analog_card_model)
        spinner.write(colored(" > Analog card '" + analog_card.make + " " + analog_card.model + "' found! ✅", "green", attrs=["bold"]))
        time.sleep(0.1)
    except:
        raise Exception(colored("Analog card '" + analog_card_model + "' not found, are you sure it's connected? Maybe try re-enabling the NI Device Scanner.", "red", attrs=["bold"]))
    
    try:
        digital_card = client.hardware.devices.retrieve(model=digital_card_model)
        spinner.write(colored(" > Digital card '" + digital_card.make + " " + digital_card.model + "' found! ✅", "green", attrs=["bold"]))
        time.sleep(0.1)
    except:
        raise Exception(colored("Digital card '" + digital_card_model + "' not found, are you sure it's connected? Maybe try re-enabling the NI Device Scanner.", "red", attrs=["bold"]))

    analog_task = ni.AnalogReadTask(
        name=analog_task_name,
        sample_rate=sy.Rate.HZ * frequency,
        stream_rate=sy.Rate.HZ * frequency/2,
        data_saving=True,
        channels=[],
    )

    digital_task = ni.DigitalWriteTask(
        name=digital_task_name,
        device=digital_card.key,
        state_rate=sy.Rate.HZ * frequency,
        data_saving=True,
        channels=[],
    )

    return analog_task, digital_task, analog_card

def get_sheet(sheet_path: str):
    spinner.start()
    spinner.text = colored("Reading sheet...", "magenta")
    if "docs.google.com" in sheet_path:
        raise Exception(colored("Google Sheets not supported yet, please download as Excel file and try again", "red", attrs=["bold"]))
        #SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        #flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        #creds = flow.run_local_server(port=0)
        # gspread_client = gspread.service_account("creds.json")
        # sheet = gspread_client.open_by_url(sheet_path)
        # vals = sheet.sheet1.get_all_values()
        # return pd.DataFrame(vals[1:], columns=vals[0])
        # try:
        #     df = pd.read_csv(sheet_path)
        # except Exception as e:
        #     raise Exception("Error reading Google Sheet: " + e + " are you sure the URL is correct?")
    else: # assume it's an excel file
        try:
            # The ICD has a goofy formatting, we start header at 1 and mappings must be in "AVI GSE Mappings" sheet
            df = pd.read_excel(sheet_path, header=1, sheet_name="OLD AVI GSE Mappings 24-25", index_col=[0])
            # we also add index_col=0 to handle the merged cells for sensor type
        except FileNotFoundError as e:
            raise Exception(colored("File not found: " + sheet_path, "red"))
        
    spinner.write(colored(" > Successfully read sheet", "green", attrs=["bold"]))

    return df.head(300) # god forbid we have more than 300 channels

def process_sheet(file: pd.DataFrame):
    # makes dict of channels and relevant data
    channels = []
    spinner.text = colored("Processing sheet...", "magenta")
    time.sleep(0.1)
    setup_thermistor = False
    for _, row in file.iterrows():
        # handle invalid rows
        if row["Channel"] == "" or row["Name"] == "":
            spinner.write(colored(" > Skipping row with no channel or name...", "yellow"))
            time.sleep(0.1)
            continue
        try:
            if "MARGIN" in row["Name"]:
                spinner.write(colored(" > Skipping margin channel...", "yellow"))
                time.sleep(0.1)
                continue
            if "broken channel" in row["Name"]:
                spinner.write(colored(" > Skipping broken valve channel...", "yellow"))
                time.sleep(0.1)
                continue
        except:
            continue

        try:
            channel_num = int(row["Channel"])
            if row.name == "PTs" or row.name == "PT":
                #time.sleep(0.1)
                channel = {
                    "name": row["Name"],
                    "type": "PT",
                    "channel": channel_num,
                    "port": channel_num -1,
                    "max": int(row["Max Pressure"]),
                    "min": 0
                }
                channels.append(channel)
                spinner.write(colored(" > Found PT: " + row["Name"], "cyan"))
            elif row.name == "VLVs" or row.name == "VLV":
                #time.sleep(0.1)
                if channel_num >= 17:
                    port = 6
                elif channel_num >= 9:
                    port = 5
                elif channel_num >= 0:
                    port = 4
                else:
                    raise Exception("Invalid channel number for valve: " + row["Name"])
                channel = {
                    "name": row["Name"],
                    "type": "VLV",
                    "channel": channel_num,
                    "port": port,
                    "line": (channel_num - 1) % 8
                }
                channels.append(channel)
                spinner.write(colored(" > Found VLV: " + row["Name"], "cyan"))
            elif row.name == "TCs" or row.name == "TC":
                if not setup_thermistor:
                    #time.sleep(0.1)
                    channel = {
                        "type": "Thermistor",
                        "name": "Thermistor",
                        "signal": 78,
                        "supply": 79,
                        "max": 8,
                        "min": -8
                    }
                    setup_thermistor = True
                    channels.append(channel)
                    spinner.write(colored(" > Found thermistor", "cyan"))
                #time.sleep(0.1)
                channel = {
                    "name": row["Name"],
                    "type": "TC",
                    "channel": channel_num,
                    "port": channel_num - 1 + 64,
                    "max": 8,
                    "min": -8
                }
                channels.append(channel)
                spinner.write(colored(" > Found TC: " + row["Name"], "cyan"))
            elif row.name == "LCs" or row.name == "LC":
                spinner.write(colored(" > Load cells not supported yet, skipping...", "yellow"))
                #time.sleep(0.1)
            else:
                spinner.write(colored(f" > Sensor type {row.name} not recognized", "yellow"))
        except KeyError as e:
            spinner.write(colored(f"Missing column in row: {e} skipping...", "yellow"))
        except Exception as e:
            spinner.write(colored(f"Error populating tasks: {e} skipping...", "yellow"))
    spinner.write(colored(" > Finished parsing channels", "green", attrs=["bold"]))
    return channels

def prompt_calibrations(client: sy.Synnax):
    try:
        old_analog_task = client.hardware.tasks.retrieve(name=analog_task_name)
    except:
        old_analog_task = None

    spinner.stop()
    print(colored("What calibration settings would you like to apply for '" + analog_task_name + "' ?", "cyan"))
    print(colored("1 - Assume system is at ambient, get new calibration data (must have ALL sensors attached)", "cyan"))
    print(colored("2 - Use factory calibration data (can be incorrect)", "cyan"))
    if (old_analog_task != None):
        print(colored("3 - Use existing calibration data from last task", "cyan"))
    answer = input(colored("Selection: ", "cyan"))
    spinner.start()

    if answer == "1":
        return 1
    elif answer == "2":
        return 2
    elif answer == "3" and old_analog_task != None:
        return 3
    else:
        print(colored("Invalid selection, please try again", "red"))
        prompt_calibrations()

def handle_calibrations(selection: int, client: sy.Synnax, channels, analog_task, frequency: int):
    if selection == 1:
        return get_ambient_calibrations(client, channels, analog_task, frequency)
    elif selection == 2:
        return get_factory_calibrations(channels)
    elif selection == 3:
        return get_old_calibrations(client, "PTs and TCs")

def apply_calibrations(calibrations, analog_task):
    for channel in analog_task.config.channels:
        # same as in get_ambient_calibrations
        if not isinstance(channel.custom_scale, ni.types.NoScale) and channel.custom_scale.scaled_units == "PoundsPerSquareInch":
            channel.custom_scale = ni.LinScale(
                slope            = calibrations[channel.port]["slope"],
                y_intercept      = calibrations[channel.port]["offset"],
                pre_scaled_units = "Volts",
                scaled_units     = "PoundsPerSquareInch"
            )
            channel.max_val = calibrations[channel.port]["max_val"]
            channel.min_val = calibrations[channel.port]["min_val"]
    spinner.write(colored(" > Calibrations applied", "green", attrs=["bold"]))    

def setup_channels(client: sy.Synnax, channels, analog_task, digital_task, analog_card):
    spinner.text = "Creating channels in Synnax..."
    yes_to_all = False # create new synnax channels for all items in the sheet?

    for channel in channels:
        if channel["type"] == "PT":            
            spinner.write(colored(f" > Creating PT: {channel["name"]}", "cyan"))
            setup_pt(client, channel, analog_task, analog_card)
        elif channel["type"] == "VLV":
            spinner.write(colored(f" > Creating VLV: {channel["name"]}", "cyan"))
            setup_vlv(client, channel, digital_task)
        elif channel["type"] == "TC":
            spinner.write(colored(f" > Creating TC: {channel["name"]}", "cyan"))
            setup_tc(client, channel, analog_task, analog_card)
        elif channel["type"] == "Thermistor":
            spinner.write(colored(" > Creating Thermistor", "cyan"))
            setup_thermistor(client, channel, analog_task, analog_card)
        else:
            raise Exception(f"Sensor type {channel["type"]} in channels dict not recognized (issue with the script)")
    spinner.write(colored(" > Successfully created channels in Synnax", "green", attrs=["bold"]))

def get_factory_calibrations(channels):
    # assume slope and offset
    calibrations = {}
    spinner.text = colored("Calculating factory calibration data...", "green")    
    for channel in channels.items():
        channel = channel[1]
        type = channel["type"]
        if type == "PT":
            calibrations[channel["port"]] = {
                "slope": (channel["max"] / 4), # 0.5-4.5V
                "offset": -(channel["max"] / 4)*0.5, # assume 0 psi at exactly 0.5V
                "min_val": channel["min"],
                "max_val": channel["max"]
            }
        elif type == "TC":
            calibrations[channel["port"]] = tc_calibrations[str(channel["channel"])]
    return calibrations

def get_ambient_calibrations(client: sy.Synnax, channels, analog_task, frequency: int):
    # temporarily setup a task with all channels
    # start it and read for a couple seconds to get an average value
    # then stop & delete the task, return the calibration values

    spinner.text = colored("Starting task for ambient calibration...", "green")

    calibrations = {}
    channel_keys = {} # map channel name to (port, min, max)
    frame = sy.Frame()

    temp_task = ni.AnalogReadTask(
        name="Ambient calibration for PTs",
        sample_rate=sy.Rate.HZ * frequency,
        stream_rate=sy.Rate.HZ * frequency/2, # 2 samples at a time
        data_saving=False,
        channels=[]
    )

    for channel in analog_task.config.channels:
        # copy pt channels for temp_task from analog_task
        # surely there's a better way to check if channel is for a pt
        if not isinstance(channel.custom_scale, ni.types.NoScale) and channel.custom_scale.scaled_units == "PoundsPerSquareInch":
            temp_task.config.channels.append(channel)

    client.hardware.tasks.configure(task=temp_task, timeout=6000)
    
    temp_task.start()

    try:
        channel_names = []
        for channel in channels:
            if channel["type"] == "PT":
                channel_names.append(f"gse_pt_{channel["channel"]}")
                channel_keys[f"gse_pt_{channel["channel"]}"] = (channel["port"], channel["min"], channel["max"])
        with client.open_streamer(channel_names) as streamer:
            spinner.text = colored("Reading for ambient calibration...", "green")        
            for i in range(frequency//2 * calibration_read_time):
                frame.append(streamer.read())
    finally:
        spinner.text = colored("Stopping task for ambient calibration...", "green")
        temp_task.stop(timeout=30000)

    for channel in frame.to_df():
        calibrations[channel_keys[channel][0]] = {
            "slope": (channel_keys[channel][2] / 4),
            "offset": -frame.to_df()[channel].mean(),
            "min_val": float(channel_keys[channel][1]),
            "max_val": float(channel_keys[channel][2])
        }

#    with open(filename, 'w') as save_file:
#        json.dump(calibrations, save_file)

    return calibrations

def get_old_calibrations(client: sy.Synnax, task_name: str):
    spinner.text = colored("Retrieving calibrations...", "green")

    try:
        task = client.hardware.tasks.retrieve(name=task_name)
    except:
        raise Exception("Task " + task_name + " not found")
    try:
        config = json.loads(task.config)
    except json.JSONDecodeError as e:
        raise Exception(f"Error decoding JSON: {e}")

    calibrations = {}

    for channel in config["channels"]:
        if (channel["type"] == "ai_voltage") and (channel["custom_scale"]["type"] != "none"): # if it has a calibration
            calibrations[channel["port"]] = { # add to calibrations dict
                "slope": channel["custom_scale"]["slope"],
                "offset": channel["custom_scale"]["y_intercept"],
                "min_val": channel["min_val"],
                "max_val": channel["max_val"]
            }

    return task.key, calibrations

def setup_pt(client: sy.Synnax, channel, analog_task, analog_card):
    time_channel = client.channels.create(
        name="gse_sensor_time",
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
        is_index=True,
    )

    pt_channel = client.channels.create(
        name=f"gse_pt_{channel["channel"]}",
        data_type=sy.DataType.FLOAT32,
        index=time_channel.key,
        retrieve_if_name_exists=True,
    )

    analog_task.config.channels.append(
        ni.AIVoltageChan(
            channel=pt_channel.key,
            device=analog_card.key,
            port=channel["port"],
            custom_scale=ni.LinScale(
                slope=(
                    channel["max"] / 4.0 # slope is max output in psi over output range (4 volts for our PTs)
                ),
                y_intercept=(
                    -(channel["max"] / 4.0) * 0.5 # y intercept is negative slope at 0.5 volts
                ),
                pre_scaled_units="Volts",
                scaled_units="PoundsPerSquareInch",
            ),
            terminal_config="RSE",
            max_val=channel["max"],
            min_val=channel["min"],
        )
    )



def setup_vlv(client: sy.Synnax, channel, digital_task):
    gse_state_time = client.channels.create(
        name="gse_state_time",
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )

    state_chan = client.channels.create(
        name=f"gse_state_{channel["channel"]}",
        data_type=sy.DataType.UINT8,
        retrieve_if_name_exists=True,
        index=gse_state_time.key,
    )

    cmd_chan = client.channels.create(
        name=f"gse_vlv_{channel["channel"]}",
        data_type=sy.DataType.UINT8,
        retrieve_if_name_exists=True,
        virtual=True,
    )

    digital_task.config.channels.append(
        ni.DOChan(
            cmd_channel=cmd_chan.key,
            state_channel=state_chan.key,
            port=channel["port"],
            line=channel["line"],
        )
    )

def setup_thermistor(client: sy.Synnax, channel, analog_task, analog_card):
    time_channel = client.channels.create(
        name="gse_sensor_time",
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
        is_index=True,
    )

    therm_supply = client.channels.create(
        name="gse_thermistor_supply",
        data_type=sy.DataType.FLOAT32,
        index=time_channel.key,
        retrieve_if_name_exists=True,
    )

    therm_signal = client.channels.create(
        name="gse_thermistor_signal",
        data_type=sy.DataType.FLOAT32,
        index=time_channel.key,
        retrieve_if_name_exists=True,
    )

    analog_task.config.channels.append(
        ni.AIVoltageChan(
            channel=therm_supply.key,
            device=analog_card.key,
            port=channel["supply"],
            min_val=channel["min"],
            max_val=channel["max"],
            terminal_config="RSE",
        ),
    )

    analog_task.config.channels.append(
        ni.AIVoltageChan(
            channel=therm_signal.key,
            device=analog_card.key,
            port=channel["signal"],
            min_val=channel["min"],
            max_val=channel["max"],
            terminal_config="RSE",
        ),
    )


def setup_tc(client: sy.Synnax, channel, analog_task, analog_card):
    time_channel = client.channels.create(
        name="gse_sensor_time",
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
        is_index=True,
    )

    tc_channel = client.channels.create(
        name=f"gse_tc_{channel["channel"]}_raw",  # TCs without any CJC, CJC happens in a seperate script in real-time
        data_type=sy.DataType.FLOAT32,
        index=time_channel.key,
        retrieve_if_name_exists=True,
    )

    analog_task.config.channels.append(
        ni.AIVoltageChan(
            channel=tc_channel.key,
            device=analog_card.key,
            port=channel["port"],
            custom_scale=ni.LinScale(
                slope=tc_calibrations[str(channel["channel"])]["slope"],
                y_intercept=tc_calibrations[str(channel["channel"])]["offset"],
                pre_scaled_units="Volts",
                scaled_units="Volts",
            ),
            terminal_config="RSE",
            max_val=channel["max"],
        )
    )

def configure_tasks(client: sy.Synnax, analog_task, digital_task):
    spinner.text = "Configuring tasks... (this may take a while)"

    if analog_task.config.channels != []:  # only configure if there are channels
        spinner.write(colored(" > Attempting to configure analog task", "cyan"))
        client.hardware.tasks.configure(
            task=analog_task, timeout=6000
        )  # long timeout cause our NI hardware is dumb
        spinner.write(colored(" > Successfully configured analog task!", "green"))
    if digital_task.config.channels != []:
        spinner.write(colored(" > Attempting to configure digital task", "cyan"))
        client.hardware.tasks.configure(task=digital_task, timeout=500)
        spinner.write(colored(" > Successfully configured digital task!", "green"))
    spinner.write(colored(" > All tasks have been successfully created!", "green", attrs=["bold"]))

# putting this here so it doesn't take up space at the top
# hardcoded calibration data for thermocouples, 
# these should never really change because of how our converters work
tc_calibrations = {
    "1": {"slope": 1.721453951, "offset": -7.888645383},
    "2": {"slope": 1.717979575, "offset": -7.887206187},
    "3": {"slope": 1.749114263, "offset": -8.059569538},
    "4": {"slope": 1.746326017, "offset": -7.988352324},
    "5": {"slope": 1.758960807, "offset": -8.000751167},
    "6": {"slope": 1.723974665, "offset": -7.891630334},
    "7": {"slope": 1.703447212, "offset": -7.961173615},
    "8": {"slope": 1.725947472, "offset": -7.928342723},
    "9": {"slope": 1.223907933, "offset": -3.041473799},
    "10": {"slope": 1.163575088, "offset": -3.001507707},
    "11": {"slope": 1.183121251, "offset": -2.962919485},
    "12": {"slope": 1.255762908, "offset": -2.436113303},
    "13": {"slope": 1.209157541, "offset": -3.018604306},
    "14": {"slope": 1.154169121, "offset": -2.924291025},
}

if __name__ == "__main__":
    spinner.stop()
    try:
        main()
    except KeyboardInterrupt:
        print(colored("Shutting down...", "red"))
        exit()
    spinner.stop()
