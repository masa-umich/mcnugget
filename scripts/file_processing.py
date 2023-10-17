import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
import gspread
import argparse
import re
from gspread import Spreadsheet
from synnax import channel as ch
import numpy


def main():
    # excel = DataFrameCase("/Users/evanhekman/testing_spreadsheet.xlsx")
    # google_url = \
    #     DataFrameCase("https://docs.google.com/spreadsheets/d/12cWNMZwD24SpkkLSkM972Z8S_Jxt4Hxe3_n6hM9yvHQ/edit#gid=0")
    # google_name = DataFrameCase("testing_spreadsheet")

    excel_str = "/Users/evanhekman/instrumentation_example.xlsx"
    google_url_str = "https://docs.google.com/spreadsheets/d/1GpaiJmR4A7l6NXS_nretchqW1pBHg2clNO7uNfHxijk/edit#gid=0"
    google_name_str = "instrumentation_sheet_copy"
    channels = extract_channels(google_url_str)
    print(channels)


def extract_channels(sheet: str) -> [ch.Channel]:
    source = DataFrameCase(sheet)
    channels = []
    for r in [row for row in range(source.data.rows()) if row != 0]:  # first row will be column headers
        print(r)
        channels.append(ch.Channel(name=source.get(r, 0), is_index=True, data_type=source.get(r, 4)))
    return channels


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


def terminal_script():
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


if __name__ == "__main__":
    main()
