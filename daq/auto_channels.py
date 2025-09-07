#
# auto_channels.py
# 
# Created on: March 1, 2025
# Author: jackmh
#
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

# hello, I know this is stupid but I don't know how else for there to be like a fail-over from the client details and the EBox :)
try:
    client = sy.Synnax()
except:
    try:
        client = sy.Synnax(
            host="synnax.masa.engin.umich.edu", port=9090, username="synnax", password="seldon"
        )
    except:
        pass
    spinner.stop()
    raise Exception(colored("Error initializing Synnax client, are you sure you're connected? Type `synnax login` to login", "red"))

# Configuration
polling_rate = 50 # Hz

analog_task_name = "Sensors"
analog_card_model = "PCI-6225"

digital_task_name = "Valves"
digital_card_model = "PCI-6514"

def main():
    analog_task, digital_task, analog_card = create_tasks()
    spinner.stop()
    sheet = get_sheet(input(colored("Path to instrumentation sheet or URL to ICD: ", "cyan")))
    spinner.text = colored("Processing sheet...", "green")
    spinner.start()
    channels = process_sheet(sheet)
    selection = prompt_calibrations()
    setup_channels(channels)
    
    
    #calibrations = get_old_calibrations("PTs and TCs")
    #setup_channels(channels, calibrations, digital_task, analog_task, analog_card)

def create_tasks():
    spinner.text = "Scanning for cards..."
    time.sleep(0.1)
    try:
        analog_card = client.hardware.devices.retrieve(model=analog_card_model)
        spinner.text = colored("Analog card " + analog_card.make + " " + analog_card.model + " found! ✅", "green")
        time.sleep(0.1)
    except:
        raise Exception(colored("Analog card " + analog_card_model + " not found, are you sure it's connected? Maybe try re-enabling the NI Device Scanner.", "red"))
    
    try:
        digital_card = client.hardware.devices.retrieve(model=digital_card_model)
        spinner.text = colored("Digital card " + digital_card.make + " " + digital_card.model + " found! ✅", "green")
        time.sleep(0.1)
    except:
        raise Exception(colored("Digital card " + digital_card_model + " not found, are you sure it's connected? Maybe try re-enabling the NI Device Scanner.", "red"))

    analog_task = ni.AnalogReadTask(
        name=analog_task_name,
        sample_rate=sy.Rate.HZ * polling_rate,
        stream_rate=sy.Rate.HZ * polling_rate/2,
        data_saving=True,
        channels=[],
    )
    digital_task = ni.DigitalWriteTask(
        name=digital_task_name,
        device=digital_card.key,
        state_rate=sy.Rate.HZ * polling_rate,
        data_saving=True,
        channels=[],
    )
    return analog_task, digital_task, analog_card

def get_sheet(sheet_path: str):
    if "docs.google.com" in sheet_path:
        raise Exception("Google Sheets not supported yet, please download as Excel file")
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
            df = pd.read_excel(sheet_path, header=1, sheet_name="AVI GSE Mappings", index_col=[0])
            # we also add index_col=0 to handle the merged cells for sensor type
        except FileNotFoundError as e:
            raise Exception(colored("File not found: " + sheet_path, "red"))
        
    return df.head(300) # god forbid we have more than 300 channels

def process_sheet(file: pd.DataFrame):
    # makes dict of channels and relevant data
    channels = []
    spinner.text = colored("Processing sheet...", "green")
    time.sleep(0.1)
    setup_thermistor = False
    for _, row in file.iterrows():
        spinner.text = colored("Processing row...", "green")

        # handle invalid rows
        if row["Channel"] == "" or row["Name"] == "":
            spinner.text = colored("Skipping row with no channel or name...", "yellow")
            time.sleep(0.1)
            continue
        try:
            if "MARGIN" in row["Name"]:
                spinner.text = colored("Skipping margin channel...", "yellow")
                time.sleep(0.1)
                continue
        except:
            continue

        try:
            channel_num = int(row["Channel"])
            if row.name == "PTs" or row.name == "PT":
                spinner.text = colored("Processing PT " + row["Name"] + "...", "green")
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
            elif row.name == "VLVs" or row.name == "VLV":
                spinner.text = colored("Processing VLV " + row["Name"] + "...", "green")
                #time.sleep(0.1)
                if channel_num >= 17:
                    port = 6
                elif channel_num >= 9:
                    port = 5
                elif channel_num >= 0:
                    port = 4
                else:
                    raise Exception("Invalid channel number for valve " + row["Name"])
                channel = {
                    "name": row["Name"],
                    "type": "VLV",
                    "channel": channel_num,
                    "port": port,
                    "line": (channel_num - 1) % 8
                }
                channels.append(channel)
            elif row.name == "TCs" or row.name == "TC":
                if not setup_thermistor:
                    spinner.text = colored("Setting up thermistor...", "green")
                    #time.sleep(0.1)
                    channel = {
                        "type": "Thermistor",
                        "name": "Thermistor",
                        "port": 79,
                        "max": 10,
                        "min": -10
                    }
                    setup_thermistor = True
                    channels.append(channel)
                spinner.text = colored("Processing TC " + row["Name"] + "...", "green")
                #time.sleep(0.1)
                channel = {
                    "name": row["Name"],
                    "type": "TC",
                    "channel": channel_num,
                    "port": channel_num - 1 + 64,
                    "max": 10,
                    "min": -10
                }
                channels.append(channel)
            elif row.name == "LCs" or row.name == "LC":
                spinner.text = colored("Load cells not supported yet, skipping...", "yellow")
                #time.sleep(0.1)
            else:
                print(f"Sensor type {row.name} not recognized")
        except KeyError as e:
            print(f"Missing column in row: {e} skipping...")
        except Exception as e:
            print(f"Error populating tasks: {e} skipping...")
    return channels

def prompt_calibrations():
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

    if answer == "1":
        return 1
    elif answer == "2":
        return 2
    elif answer == "3" and old_analog_task != None:
        return 3
    else:
        print(colored("Invalid selection, please try again", "red"))
        prompt_calibrations()

def setup_channels(channels):
    yes_to_all = False # create new synnax channels for all items in the sheet?

    for channel in channels:
        if channel["type"] == "PT":
            print("PT")
        elif channel["type"] == "VLV":
            print("VLV")
        elif channel["type"] == "TC":
            print("LC")
        elif channel["type"] == "Thermistor":
            print("Thermistor")
        else:
            raise Exception(f"Sensor type {channel["type"]} in channels dict not recognized (issue with the script)")

def get_factory_calibration(channels):
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

def get_ambient_calibration(channels):
    # temporarily setup a task with all channels
    # start it and read for a couple seconds to get an average value
    # then stop & delete the task, return the calibration values

    spinner.text = colored("Setting up task for ambient calibration...", "green")

def get_old_calibrations(task_name: str):
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

    #client.hardware.tasks.delete(task.key)

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
}

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("Shutting down...", "red"))
        exit()
    spinner.stop()