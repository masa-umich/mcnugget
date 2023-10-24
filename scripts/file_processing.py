import pandas as pd
import tkinter as tk
import re
from tkinter import filedialog
from tkinter import simpledialog
import synnax as sy
import gspread
from gspread import Spreadsheet
from synnax.telem import (
    CrudeDataType,
    CrudeRate,
    DataType,
    TimeStamp,
    TimeSpan,
    TimeRange,
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


"""
key-value pairs on the range
A range is a period of data (range of time)
ACTIVE RANGE is the current context that everything operates under
Range has KV dictionaries which contain metadata (col 5-9 of spreadsheet)
active_range() returns a class object of range which we can call set(key, value) or kv.set() on
set_alias(key, value) sets a human-readable name for each channel/range
see test_range for examples
kv.set_alias("PT_1_slope", 5) to set pt_slope to 5 on channel PT_1
"""

"""
- one active_range for ALL channels, indexed using name as a key in a dictionary-like structure
- alias is not a field on Channel but needs to be set, so I need to turn everything into a SugaredChannel
    - everything becomes a SugaredChannel but might have empty 'sugar'. Can iterate over all sugar kv pairs and set
- "pt_slope", "pt_offset", "tc_type", "tc_offset"
gse_pt_01_pt_slope, gse_pt_01_pt_offset, gse_tc_01_tc_type, gse_tc_01_tc_offset
"""

"""
TODO
- change sugar so channel.alias works on everything
- 
"""


def main():
    channels = extract_channels("/Users/evanhekman/instrumentation_sheet_copy.xlsx")
    print(channels)
    # parse cli


class SugaredChannel:
    """ A messy subclass of Channel that isn't actually a subclass.
    Has the same properties as Channel but actually represents an object with a Channel and Dictionary attached to it.
    SugaredChannel.channel is the standard channel.
    SugaredChannel.sugar is a dictionary representing the calibration info for a PT/TC channel
    SugaredChannel.alias is the alias for the channel
    """
    def __init__(self, *, name: str, data_type: CrudeDataType, rate: CrudeRate = 0, is_index: bool = False,
                 index: sy.channel.payload.ChannelKey = 0, sugar: {str: str}, alias: str) -> None:
        self.channel = sy.Channel(name=name, data_type=data_type, rate=rate, is_index=is_index, index=index)
        self.sugar = sugar
        self.alias = alias

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


def update_active_range(channels: [sy.Channel]) -> None:
    """ Updates active_range with info from the input channel
    Specifically, it updates the alias and calibration info
    """
    active_range = sy.get_active_range()  # waiting for a function definition

    for channel in channels:
        active_range.set_alias(channel.name, channel.alias)
        for key, value in channel.sugar:
            active_range.kv.set(key, value)


def extract_channels(sheet: str) -> [sy.Channel]:
    """ Extracts all channels from a sheet.
    For the sheet, pass in a google sheet url, the name of a google sheet shared with the service account,
    or a filepath to an excel file.
    Returns an array of Channel and SugaredChannel objects
    """
    source = DataFrameCase(sheet)
    channels = []
    for r in [row for row in range(source.rows()) if row != 0]:  # first row will be column headers
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
                                           sugar=sugar, index=tc_index.key, alias=source.get(r, ALIAS_COL)))
        elif source.get(r, SENSOR_TYPE_COL) == "PT":  # handles PT channel creation
            sugar = {"pt_slope": source.get(r, PT_SLOPE_COL), "pt_offset": source.get(r, PT_OFFSET_COL)}
            pt_index = sy.Channel(name=(source.get(r, NAME_COL) + "_time"), is_index=True, data_type=DataType.TIMESTAMP)
            if sugar["pt_slope"] is None or sugar["pt_offset"] is None:
                raise Exception("Undefined PT slope or PT offset in column "
                                + str(PT_SLOPE_COL) + " or " + str(PT_OFFSET_COL))
            channels.append(SugaredChannel(name=source.get(r, NAME_COL),
                                           is_index=False, data_type=DataType(source.get(r, DATA_TYPE_COL)),
                                           sugar=sugar, index=pt_index.key, alias=source.get(r, ALIAS_COL)))
        else:
            raise Exception("Undefined Sensor Type in column " + str(SENSOR_TYPE_COL))
            # if channel is not defined as "TC", "PT" or "VLV", an exception is raised
    return channels


def validate_sheet(source, row) -> None:
    """ Checks to make sure no important fields are empty in a given row for a sheet
    If you're having trouble querying the API too much you could try skipping validation as this
        function includes 7 extra API calls for every row
    """
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


def valve_channel(source, r) -> [SugaredChannel]:
    """ Helper function to define sub-channels associated with a VLV channel
    valve_en(uint8), valve_cmd(uint8), valve_v(float32), valve_i(float32), valve_plugged(uint32)
    """
    prefix = source.data.get(r, 0)
    index_ch = SugaredChannel(name=(prefix + "_time"), data_type=DataType.TIMESTAMP, is_index=True,
                              alias=source.get(r, ALIAS_COL), sugar={})
    channels = [
        index_ch,
        SugaredChannel(name=(prefix + "_en"), data_type=DataType.UINT8, is_index=False, index=index_ch.key,
                       alias=source.get(r, ALIAS_COL), sugar={}),
        SugaredChannel(name=(prefix + "_cmd"), data_type=DataType.UINT8, is_index=False, index=index_ch.key,
                       alias=source.get(r, ALIAS_COL), sugar={}),
        SugaredChannel(name=(prefix + "_v"), data_type=DataType.FLOAT32, is_index=False, index=index_ch.key,
                       alias=source.get(r, ALIAS_COL), sugar={}),
        SugaredChannel(name=(prefix + "_i"), data_type=DataType.FLOAT32, is_index=False, index=index_ch.key,
                       alias=source.get(r, ALIAS_COL), sugar={}),
        SugaredChannel(name=(prefix + "_plugged"), data_type=DataType.UINT32, is_index=False, index=index_ch.key,
                       alias=source.get(r, ALIAS_COL), sugar={})
    ]
    return channels


class DataFrameCase:
    """ A class that can be instantiated to represent a google or Excel sheet
    Almost everything is handled internally - just instantiate using a url, name, or filepath
        and query using the get(row, col) function. The set(row, col) can also be used and will automatically save
    """
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

    def rows(self) -> int:
        # returns the number of non-empty rows in the sheet
        return self.data.rows()


class ExcelDataFrameCase:
    """ A class that contains methods to extract data from an Excel sheet
    Instantiated using the filepath to the desired sheet
    Some weird fencepost error handling because Excel has a header row and pandas.DataFrame does not
    However, pandas.DataFrames are much easier to work with and provide easy extraction
    """
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
            self.df.loc[row, self.headers.get(col)] = val
            self.save()

    def save(self):
        self.df.to_excel(self.filepath)

    def rows(self) -> int:
        print(self.df["Name"])
        return len(self.df["Name"]) + 1
        # returns the number of names in the name column + 1 because Excel has headers but pandas does not


class GoogleDataFrameCase:
    """ A class that contains methods to extract data from a google sheet
    Can be instantiated using the url of a google sheet
    Can also be instantiated using the name of a google sheet shared with the service account
    Note that the API has a cap and cannot be queried infinitely for free
    """
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


def authentication_path():
    try:
        with open("credentials.json", "r") as creds:
            return creds.name
    except FileNotFoundError:
        raise Exception("Create a 'credentials.json' file in this directory to authenticate to the gcloud server")


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


def open_excel(file_path) -> pd.DataFrame:
    workbook = pd.read_excel(file_path)
    if workbook is not None:
        return workbook
    else:
        raise Exception("Unable to process Excel file")


if __name__ == "__main__":
    main()
