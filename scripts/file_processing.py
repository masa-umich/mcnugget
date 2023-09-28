import pandas as pd
import numpy as np
import tkinter as tk
import openpyxl
from tkinter import filedialog
import gspread
import re
import argparse


def main():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="file extraction script")

    # Add optional arguments
    parser.add_argument("--google_link", type=str, default=None, help="link to a google sheet (requires access)")
    parser.add_argument("--excel_filepath", type=str, default=None, help="filepath to an excel sheet")
    parser.add_argument("--google_name", type=str, default=None, help="title of a google sheet (requires access)")
    parser.add_argument("--columns", nargs='+', type=str, default=None, help="which columns to extract from the sheet")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the argument values
    google_link = args.google_link
    excel_filepath = args.excel_filepath
    google_name = args.google_name
    columns = args.columns

    # Print the argument values
    print("processing these arguments:")
    print("google_link:", google_link)
    print("excel_filepath:", excel_filepath)
    print("google_name:", google_name)
    print("columns:", columns)

    



def prompt_columns():
    columns = []
    while True:
        column_name = tk.simpledialog.askstring("Input", "Input columns to extract - select cancel to finish")
        if column_name is None:
            break
        if column_name != "" and not (column_name in columns):
            columns.append(column_name)
    return columns


def open_google():
    gspread_client = gspread.service_account(
        filename="/Users/evanhekman/coding_projects/masa-sheet-reading-v1-authenticationkey.json")
    # title = tk.simpledialog.askstring("Input", "Name of sheet (or link to sheet)")
    title = "testing_spreadsheet"  # testing
    sheet = None
    if re.match("^https://docs.google.com", title):
        sheet = gspread_client.open_by_url(title).sheet1
    else:
        spreadsheets = {sheet.title: sheet for sheet in gspread_client.openall()}
        sheet = spreadsheets[title].sheet1
    # column_names = prompt_columns()
    column_names = ["Albatross", "Capybara"]  # testing
    headers = [header for header in sheet.row_values(1)]
    columns = {}
    for name in column_names:
        try:
            columns[name] = sheet.col_values(headers.index(name) + 1)
        except ValueError as e:
            print(f'Column {name} not found.')
    # columns = {col: [header for header in sheet.row_values(0)].index(col) for col in column_names}
    new_workbook = pd.DataFrame(columns)
    print(new_workbook)


def open_excel():
    file_path = filedialog.askopenfilename(filetypes=[("excel file", "*.xlsx")])
    if not file_path:
        raise Exception("Invalid file name")
    workbook = pd.read_excel(file_path)
    columns = prompt_columns()
    try:
        new_workbook = pd.DataFrame({col: workbook[col] for col in columns})
    except Exception as e:
        print(f'Column {col} not found')
    raise Exception("Column not found")
    print(new_workbook)


# open_excel()
open_google()
