import pandas as pd
import os

def delete_data_outside_indices(file_paths, start_index, end_index):
    """
    Deletes all data outside the range of start_index and end_index for the given list of files.
    
    Args:
        file_paths (list of str): List of file paths to process.
        start_index (int): The starting index.
        end_index (int): The ending index.
    
    Returns:
        None
    """
    for file_path in file_paths:
        try:
            # Read the CSV file into a pandas DataFrame
            data = pd.read_csv(file_path, header=None)
            
            # Keep only the rows between the start and end indices
            filtered_data = data.iloc[start_index:end_index + 1]
            
            # Overwrite the original file with the filtered data
            filtered_data.to_csv(file_path, index=False, header=False)
            
            print(f"Processed and saved: {file_path}")
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

# Example usage
file_paths = ['65542.csv', '65543.csv', '65544.csv']  # Replace with the list of files you want to process
start_index = 100  # Replace with the actual start index
end_index = 200    # Replace with the actual end index
delete_data_outside_indices(file_paths, start_index, end_index)
