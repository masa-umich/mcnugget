import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
import gspread
import argparse

# OVERVIEW
# define a function that returns a read(sheet/filepath, column) object
#   that can read column data from a google sheet or an excel file
# make a protocol class
'''
method signatures
read
get
row, col (returns value)

Name - permanent name for the channel, never changes. 
    .channels.create(name) - pass in name
    if name already exists, leave it (internally handled)
    retrieve_if_name_exists = true
Alias - 
    temporary name (depending on port/channel)
Device - *subject to change
    enum of what computer is connected to the channel
Port - *subject to change
    port of the connected cpu
Data Type - 
    smallest possible data type (usually a float32 except for gps float64, bool = uint8, )
client.set(key, value)
    key = name_device
Sensor Type - 
    TC? Pressure Transducer? Etc. Relevant for DAC side, understanding calibration values
    Valve is not a sensor - instead, create 3 channels for valve. Call create() 3-5 times. Use name as a prefix
    en (uint8) open/closed
    cmd (push/write channel to open/close)
    v (voltage) float32
    _i (current)
    plugged (uint32) plugged in or not
    cmd_time (time we sent the command) indexed channel
        field on create method - is_index field on create method should be set to true
        use the key from the channel to link the indexed channel
Units - 
    units is the data type (pass as value to create())
PT Slope - 
    only applies to PT sensors
PT Offset - 
    only applies to PT sensors
TC Type - 
    thermocouples, use lookup table (embedded in DAC firmware) 
TC Offset - 
    thermocouples, use lookup table (embedded in DAC firmware) 

GSE_time(is_index = true)
when we create a GSE channel that is time-indexed, link the GSE_time TIME-INDEXED channel to index the time
time-indexed channels are really just a pair of channels to store time data

sunday:
we will get
    set()
    create()
we should provide
    get(row->int, column->int) ->string or ->num or ->whatever
'''


class Table:
    def __init__(self, dataframe: pd.DataFrame):
        self.df_ = dataframe

    @property
    def df(self) -> pd.DataFrame:
        return self.df_

    def get(self, row, col):
        return self.df.columns[col][row]


def handle_excel(file_path, columns):
    if file_path is None:
        file_path = filedialog.askopenfilename(filetypes=[("excel file", "*.xlsx")])
        if not file_path:
            raise Exception("Invalid file path")
    columns = prompt_columns(columns)
    print(open_excel(file_path, columns))


def handle_google_link(url, columns):
    if url is None:
        url = tk.simpledialog.askstring("Input", "Link to google sheet (must be accessible)")
    columns = prompt_columns(columns)
    print(open_google_link(url, columns))


def handle_google_name(name, columns):
    if name is None:
        name = tk.simpledialog.askstring("Input", "Title of google sheet (must be accessible)")
    columns = prompt_columns(columns)
    print(open_google_name(name, columns))


def prompt_columns(existing_columns):
    if existing_columns is None:
        root = tk.Tk()
        dialog = tk.Toplevel()
        columns = []
        while True:
            column_name = tk.simpledialog.askstring("Input", "Input columns to extract - select cancel to finish")
            if column_name is None:
                break
            if column_name != "" and not (column_name in columns):
                columns.append(column_name)
        dialog.destroy()
        root.destroy()
        return columns
    else:
        return existing_columns


# inputs the name of the google sheet and returns a workbook containing the extracted data
def open_google_name(name, columns):
    file_path = authentication_path()
    gspread_client = gspread.service_account(
        filename=file_path)
    spreadsheets = {sheet.title: sheet for sheet in gspread_client.openall()}
    google_sheet = spreadsheets.get(name, None)
    if google_sheet is None:
        raise Exception(f"Google Sheet '{name}' not found")
        # retry opening the google sheet
    else:
        # extract column data
        sheet = google_sheet.sheet1
        headers = [header for header in sheet.row_values(1)]
        missing_columns = [col for col in columns if headers.count(col) == 0]
        columns = [col for col in columns if headers.count(col) != 0]
        for col in missing_columns:
            print(f"column {col} not found")
        column_values = {col: sheet.col_values(headers.index(col) + 1) for col in columns}
        new_workbook = pd.DataFrame(column_values)
        if new_workbook is not None:
            return new_workbook
        else:
            raise Exception("Unable to process Google sheet")


# inputs the link to the google sheet and returns a workbook containing the extracted data
def open_google_link(link, columns):
    file_path = authentication_path()
    gspread_client = gspread.service_account(
        filename=file_path)
    sheet = gspread_client.open_by_url(link).sheet1
    # extract column data
    headers = [header for header in sheet.row_values(1)]
    missing_columns = [col for col in columns if headers.count(col) == 0]
    columns = [col for col in columns if headers.count(col) != 0]
    for col in missing_columns:
        print(f"column {col} not found")
    column_values = {col: sheet.col_values(headers.index(col) + 1) for col in columns}
    new_workbook = pd.DataFrame(column_values)
    if new_workbook is not None:
        return new_workbook
    else:
        raise Exception("Unable to process Google link/file")


def open_excel(file_path, columns):
    workbook = pd.read_excel(file_path)
    if columns is None:
        columns = prompt_columns(columns)
    new_workbook = pd.DataFrame({col: workbook.get(col) for col in columns})
    if new_workbook is not None:
        return new_workbook
    else:
        raise Exception("Unable to process Excel file")


def main():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="file extraction script")

    # Add optional arguments
    parser.add_argument("--excel_filepath", type=str, default=None, help="filepath to an excel sheet")
    parser.add_argument("--google_link", type=str, default=None, help="link to a google sheet (requires access)")
    parser.add_argument("--google_name", type=str, default=None, help="title of a google sheet (requires access)")
    parser.add_argument("--columns", nargs='+', type=str, default=None, help="which columns to extract from the sheet")
    args = parser.parse_args()

    # Access the argument values
    excel_filepath = args.excel_filepath
    google_link = args.google_link
    google_name = args.google_name
    columns = args.columns

    # Print the argument values
    print("processing these arguments:")
    print("excel_filepath:", excel_filepath)
    print("google_link:", google_link)
    print("google_name:", google_name)
    print("columns:", columns)

    if excel_filepath:
        handle_excel(file_path=excel_filepath, columns=columns)
    elif google_link:
        handle_google_link(url=google_link, columns=columns)
    elif google_name:
        handle_google_name(name=google_name, columns=columns)
    else:
        print("no arguments detected")
        root = tk.Tk()
        root.title("Input Type")
        root.geometry("600x200+435+378")
        button_excel = \
            tk.Button(root, text="Excel file",
                      command=lambda: (root.destroy(), handle_excel(file_path=None, columns=None)))
        button_excel['foreground'] = 'green'
        button_google_link = \
            tk.Button(root, text="Google Sheet link",
                      command=lambda: (root.destroy(), handle_google_link(url=None, columns=None)))
        button_google_link['foreground'] = 'blue'
        button_google_name = \
            tk.Button(root, text="Google Sheet by name",
                      command=lambda: (root.destroy(), handle_google_name(name=None, columns=None)))
        button_google_name['foreground'] = 'blue'
        button_excel.pack()
        button_google_link.pack()
        button_google_name.pack()
        root.mainloop()


def authentication_path():
    try:
        with open("credentials.json", "r") as creds:
            return creds.name
    except FileNotFoundError:
        raise Exception("Create a 'credentials.json' file in this directory to authenticate to the gcloud server")


if __name__ == "__main__":
    main()
