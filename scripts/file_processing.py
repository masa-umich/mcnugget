import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
import gspread
import argparse


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
    gspread_client = gspread.service_account(
        filename="/Users/evanhekman/coding_projects/masa-sheet-reading-v1-authenticationkey.json")
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
    gspread_client = gspread.service_account(
        filename="/Users/evanhekman/coding_projects/masa-sheet-reading-v1-authenticationkey.json")
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
        # input_type_label = tk.Label(root, text="Select how you would like to input the file")
        root.mainloop()


if __name__ == "__main__":
    main()
