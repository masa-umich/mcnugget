import os
import json

def mark_data(key_mappings_file, data_dir):
    # Load the key_mappings.json file
    with open(key_mappings_file, 'r') as f:
        key_mappings = json.load(f)

    # Iterate over all CSV files in the data_dir
    for file_name in os.listdir(data_dir):
        if file_name.endswith(".csv"):
            key = file_name.replace(".csv", "")
            if key in key_mappings:
                new_file_name = f"{key_mappings[key]}.csv"
                os.rename(os.path.join(data_dir, file_name), os.path.join(data_dir, new_file_name))
                print(f"Renamed {file_name} to {new_file_name}")

if __name__ == "__main__":
    mark_data('key_mappings.json', 'xxx')
