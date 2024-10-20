import pandas as pd

def find_data(file_path, lower_bound, upper_bound):
    try:
        # Read the CSV file containing only timestamps
        data = pd.read_csv(file_path, header=None)

        # Convert to int (assuming timestamps are in the first column)
        data[0] = data[0].astype(int)

        # Find the first index where the timestamp is greater than the lower bound
        try:
            start_index = data[data[0] > lower_bound].index[0]
        except IndexError:
            start_index = -1

        # Find the last index where the timestamp is less than the upper bound
        try:
            end_index = data[data[0] < upper_bound].index[-1]
        except IndexError:
            end_index = -1

        return start_index, end_index

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return -1, -1

if __name__ == "__main__":
    file = 'data/65538.csv'  # Example file
    lower = 1715756281666610043  # Example lower bound
    upper = 1715756881666610043  # Example upper bound
    start_index, end_index = find_data(file, lower, upper)
    print(f"Start index: {start_index}, End index: {end_index}")
