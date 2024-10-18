import pandas as pd

def find_indices(file_path, start_timestamp, end_timestamp):
    """
    Finds the index of the first timestamp at or above the start timestamp,
    and the index of the timestamp exactly matching the end timestamp.
    
    Args:
        file_path (str): Path to the CSV file (e.g., 65538.csv or 65540.csv).
        start_timestamp (int): The target starting timestamp to find the first index for.
        end_timestamp (int): The exact ending timestamp to find the index for.
    
    Returns:
        tuple: (start_index, end_index) where start_index corresponds to the first timestamp at or above
               start_timestamp, and end_index corresponds to the exact timestamp for end_timestamp.
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
        
        # Find the first index where the timestamp is at or above the start timestamp
        start_index = data[data[0] >= start_timestamp].index[0]

        # Find the index where the timestamp exactly matches the end timestamp
        if end_timestamp in data[0].values:
            end_index = data[data[0] == end_timestamp].index[0]
        else:
            print(f"Error: End timestamp {end_timestamp} not found in {file_path}.")
            return None, None

        # Debug: Print the timestamps and their indices
        print(f"First start timestamp at or above {start_timestamp}: {data[0].iloc[start_index]}, at index: {start_index}")
        print(f"Exact end timestamp {end_timestamp}: {data[0].iloc[end_index]}, at index: {end_index}")

        return start_index, end_index
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, None

# Example usage
file_path = 'data/65538.csv'  # Replace with the actual file path
start_timestamp = 1715706000000000000  # May 14, 2024, 5 PM
end_timestamp = 1715756881666610043    # Exact end timestamp
start_index, end_index = find_indices(file_path, start_timestamp, end_timestamp)
print(f"Start index: {start_index}, End index: {end_index}")
