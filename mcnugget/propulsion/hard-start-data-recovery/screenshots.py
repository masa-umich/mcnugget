import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

def parse_df(csv_file_path):
    """Reads a CSV file and returns it as a pandas DataFrame."""
    df = pd.read_csv(csv_file_path, header=None)
    print(f"Successfully read CSV file: {csv_file_path}")
    return df

def graph_and_save(title, df, timestamps, output_dir):
    """Generates and saves a graph for the given data and timestamps."""
    plt.figure(figsize=(13, 8))
    plt.title(title)
    plt.plot(timestamps, df[0].astype(float))  # Assuming the data is in the first column
    plt.grid(True)

    # Save the plot
    output_file = os.path.join(output_dir, f"{title.replace(' ', '_')}.png")
    plt.savefig(output_file)
    print(f"Saved graph to {output_file}")
    plt.close()  # Close the figure to avoid memory issues

def generate_screenshots(filtered_data_dir, output_dir):
    """Generates screenshots for all channels in filtered_data/ using appropriate timestamps."""
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load timestamp data for AI and DOA channels
    ai_timestamp_file = os.path.join(filtered_data_dir, 'gse_ai_time.csv')
    doa_timestamp_file = os.path.join(filtered_data_dir, 'gse_doa_time.csv')

    if not os.path.exists(ai_timestamp_file) or not os.path.exists(doa_timestamp_file):
        print("Error: AI or DOA timestamp files not found.")
        return

    # Read timestamps for AI and DOA channels
    ai_timestamps_df = parse_df(ai_timestamp_file)
    doa_timestamps_df = parse_df(doa_timestamp_file)

    # Convert timestamps to pandas Timestamps
    ai_timestamps = ai_timestamps_df[0].astype(float)
    translated_ai_timestamps = [pd.Timestamp(ts, unit='ns') for ts in ai_timestamps]

    doa_timestamps = doa_timestamps_df[0].astype(float)
    translated_doa_timestamps = [pd.Timestamp(ts, unit='ns') for ts in doa_timestamps]

    # Iterate through all files in the filtered_data directory
    for file_name in os.listdir(filtered_data_dir):
        # Skip the time index files
        if file_name == 'gse_ai_time.csv' or file_name == 'gse_doa_time.csv':
            continue
        
        file_path = os.path.join(filtered_data_dir, file_name)
        
        if file_name.startswith("gse_ai_"):
            # Use AI timestamps for AI channels
            timestamps = translated_ai_timestamps
        elif file_name.startswith("gse_doa_"):
            # Use DOA timestamps for DOA channels
            timestamps = translated_doa_timestamps
        else:
            print(f"Skipping unknown channel file: {file_name}")
            continue

        # Load the data for the current channel
        df = parse_df(file_path)

        # Generate and save the graph
        graph_and_save(file_name.replace(".csv", ""), df, timestamps, output_dir)

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) != 3:
        print("Usage: python screenshots.py <filtered_data_dir> <output_dir>")
    else:
        filtered_data_dir = sys.argv[1]
        output_directory = sys.argv[2]

        generate_screenshots(filtered_data_dir, output_directory)
