import pandas as pd
import os

def filter_csv_by_timestamp(file_path, start_timestamp, end_timestamp):
    """
    Filters a CSV file, keeping only the rows between the start and end timestamps.
    
    Args:
        file_path (str): Path to the CSV file.
        start_timestamp (int): The starting timestamp (inclusive).
        end_timestamp (int): The ending timestamp (inclusive).
    
    Returns:
        pd.DataFrame: The filtered data.
    """
    try:
        # Read the CSV file (assuming the file contains timestamps in the first column)
        data = pd.read_csv(file_path, header=None)

        # Ensure the first column is interpreted as integer timestamps
        data[0] = data[0].astype(int)
        
        # Find the rows between the start and end timestamps
        filtered_data = data[(data[0] >= start_timestamp) & (data[0] <= end_timestamp)]
        
        return filtered_data
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def filter_all_csv_files(directory, start_timestamp, end_timestamp, save_filtered=True):
    """
    Filters all CSV files in a directory, keeping only rows between the start and end timestamps.
    
    Args:
        directory (str): Directory containing the CSV files.
        start_timestamp (int): The starting timestamp (inclusive).
        end_timestamp (int): The ending timestamp (inclusive).
        save_filtered (bool): If True, saves the filtered data back to the files (overwrites original files).
                              If False, saves the filtered data to new files with a '_filtered' suffix.
    
    Returns:
        None
    """
    # for filename in os.listdir(directory):
    filename = "65540.csv"
    if filename.endswith(".csv"):
        file_path = os.path.join(directory, filename)
        
        # Filter the CSV file
        filtered_data = filter_csv_by_timestamp(file_path, start_timestamp, end_timestamp)
        
        if filtered_data is not None:
            if save_filtered:
                # Overwrite the original file with the filtered data
                filtered_data.to_csv(file_path, index=False, header=False)
            else:
                # Save to a new file with '_filtered' suffix
                filtered_file_path = os.path.join(directory, filename.replace(".csv", "_filtered.csv"))
                filtered_data.to_csv(filtered_file_path, index=False, header=False)
            
            print(f"Processed and saved: {filename}")
        else:
            print(f"Skipping: {filename} (Error occurred)")

# Example usage
directory_path = 'data'  # Replace with the directory containing your CSV files
start_timestamp = 1715706000000000000  # May 14, 2024, 5 PM
end_timestamp = 1715756881666610043    # End timestamp

# Run the function to filter all CSV files in the directory
filter_all_csv_files(directory_path, start_timestamp, end_timestamp, save_filtered=True)
