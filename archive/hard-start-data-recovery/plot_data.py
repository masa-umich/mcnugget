import pandas as pd
import matplotlib.pyplot as plt
import sys

def plot_data(data_file, timestamp_file):
    # Read the data CSV (first argument)
    data = pd.read_csv(data_file, header=None)

    # Read the timestamp CSV (second argument)
    timestamps = pd.read_csv(timestamp_file, header=None)

    # Check if both files have the same number of rows
    if len(data) != len(timestamps):
        print("Error: Data and timestamp files do not have the same number of rows.")
        return

    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps[0], data[0], label=f"Data from {data_file}")

    # Set plot labels and title
    plt.xlabel('Timestamps')
    plt.ylabel('Data Values')
    plt.title('Data vs Timestamps')

    # Show legend and grid
    plt.legend()
    plt.grid(True)

    # Display the plot
    plt.show()

if __name__ == "__main__":
    # Ensure two arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python plot_data.py <data_file.csv> <timestamp_file.csv>")
    else:
        # Get the file names from the command line arguments
        data_file = sys.argv[1]
        timestamp_file = sys.argv[2]

        # Plot the data
        plot_data(data_file, timestamp_file)

