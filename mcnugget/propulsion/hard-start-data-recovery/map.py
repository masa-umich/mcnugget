import os
import json

# JSON mapping (you can also load this from a file if needed)
channel_mapping = {
    "65542": "gse_ai_1",
    "65543": "gse_ai_2",
    "65544": "gse_ai_3",
    "65545": "gse_ai_4",
    "65546": "gse_ai_5",
    "65547": "gse_ai_6",
    "65548": "gse_ai_7",
    "65549": "gse_ai_8",
    "65550": "gse_ai_9",
    "65551": "gse_ai_10",
    "65552": "gse_ai_11",
    "65553": "gse_ai_12",
    "65554": "gse_ai_13",
    "65555": "gse_ai_14",
    "65556": "gse_ai_15",
    "65557": "gse_ai_16",
    "65558": "gse_ai_17",
    "65559": "gse_ai_18",
    "65560": "gse_ai_19",
    "65561": "gse_ai_20",
    "65562": "gse_ai_21",
    "65563": "gse_ai_22",
    "65564": "gse_ai_23",
    "65565": "gse_ai_24",
    "65566": "gse_ai_25",
    "65567": "gse_ai_26",
    "65568": "gse_ai_27",
    "65569": "gse_ai_28",
    "65570": "gse_ai_29",
    "65571": "gse_ai_30",
    "65572": "gse_ai_31",
    "65573": "gse_ai_32",
    "65574": "gse_ai_33",
    "65575": "gse_ai_34",
    "65576": "gse_ai_35",
    "65694": "gse_doa_1",
    "65695": "gse_doa_2",
    "65696": "gse_doa_3",
    "65697": "gse_doa_4",
    "65698": "gse_doa_5",
    "65699": "gse_doa_6",
    "65700": "gse_doa_7",
    "65701": "gse_doa_8",
    "65702": "gse_doa_9",
    "65703": "gse_doa_10",
    "65704": "gse_doa_11",
    "65705": "gse_doa_12",
    "65706": "gse_doa_13",
    "65707": "gse_doa_14",
    "65708": "gse_doa_15",
    "65709": "gse_doa_16",
    "65710": "gse_doa_17",
    "65711": "gse_doa_18",
    "65712": "gse_doa_19",
    "65713": "gse_doa_20",
    "65714": "gse_doa_21",
    "65715": "gse_doa_22",
    "65716": "gse_doa_23",
    "65538": "gse_ai_time",
    "65540": "gse_doa_time"
}

def rename_files(directory, channel_mapping):
    """
    Renames CSV files in the directory based on the channel mapping.
    
    Args:
        directory (str): Path to the directory containing the CSV files.
        channel_mapping (dict): Dictionary mapping keys to channel names.
    
    Returns:
        None
    """
    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        # Check if the file is a CSV file
        if filename.endswith(".csv"):
            # Extract the key (file name without extension)
            key = filename.replace(".csv", "")
            
            # Check if the key exists in the channel mapping
            if key in channel_mapping:
                # Get the new channel name
                new_filename = channel_mapping[key] + ".csv"
                
                # Get the full file paths
                old_file_path = os.path.join(directory, filename)
                new_file_path = os.path.join(directory, new_filename)
                
                # Rename the file
                os.rename(old_file_path, new_file_path)
                print(f"Renamed: {filename} -> {new_filename}")
            else:
                print(f"No mapping found for: {filename}")

# Example usage
directory_path = 'data'  # Replace with the path to your directory containing the CSV files
rename_files(directory_path, channel_mapping)
