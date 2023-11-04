import pandas as pd
import synnax as sy
import gspread
from gspread import Spreadsheet
from synnax.telem import DataType
import sys
import time
from synnax import Synnax

client = Synnax()

NAME_COL = 0
ALIAS_COL = 1
DEVICE_COL = 2
PORT_COL = 3
DATA_TYPE_COL = 4
SENSOR_TYPE_COL = 5
UNITS_COL = 6
PT_SLOPE_COL = 7
PT_OFFSET_COL = 8
TC_TYPE_COL = 9
TC_OFFSET_COL = 10
TITLES = [
    "Name", "Alias", "Device", "Port", "Data Type", "Sensor Type", "Units",
    "PT Slope (psi/mv)", "PT Offset (mv)", "TC Type", "TC Offset (K)"
]
#  note that the above titles are used when extracting from an excel sheet and need to match the headers of the sheet
confirmed_index_channels = {}


"""
1. Read and process sheet name
Excel:
    A. Validate file path
    B. Extract using pd method
Google:
    A. Validate gspread client
    B. Extract sheet data
    C. 'Cache' data (1 api call)
2. Validate/create device time-index channel(s)
3. Validate/create device ambientize channel(s)
4. Validate/create device sub-channel(s)
    A. PT/TC channels
        - calibration info
        - channel info
        - change active range
    B. Valve channels
        - create/validate valve_time
        - create/validate 5 subchannels (_en, _cmd, _v, _i, _plugged)
5. Return

- store channels as dictionary objects with the name as the key
- when needed, check the key and update or create based on the values

The meaningful data behind a channel is represented internally by:
- key=name
- values=dict
    - "data_type": sy.DataType
    - "device": str
    - "index": str
    - "is_index: bool
    - * "pt_slope": str
    - * "pt_offset": str
    - * "tc_type": str
    - * "tc_offset": str
Note that the sensor type is already known from the dictionary it is stored under

sets calibration info by using client.
gse_pt_01_pt_slope, gse_pt_01_pt_offset, gse_tc_01_tc_type, gse_tc_01_tc_offset
"""


def main():
    start_time = time.time()
    n = len(sys.argv)
    if n != 2:
        print("Usage: file_processing.py sheet"
              "\nsheet must be a filepath to an excel sheet, url of a google sheet, or name of a google sheet.")
        return 1
    else:
        source = sys.argv[1]
    print("reading from " + source)
    process_source(source)
    print("time to execute: " + str(time.time() - start_time))


def process_source(source: str) -> None:
    data = abstract_data(source)
    for ch_dict in data["DEV"]:
        for ch in ch_dict:
            update_or_create_channel(ch, ch_dict.get(ch))
    for ch_dict in data["VLV"]:
        for ch in ch_dict:
            update_or_create_channel(ch, ch_dict.get(ch))
    for ch_dict in data["PT"]:
        for ch in ch_dict:
            update_or_create_channel(ch, ch_dict.get(ch))
    for ch_dict in data["TC"]:
        for ch in ch_dict:
            update_or_create_channel(ch, ch_dict.get(ch))


def abstract_data(source) -> {str: [{str: {str: str}}]}:
    if ".xlsx" in source:
        data = process_excel(source)
    elif "docs.google.com" in source:
        data = process_url(source)
    else:
        data = process_name(source)
    validate_sheet(data)
    result = {"DEV": default_device_channels(data[TITLES[DEVICE_COL]]), "VLV": [], "PT": [], "TC": []}
    for r in range(len(data[TITLES[NAME_COL]])):
        if data[TITLES[SENSOR_TYPE_COL]][r] == "VLV":
            for ch in valve_channel(data, r):
                result["VLV"].append(ch)
        elif data[TITLES[SENSOR_TYPE_COL]][r] == "PT":
            for ch in pt_channel(data, r):
                result["PT"].append(ch)
        elif data[TITLES[SENSOR_TYPE_COL]][r] == "TC":
            for ch in tc_channel(data, r):
                result["TC"].append(ch)
        else:
            print(f"Unconfirmed sensor type in column {SENSOR_TYPE_COL}")
            print(f"{data[TITLES[SENSOR_TYPE_COL]][r]}")
    return result


def default_device_channels(devices: [str]) -> [{str: {str: str}}]:
    partial_result = []
    for device in devices:
        # print(device)
        if (device + "_time") not in partial_result:
            partial_result.append({device + "_time": {"data_type": "timestamp",
                                                      "device": device, "is_index": True}})
            partial_result.append({device + "_ambientize": {"data_type": "INT64",
                                                            "device": device, "index": device + "_time"}})
    return partial_result


def valve_channel(data, r) -> [{str: {str: str}}]:
    # print()
    # print(data)
    # print()
    # print(data.__class__)
    # print()
    valve_name = data[TITLES[NAME_COL]][r]
    device = data[TITLES[DEVICE_COL]][r]
    partial_result = [
        {valve_name + "_time": {
            "data_type": "timestamp",
            "device": device,
            "is_index": True}},
        {valve_name + "_en": {
            "data_type": "uint8",
            "device": device,
            "index": device + "_time"}},
        {valve_name + "_cmd": {
            "data_type": "uint8",
            "device": device,
            "index": device + "_time"}},
        {valve_name + "_v": {
            "data_type": "float32",
            "device": device,
            "index": device + "_time"}},
        {valve_name + "_i": {
            "data_type": "float32",
            "device": device,
            "index": device + "_time"}},
        {valve_name + "_plugged": {
            "data_type": "uint32",
            "device": device,
            "index": device + "_time"}}
    ]
    return partial_result


def pt_channel(data, r) -> [{str: {str: str}}]:
    device = data[TITLES[DEVICE_COL]][r]
    return [{
        data[TITLES[NAME_COL]][r]: {
            "data_type": data[TITLES[DATA_TYPE_COL]][r],
            "device": device,
            "pt_slope": data[TITLES[PT_SLOPE_COL]][r],
            "pt_offset": data[TITLES[PT_OFFSET_COL]][r],
            "index": device + "_time"
        }}]


def tc_channel(data, r) -> {str: {str: str}}:
    device = data[TITLES[DEVICE_COL]][r]
    return [{
        data["Name"][r]: {
            "data_type": data[TITLES[DATA_TYPE_COL]][r],
            "device": device,
            "tc_type": data[TITLES[TC_TYPE_COL]][r],
            "tc_offset": data[TITLES[TC_OFFSET_COL]][r],
            "index": device + "_time"
        }}]


def update_or_create_channel(ch_name: str, ch_as_dict: {str: str}) -> None:
    print(f"checking channel {ch_name}")
    # print(ch_as_dict)
    if ch_as_dict.get("is_index"):
        if confirmed_index_channels.get(ch_name) is not None:
            print(f"index channel {ch_name} already updated")
            return
        if channel_exists(ch_name):
            index_key = update_channel(ch_name, ch_as_dict)
        else:
            index_key = create_channel(ch_name, ch_as_dict)
        confirmed_index_channels[ch_name] = index_key
    elif "_ambientize" in ch_name:
        if confirmed_index_channels.get(ch_name) is not None:
            print(f"ambientize channel {ch_name} already updated")
            return
        if channel_exists(ch_name):
            index_key = update_channel(ch_name, ch_as_dict)
        else:
            index_key = create_channel(ch_name, ch_as_dict)
        confirmed_index_channels[ch_name] = index_key
    else:
        try:
            client.channels.retrieve(ch_name)
            update_channel(ch_name, ch_as_dict)
        except sy.exceptions.QueryError:
            create_channel(ch_name, ch_as_dict)


def update_channel(ch_name: str, ch_as_dict: {str: str}) -> int:
    print(f"There is not yet functionality to update existing channels - {ch_name} not updated")
    if ch_as_dict.get("pt_slope"):
        print("there is not yet functionality to update calibration info, but if there was...")
        print(f"{ch_name}_pt_slope = " + str(ch_as_dict["pt_slope"]))
        print(f"{ch_name}_pt_offset = " + str(ch_as_dict["pt_offset"]))
        #  client.channels.kv.update(ch_name + "_pt_slope", ch_as_dict.get("pt_slope"))
        #  client.channels.kv.update(ch_name + "_pt_slope", ch_as_dict.get("pt_slope"))
    if ch_as_dict.get("tc_type"):
        print("there is not yet functionality to update calibration info, but if there was...")
        # client.channels.kv.update(ch_name + "_tc_type", ch_as_dict.get("tc_type"))
        # client.channels.kv.update(ch_name + "_tc_offset", ch_as_dict.get("tc_offset"))
        print(f"{ch_name}_tc_type = " + str(ch_as_dict["tc_type"]))
        print(f"{ch_name}_tc_offset = " + str(ch_as_dict["tc_offset"]))
    return 0


def create_channel(ch_name: str, ch_as_dict: {str: str}) -> int:
    print(f"creating channel {ch_name}")
    if ch_as_dict.get("pt_slope"):
        print("there is not yet functionality to update calibration info, but if there was...")
        print(f"{ch_name}_pt_slope = " + str(ch_as_dict["pt_slope"]))
        print(f"{ch_name}_pt_offset = " + str(ch_as_dict["pt_offset"]))
        #  client.channels.kv.update(ch_name + "_pt_slope", ch_as_dict.get("pt_slope"))
        #  client.channels.kv.update(ch_name + "_pt_slope", ch_as_dict.get("pt_slope"))
    if ch_as_dict.get("tc_type"):
        print("there is not yet functionality to update calibration info, but if there was...")
        # client.channels.kv.update(ch_name + "_tc_type", ch_as_dict.get("tc_type"))
        # client.channels.kv.update(ch_name + "_tc_offset", ch_as_dict.get("tc_offset"))
        print(f"{ch_name}_tc_type = " + str(ch_as_dict["tc_type"]))
        print(f"{ch_name}_tc_offset = " + str(ch_as_dict["tc_offset"]))
    if ch_as_dict.get("is_index"):
        return client.channels.create(data_type=DataType(ch_as_dict["data_type"]), name=ch_name,
                                      is_index=True).key
    else:
        return client.channels.create(data_type=DataType(ch_as_dict["data_type"]), name=ch_name,
                                      index=find_index(ch_as_dict["index"])).key


def channel_exists(ch_name: str) -> bool:
    try:
        client.channels.retrieve(ch_name)
        return True
    except sy.exceptions.QueryError:
        return False


def process_excel(source) -> {str: {str: {str: str}}}:
    try:
        workbook = pd.read_excel(source)
    except pd.errors.EmptyDataError:
        raise "failed while trying to extract excel sheet from " + source
    return workbook


def process_url(source) -> {str: {str: {str: str}}}:
    try:
        gspread_client = gspread.service_account("credentials.json")
    except FileNotFoundError:
        raise "to authenticate to the gcloud server, you must add a valid credentials.json file in this directory"
    sheet = gspread_client.open_by_url(source)
    if not sheet:
        raise "Unable to process url as google sheet"
    return extract_google_sheet(sheet)


def process_name(source) -> {str: {str: {str: str}}}:
    try:
        gspread_client = gspread.service_account("credentials.json")
    except FileNotFoundError:
        raise "to authenticate to the gcloud server, you must add a valid credentials.json file in this directory"
    sheet = gspread_client.open(source)
    if not sheet:
        raise "Unable to process name as google sheet"
    return extract_google_sheet(sheet)


def extract_google_sheet(sheet: Spreadsheet) -> {str: {str: {str: str}}}:
    vals = sheet.sheet1.get_all_values()
    return pd.DataFrame(vals[1:], columns=vals[0])


def find_index(ch_name: str) -> int:
    if confirmed_index_channels.get(ch_name):
        return confirmed_index_channels.get(ch_name)
    else:
        raise "attempting to access index channel before it has been verified"


def validate_sheet(df: pd.DataFrame) -> None:
    for r in range(len(df)):
        for c in range(7):
            if not df[TITLES[c]][r]:
                raise f"{df[TITLES[NAME_COL]][r]} column {c} cannot be empty"
        if df[TITLES[DATA_TYPE_COL]][r] not in ["timestamp", "uint8", "uint16", "uint32", "uint64",
                                        "int8", "int16", "int32", "int64", "float32", "float64"]:
            raise f"invalid data type for {df[TITLES[NAME_COL]][r]} in column {DATA_TYPE_COL}"
        if df[TITLES[SENSOR_TYPE_COL]][r] == "PT":
            if not (df[TITLES[SENSOR_TYPE_COL]][r] and df[TITLES[SENSOR_TYPE_COL]][r]):
                raise f"define calibration info for {df[TITLES[NAME_COL]][r]} in columns {TC_TYPE_COL} and {TC_OFFSET_COL}"
        elif df[TITLES[SENSOR_TYPE_COL]][r] == "TC":
            if not (df[TITLES[SENSOR_TYPE_COL]][r] and df[TITLES[SENSOR_TYPE_COL]][r]):
                raise f"define calibration info for {df[TITLES[NAME_COL]][r]} in columns {TC_TYPE_COL} and {TC_OFFSET_COL}"
        elif df[TITLES[SENSOR_TYPE_COL]][r] != "VLV":
            raise f"invalid sensor type for {df[TITLES[NAME_COL]][r]} in column {SENSOR_TYPE_COL} - must be VLV, PT, or TC"


if __name__ == "__main__":
    main()
