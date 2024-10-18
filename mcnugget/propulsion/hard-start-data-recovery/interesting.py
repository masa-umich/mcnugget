import os
import pandas as pd

def is_interesting(file_path, threshold=100):
    """
    Determines if a CSV file is 'interesting', i.e., if any two consecutive values differ by more than the given threshold.
    
    Args:
        file_path (str): Path to the CSV file.
        threshold (float): The difference threshold to check for.
    
    Returns:
        bool: True if the file is interesting, False otherwise.
    """
    try:
        # Read the CSV file into a pandas DataFrame
        data = pd.read_csv(file_path, header=None)
        
        # Calculate the absolute difference between consecutive rows
        differences = data[0].diff().abs()
        
        # Check if any difference exceeds the threshold
        return (differences > threshold).any()
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def find_interesting_files(directory, threshold=100):
    """
    Iterates through all CSV files in a directory to find the ones that are 'interesting'.
    
    Args:
        directory (str): Directory containing the CSV files.
        threshold (float): The difference threshold to check for.
    
    Returns:
        list: A list of file paths that are 'interesting'.
    """
    interesting_files = []
    
    # Iterate through all CSV files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            
            # Check if the file is interesting
            if is_interesting(file_path, threshold):
                interesting_files.append(filename)
    
    return interesting_files

# Example usage
directory_path = 'data'  # Replace with the directory containing your CSV files
interesting_files = find_interesting_files(directory_path, threshold=100)

print("Interesting files:", interesting_files)
