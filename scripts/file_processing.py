import pandas as pd
import tkinter as tk
import re
import argparse
from tkinter import filedialog
from tkinter import simpledialog
import synnax as sy
import gspread
from gspread import Spreadsheet
from synnax.telem import (
    Rate,
    CrudeDataType,
    CrudeRate,
    DataType,
    TimeRange,
    Series,
    CrudeTimeStamp,
)

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


def main():
    # excel = DataFrameCase("/Users/evanhekman/testing_spreadsheet.xlsx")
    # google_url = \
    #     DataFrameCase("https://docs.google.com/spreadsheets/d/12cWNMZwD24SpkkLSkM972Z8S_Jxt4Hxe3_n6hM9yvHQ/edit#gid=0")
    # google_name = DataFrameCase("testing_spreadsheet")

    excel_str = "/Users/evanhekman/instrumentation_sheet_copy.xlsx"
    google_url_str = "https://docs.google.com/spreadsheets/d/1GpaiJmR4A7l6NXS_nretchqW1pBHg2clNO7uNfHxijk/edit#gid=0"
    google_name_str = "instrumentation_sheet_copy"
    channels = extract_channels(excel_str)
    for channel in channels:
        print(str(channel.name) + " " + str(channel.data_type) + " " + str(channel.is_index))


def extract_channels(sheet: str) -> [sy.Channel]:
    source = DataFrameCase(sheet)
    channels = []
    for r in [row for row in range(source.data.rows()) if row != 0]:  # first row will be column headers
        print(r)
        validate_sheet(source, r)
        if source.get(r, SENSOR_TYPE_COL) == "VLV":  # handles valve channel creation
            valve_subchannels = valve_channel(source, r)
            for channel in valve_subchannels:
                channels.append(channel)
        elif source.get(r, SENSOR_TYPE_COL) == "TC":  # handles TC channel creation
            sugar = {"tc_type": source.get(r, TC_TYPE_COL), "tc_offset": source.get(r, TC_OFFSET_COL)}
            tc_index = sy.Channel(name=(source.get(r, NAME_COL) + "_time"), is_index=True, data_type=DataType.TIMESTAMP)
            if sugar["tc_offset"] is None or sugar["tc_type"] is None:
                raise Exception("Undefined TC type or TC offset in column "
                                + str(TC_TYPE_COL) + " or " + str(TC_OFFSET_COL))
            channels.append(SugaredChannel(name=source.get(r, NAME_COL),
                                           is_index=False, data_type=DataType(source.get(r, DATA_TYPE_COL)),
                                           sugar=sugar, index=tc_index.key))
        elif source.get(r, SENSOR_TYPE_COL) == "PT":  # handles PT channel creation
            sugar = {"pt_slope": source.get(r, PT_SLOPE_COL), "pt_offset": source.get(r, PT_OFFSET_COL)}
            pt_index = sy.Channel(name=(source.get(r, NAME_COL) + "_time"), is_index=True, data_type=DataType.TIMESTAMP)
            if sugar["pt_slope"] is None or sugar["pt_offset"] is None:
                raise Exception("Undefined PT slope or PT offset in column "
                                + str(PT_SLOPE_COL) + " or " + str(PT_OFFSET_COL))
            channels.append(SugaredChannel(name=source.get(r, NAME_COL),
                                           is_index=False, data_type=DataType(source.get(r, DATA_TYPE_COL)),
                                           sugar=sugar, index=pt_index.key))
        else:
            raise Exception("Undefined Sensor Type in column " + str(SENSOR_TYPE_COL))
            # if channel is not defined as "TC", "PT" or "VLV", an exception is raised
    return channels


def validate_sheet(source, row) -> None:
    if source.get(row, NAME_COL) is None:
        raise Exception("Name cannot be empty - row " + str(row) + " col " + str(NAME_COL))

    if source.get(row, ALIAS_COL) is None:
        raise Exception("Alias cannot be empty - row " + str(row) + " col " + str(ALIAS_COL))

    if source.get(row, DEVICE_COL) is None:
        raise Exception("Device cannot be empty - row " + str(row) + " col " + str(DEVICE_COL))

    if source.get(row, PORT_COL) is None:
        raise Exception("Port cannot be empty - row " + str(row) + " col " + str(PORT_COL))

    if source.get(row, DATA_TYPE_COL) is None:
        raise Exception("Data Type cannot be empty - row " + str(row) + " col " + str(DATA_TYPE_COL))

    if source.get(row, SENSOR_TYPE_COL) is None:
        raise Exception("Sensor Type cannot be empty - row " + str(row) + " col " + str(SENSOR_TYPE_COL))

    if source.get(row, UNITS_COL) is None:
        raise Exception("Units cannot be empty - row " + str(row) + " col " + str(UNITS_COL))


def valve_channel(source, row) -> [sy.Channel]:
    prefix = source.data.get(row, 0)
    index_ch = sy.Channel(name=(prefix + "_time"), data_type=DataType.TIMESTAMP, is_index=True)
    channels = [
        index_ch,
        sy.Channel(name=(prefix + "_en"), data_type=DataType.UINT8, is_index=False, index=index_ch.key),
        sy.Channel(name=(prefix + "_cmd"), data_type=DataType.UINT8, is_index=False, index=index_ch.key),
        sy.Channel(name=(prefix + "_v"), data_type=DataType.FLOAT32, is_index=False, index=index_ch.key),
        sy.Channel(name=(prefix + "_i"), data_type=DataType.FLOAT32, is_index=False, index=index_ch.key),
        sy.Channel(name=(prefix + "_plugged"), data_type=DataType.UINT32, is_index=False, index=index_ch.key)
    ]
    return channels


class SugaredChannel:
    def __init__(self, *, name: str, data_type: CrudeDataType, rate: CrudeRate = 0,
                 is_index: bool = False, index: sy.channel.payload.ChannelKey = 0, sugar: {str: str}) -> None:
        self.channel = sy.Channel(name=name, data_type=data_type, rate=rate, is_index=is_index, index=index)
        self.sugar = sugar

    # name, data_type, rate, is_index, index
    @property
    def name(self) -> str:
        return self.channel.name

    @property
    def data_type(self) -> str:
        return self.channel.data_type

    @property
    def rate(self) -> CrudeRate:
        return self.channel.rate

    @property
    def is_index(self) -> bool:
        return self.channel.is_index

    @property
    def index(self) -> sy.channel.payload.ChannelKey:
        return self.channel.index

    @property
    def leaseholder(self) -> int:
        return self.channel.leaseholder

    @property
    def key(self) -> sy.channel.payload.ChannelKey:
        return self.channel.key


class DataFrameCase:
    def __init__(self, unknown_input=None, excel_filepath=None, google_sheet_url=None, google_sheet_name=None):
        if excel_filepath:
            self.data = ExcelDataFrameCase(unknown_input)
        elif google_sheet_url or google_sheet_name:
            self.data = GoogleDataFrameCase(unknown_input)
        elif re.search(r'\.xlsx', unknown_input):
            self.data = ExcelDataFrameCase(unknown_input)
        else:
            self.data = GoogleDataFrameCase(unknown_input)

    def get(self, row, col):
        return self.data.get(row, col)

    def set(self, row, col, val):
        return self.data.set(row, col, val)

    def save(self):
        self.data.save()


class ExcelDataFrameCase:
    def __init__(self, filepath):
        self.df = handle_excel(filepath)
        self.headers = {i: self.df.columns[i] for i in range(self.df.columns.size)}
        self.filepath = filepath

    def get(self, row, col):
        if row == 0:
            return self.df.columns[0]
        return self.df.get(self.headers.get(col))[row - 1]

    def set(self, row, col, val):
        if row == 0:
            raise Exception("Pandas does not support renaming headers - please edit the excel file directly.")
        else:
            self.df.loc[row - 1, self.headers.get(col)] = val

    def save(self):
        self.df.to_excel(self.filepath)

    def rows(self) -> int:
        return len(self.df.columns[0])


class GoogleDataFrameCase:
    def __init__(self, url_or_name):
        self.gspread_client = gspread.service_account("credentials.json")
        if re.search(r'docs\.google\.com', url_or_name):
            self.sheet = handle_google_link(url_or_name, self.gspread_client)
        else:
            self.sheet = handle_google_name(url_or_name, self.gspread_client)

    def get(self, row, col):
        return self.sheet.sheet1.cell(row + 1, col + 1).value

    def set(self, row, col, val):
        self.sheet.sheet1.update_cell(row + 1, col + 1, val)

    def save(self):
        print("Why are you saving? Google sheets save automatically")

    def rows(self) -> int:
        return len(self.sheet.sheet1.col_values(1))


def handle_excel(file_path) -> pd.DataFrame:
    if file_path is None:
        file_path = filedialog.askopenfilename(filetypes=[("excel file", "*.xlsx")])
        if not file_path:
            raise Exception("Invalid file path")
    return open_excel(file_path)


def handle_google_link(url, gspread_client) -> Spreadsheet:
    if url is None:
        url = tk.simpledialog.askstring("Input", "Link to google sheet (must be accessible)")
    return open_google_link(url, gspread_client)


def handle_google_name(name, gspread_client) -> Spreadsheet:
    if name is None:
        name = tk.simpledialog.askstring("Input", "Title of google sheet (must be accessible)")
    return open_google_name(name, gspread_client)


# inputs the name of the google sheet and returns a workbook containing the extracted data
def open_google_name(name, gspread_client) -> Spreadsheet:
    s = gspread_client.open(name)
    if s is not None:
        return s
    else:
        raise Exception("Unable to process google link")


# inputs the link to the google sheet and returns a workbook containing the extracted data
def open_google_link(link, gspread_client) -> Spreadsheet:
    s = gspread_client.open_by_url(link)
    if s is not None:
        return s
    else:
        raise Exception("Unable to process google link")


def authentication_path():
    try:
        with open("credentials.json", "r") as creds:
            return creds.name
    except FileNotFoundError:
        raise Exception("Create a 'credentials.json' file in this directory to authenticate to the gcloud server")


def open_excel(file_path) -> pd.DataFrame:
    workbook = pd.read_excel(file_path)
    if workbook is not None:
        return workbook
    else:
        raise Exception("Unable to process Excel file")


# def terminal_script():
#     # Create an ArgumentParser object
#     parser = argparse.ArgumentParser(description="file extraction script")
#
#     # Add optional arguments
#     parser.add_argument("--excel_filepath", type=str, default=None, help="filepath to an excel sheet")
#     parser.add_argument("--google_link", type=str, default=None, help="link to a google sheet (requires access)")
#     parser.add_argument("--google_name", type=str, default=None, help="title of a google sheet (requires access)")
#     parser.add_argument("--columns", nargs='+', type=str, default=None, help="which columns to extract from the sheet")
#     args = parser.parse_args()
#
#     # Access the argument values
#     excel_filepath = args.excel_filepath
#     google_link = args.google_link
#     google_name = args.google_name
#     columns = args.columns
#
#     # Print the argument values
#     print("processing these arguments:")
#     print("excel_filepath:", excel_filepath)
#     print("google_link:", google_link)
#     print("google_name:", google_name)
#     print("columns:", columns)
#
#     if excel_filepath:
#         handle_excel(file_path=excel_filepath, columns=columns)
#     elif google_link:
#         handle_google_link(url=google_link, columns=columns)
#     elif google_name:
#         handle_google_name(name=google_name, columns=columns)
#     else:
#         print("no arguments detected")
#         root = tk.Tk()
#         root.title("Input Type")
#         root.geometry("600x200+435+378")
#         button_excel = \
#             tk.Button(root, text="Excel file",
#                       command=lambda: (root.destroy(), handle_excel(file_path=None, columns=None)))
#         button_excel['foreground'] = 'green'
#         button_google_link = \
#             tk.Button(root, text="Google Sheet link",
#                       command=lambda: (root.destroy(), handle_google_link(url=None, columns=None)))
#         button_google_link['foreground'] = 'blue'
#         button_google_name = \
#             tk.Button(root, text="Google Sheet by name",
#                       command=lambda: (root.destroy(), handle_google_name(name=None, columns=None)))
#         button_google_name['foreground'] = 'blue'
#         button_excel.pack()
#         button_google_link.pack()
#         button_google_name.pack()
#         root.mainloop()


if __name__ == "__main__":
    main()
