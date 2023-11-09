import pandas as pd
import gspread
from gspread import Spreadsheet
import sys
import time
from synnax import Synnax

client = Synnax()
active_range = client.ranges.active() # still not sure how to access this?

ALIAS_COL = 0
DEVICE_COL = 1
PORT_COL = 2
SENSOR_TYPE_COL = 3
UNITS_COL = 4
PT_SLOPE_COL = 5
PT_OFFSET_COL = 6
TC_TYPE_COL = 7
TC_OFFSET_COL = 8
TITLES = [
    "Alias",
    "Device",
    "Port",
    "Sensor Type",
    "Units",
    "PT Slope (psi/mv)",
    "PT Offset (mv)",
    "TC Type",
    "TC Offset (K)",
]
#  note that the above titles are used when extracting from an excel sheet and need to match the headers of the sheet

"""
# PURPOSE OF THIS SCRIPT
- verify no duplicates on port number
- verify valid sensor types
- verify calibration info
- verify port numbers:
    port # 1-32 for gse_vlv
    port # 1-80 for gse_pt gse_tc
set key-value pairs on the range (PT/TC calibration info)
set alias for each channel

* testing without active_range is kind of hard
* what should i do if a channel is not found? just error not found?
* what should be updated for valve channels?
update with alias as prefix

"""


def main():
    start_time = time.time()
    n = len(sys.argv)
    if n != 2:
        print(
            "Usage: file_processing.py sheet"
            "\nsheet must be a filepath to an excel sheet, url of a google sheet, or name of a google sheet."
        )
        return 1
    else:
        source = sys.argv[1]
    print("reading from " + source)
    process_source(source)
    print("time to execute: " + str(time.time() - start_time))


def process_source(source) -> None:
    if ".xlsx" in source:
        data = process_excel(source)
    elif "docs.google.com" in source:
        data = process_url(source)
    else:
        data = process_name(source)
    validate_sheet(data)
    update_active_range(data)


def process_excel(source) -> pd.DataFrame:
    try:
        workbook = pd.read_excel(source)
    except pd.errors.EmptyDataError:
        raise "failed while trying to extract excel sheet from " + source
    return workbook


def process_url(source) -> pd.DataFrame:
    try:
        gspread_client = gspread.service_account("credentials.json")
    except FileNotFoundError:
        raise "to authenticate to the gcloud server, you must add a valid credentials.json file in this directory"
    sheet = gspread_client.open_by_url(source)
    if not sheet:
        raise "Unable to process url as google sheet"
    return extract_google_sheet(sheet)


def process_name(source) -> pd.DataFrame:
    try:
        gspread_client = gspread.service_account("credentials.json")
    except FileNotFoundError:
        raise "to authenticate to the gcloud server, you must add a valid credentials.json file in this directory"
    sheet = gspread_client.open(source)
    if not sheet:
        raise "Unable to process name as google sheet"
    return extract_google_sheet(sheet)


def validate_sheet(df: pd.DataFrame) -> None:
    ai = {}
    vlv = {}
    for r in range(len(df)):
        for c in range(5):
            if not df[TITLES[c]][r]:
                raise f"{df[TITLES[ALIAS_COL]][r]} column {c} cannot be empty"
        if df[TITLES[SENSOR_TYPE_COL]][r] == "PT":
            if ai.get(df[TITLES[PORT_COL]][r]):
                raise f"duplicate port number in row {r} column {PORT_COL}"
            ai[df[TITLES[PORT_COL]][r]] = True
            if not (df[TITLES[SENSOR_TYPE_COL]][r] and df[TITLES[SENSOR_TYPE_COL]][r]):
                raise f"define calibration info for {df[TITLES[ALIAS_COL]][r]} " \
                      f"in columns {TC_TYPE_COL} and {TC_OFFSET_COL}"
            if int(df[TITLES[PORT_COL]][r]) < 1 or int(df[TITLES[PORT_COL]][r]) > 80:
                raise f"port number for {df[TITLES[ALIAS_COL]][r]} is not within the valid range"
        elif df[TITLES[SENSOR_TYPE_COL]][r] == "TC":
            if ai.get(df[TITLES[PORT_COL]][r]):
                raise f"duplicate port number in row {r} column {PORT_COL}"
            ai[df[TITLES[PORT_COL]][r]] = True
            if not (df[TITLES[SENSOR_TYPE_COL]][r] and df[TITLES[SENSOR_TYPE_COL]][r]):
                raise f"define calibration info for {df[TITLES[ALIAS_COL]][r]} " \
                      f"in columns {TC_TYPE_COL} and {TC_OFFSET_COL}"
            if int(df[TITLES[PORT_COL]][r]) < 1 or int(df[TITLES[PORT_COL]][r]) > 80:
                raise f"port number for {df[TITLES[ALIAS_COL]][r]} is not within the valid range"
        elif df[TITLES[SENSOR_TYPE_COL]][r] == "VLV":
            if vlv.get(df[TITLES[PORT_COL]][r]):
                raise f"duplicate port number in row {r} column {PORT_COL}"
            vlv[df[TITLES[PORT_COL]][r]] = True
            if int(df[TITLES[PORT_COL]][r]) < 1 or int(df[TITLES[PORT_COL]][r]) > 32:
                raise f"port number for {df[TITLES[ALIAS_COL]][r]} is not within the valid range"
        else:
            raise f"invalid sensor type for {df[TITLES[ALIAS_COL]][r]} " \
                  f"in column {SENSOR_TYPE_COL} - must be VLV, PT, or TC"


def update_active_range(data: pd.DataFrame) -> None:
    for r in range(len(data[TITLES[ALIAS_COL]])):
        if data[TITLES[SENSOR_TYPE_COL]][r] == "VLV":
            process_valve(data, r)
        elif data[TITLES[SENSOR_TYPE_COL]][r] == "PT":
            process_pt(data, r)
        elif data[TITLES[SENSOR_TYPE_COL]][r] == "TC":
            process_tc(data, r)


def process_valve(data: pd.DataFrame, r: int) -> None:
    name = data[TITLES[DEVICE_COL]][r] + "_vlv_"
    if int(data[TITLES[PORT_COL]][r]) < 10:
        name += "0"
    name += data[TITLES[PORT_COL]][r]
    alias = data[TITLES[ALIAS_COL]][r]
    client.channels.retrieve(name).set_alias(
        {
            name + "_i": alias + " Current",
            name + "_en": alias + " English",
            name + "_v": alias + " Voltage",
            name + "_plugged": alias + " Plugged",
            name + "cmd": alias + " Command",
        }
    )
    print("updated" + name)


def process_pt(data: pd.DataFrame, r: int) -> None:
    name = data[TITLES[DEVICE_COL]][r] + "_vlv_"
    if int(data[TITLES[PORT_COL]][r]) < 10:
        name += "0"
    name += data[TITLES[PORT_COL]][r]
    client.channels.retrieve(name).set_alias(data[TITLES[ALIAS_COL]][r])
    active_range.meta_data.set(
        {
            name + "_pt_slope": data[TITLES[PT_SLOPE_COL]][r],
            name + "_pt_offset": data[TITLES[PT_OFFSET_COL]][r],
        }
    )
    print("updated " + name)


def process_tc(data: pd.DataFrame, r: int) -> None:
    name = data[TITLES[DEVICE_COL]] + "_vlv_"
    if int(data[TITLES[PORT_COL]][r]) < 10:
        name += "0"
    name += data[TITLES[PORT_COL]][r]
    client.channels.retrieve(name).set_alias(data[TITLES[ALIAS_COL]][r])
    active_range.meta_data.set(
        {
            name + "_tc_type": data[TITLES[TC_TYPE_COL]][r],
            name + "_tc_offset": data[TITLES[TC_OFFSET_COL]][r],
        }
    )
    print("updated " + name)


def extract_google_sheet(sheet: Spreadsheet) -> pd.DataFrame:
    vals = sheet.sheet1.get_all_values()
    return pd.DataFrame(vals[1:], columns=vals[0])


if __name__ == "__main__":
    main()
