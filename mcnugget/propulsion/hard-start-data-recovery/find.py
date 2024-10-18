import pandas as pd

def find_closest_timestamp_indices(file_path, start_timestamp, end_timestamp):
    """
    Finds the indices of the timestamps closest to the start and end timestamps in the provided CSV file.
    
    Args:
        file_path (str): Path to the CSV file (e.g., 65538.csv or 65540.csv).
        start_timestamp (int): The target starting timestamp to find the closest index for.
        end_timestamp (int): The target ending timestamp to find the closest index for.
    
    Returns:
        tuple: (start_index, end_index) where the indices correspond to the closest timestamps.
    """
    try:
        # Read the CSV file into a pandas DataFrame (assuming the first column contains the timestamps)
        data = pd.read_csv(file_path, header=None)

        # Check if the file is empty
        if data.empty:
            print(f"Error: The file {file_path} is empty.")
            return None, None
        
        # Convert the first column (timestamps) to integers
        data[0] = data[0].astype(int)
        
        # Find the index of the timestamp closest to the start timestamp
        start_index = (data[0] - start_timestamp).abs().idxmin()

        # Find the index of the timestamp closest to the end timestamp
        end_index = (data[0] - end_timestamp).abs().idxmin()

        return start_index, end_index
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, None

# Example usage
file_path = 'data/65538.csv'  # Replace with the actual file path
start_timestamp = 1715706000000000000  # May 14, 2024, 5 PM
end_timestamp = 1715756881666610043    # End timestamp
start_index, end_index = find_closest_timestamp_indices(file_path, start_timestamp, end_timestamp)
print(f"Start index: {start_index}, End index: {end_index}")
