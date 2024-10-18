# import csv
# from datetime import datetime

# # Define the range: May 14, 2024 midnight to May 15, 2024 noon in nanoseconds
# start_time = int(datetime(2024, 5, 14, 0, 0).timestamp() * 1e9)
# end_time = int(datetime(2024, 5, 15, 12, 0).timestamp() * 1e9)

# def find_latest_timestamp(csv_file):
#     latest_timestamp = None
    
#     # Open the CSV file and iterate through timestamps
#     with open(csv_file, mode='r') as file:
#         reader = csv.reader(file)
#         for row in reader:
#             # Convert the timestamp to an integer
#             timestamp = int(row[0].strip())

#             # Check if the timestamp is within the specified range
#             if start_time <= timestamp <= end_time:
#                 # If this is the latest timestamp found so far, update the latest_timestamp
#                 if latest_timestamp is None or timestamp > latest_timestamp:
#                     latest_timestamp = timestamp
    
#     if latest_timestamp:
#         # Convert the latest timestamp to a human-readable format
#         latest_date = datetime.utcfromtimestamp(latest_timestamp / 1e9)
#         return latest_date
#     else:
#         return "No timestamp found in the specified range."

# # Example usage
# csv_file = 'data/65538.csv'  # Replace with the path to your CSV file
# latest_time = find_latest_timestamp(csv_file)
# print(f"The latest timestamp in the range is: {latest_time}")

# import csv

# def count_rows_in_csv(file_path):
#     """Counts the number of rows in a given CSV file."""
#     with open(file_path, mode='r') as file:
#         reader = csv.reader(file)
#         row_count = sum(1 for row in reader)
#     return row_count

# def compare_csv_row_counts(file1, file2):
#     """Compares the number of rows in two CSV files."""
#     count1 = count_rows_in_csv(file1)
#     count2 = count_rows_in_csv(file2)

#     if count1 == count2:
#         print(f"Both files contain the same number of samples: {count1} rows.")
#     else:
#         print(f"The files contain different numbers of samples.")
#         print(f"{file1} contains {count1} rows.")
#         print(f"{file2} contains {count2} rows.")

# # File paths
# file1 = 'data/65538.csv'
# file2 = 'data/65591.csv'

# # Compare the row counts
# compare_csv_row_counts(file1, file2)

import csv
import os
from collections import defaultdict

def count_rows_in_csv(file_path):
    """Counts the number of rows in a given CSV file."""
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        row_count = sum(1 for row in reader)
    return row_count

def group_files_by_row_count(file_list, base_directory):
    """Groups CSV files by their row counts."""
    row_count_groups = defaultdict(list)  # Dictionary to group files by row count
    
    for file_name in file_list:
        file_path = os.path.join(base_directory, file_name)
        row_count = count_rows_in_csv(file_path)
        row_count_groups[row_count].append(file_name)
    
    return row_count_groups

# List of file names
file_list = [
    '65538.csv', '65557.csv', '65574.csv', '65591.csv', '65608.csv',
    '65541.csv', '65558.csv', '65575.csv', '65592.csv', '65609.csv',
    '65542.csv', '65559.csv', '65576.csv', '65593.csv', '65610.csv',
    '65543.csv', '65560.csv', '65577.csv', '65594.csv', '65611.csv',
    '65544.csv', '65561.csv', '65578.csv', '65595.csv', '65612.csv',
    '65545.csv', '65562.csv', '65579.csv', '65596.csv', '65613.csv',
    '65546.csv', '65563.csv', '65580.csv', '65597.csv', '65614.csv',
    '65547.csv', '65564.csv', '65581.csv', '65598.csv', '65615.csv',
    '65548.csv', '65565.csv', '65582.csv', '65599.csv', '65616.csv',
    '65549.csv', '65566.csv', '65583.csv', '65600.csv', '65617.csv',
    '65550.csv', '65567.csv', '65584.csv', '65601.csv', '65618.csv',
    '65551.csv', '65568.csv', '65585.csv', '65602.csv', '65619.csv',
    '65552.csv', '65569.csv', '65586.csv', '65603.csv', '65620.csv',
    '65553.csv', '65570.csv', '65587.csv', '65604.csv', '65717.csv',
    '65554.csv', '65571.csv', '65588.csv', '65605.csv',
    '65555.csv', '65572.csv', '65589.csv', '65606.csv',
    '65556.csv', '65573.csv', '65590.csv', '65607.csv'
]

# Base directory containing the CSV files
base_directory = 'data'  # Replace with the actual directory path

# Group the files by the number of rows
grouped_files = group_files_by_row_count(file_list, base_directory)

# Print the grouped files
for row_count, files in grouped_files.items():
    print(f"{row_count} rows: {files}")
