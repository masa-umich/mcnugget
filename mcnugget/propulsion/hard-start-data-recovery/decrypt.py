import os
import json
import struct
import csv

# Paths
BASE_DIR = "/Users/evanhekman/masa/var/lib/docker/volumes/deploy_synnax-data/_data/cesium/"  # Update with the actual base directory
META_CONFIG_PATH = "metaconfig.json"
OUTPUT_DIR = "data"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Number of samples to extract
SAMPLES_TO_EXTRACT = 1620000

# Bytes required for each data type
BYTES_PER_TYPE = {
    "float32": 4,  # 4 bytes per float32
    "uint8": 1,    # 1 byte per uint8
    "uint64": 8,    # 8 bytes per int64
    "timestamp": 8 # 8 bytes per int64
}

# Function to check if the file contains enough data
def has_enough_data(file_path, data_type):
    required_bytes = SAMPLES_TO_EXTRACT * BYTES_PER_TYPE[data_type]
    file_size = os.path.getsize(file_path)
    return file_size >= required_bytes

def extract_samples_from_end(file_path, data_type, num_samples):
    samples = []
    bytes_per_sample = BYTES_PER_TYPE[data_type]
    file_size = os.path.getsize(file_path)
    
    # Calculate the start position (from the end) to read the last `num_samples`
    start_position = file_size - (num_samples * bytes_per_sample)
    
    # Open the binary file in read mode
    with open(file_path, "rb") as f:
        f.seek(start_position)  # Move to the calculated start position
        
        if data_type == "timestamp":  # Treat as int64 (8 bytes per value)
            for _ in range(num_samples):
                data = f.read(8)  # 8 bytes per int64
                if not data:
                    break
                samples.append(struct.unpack('q', data)[0])  # 'q' is for signed int64

    return samples

# Function to read binary data from '1.domain' based on data type
def extract_samples(file_path, data_type, num_samples):
    samples = []

    # Open the binary file in read mode
    with open(file_path, "rb") as f:
        if data_type == "float32":
            # Extract float32 values
            for _ in range(num_samples):
                data = f.read(4)  # 4 bytes per float32
                if not data:
                    break
                samples.append(struct.unpack('f', data)[0])

        elif data_type == "uint8":
            # Extract uint8 values
            for _ in range(num_samples):
                data = f.read(1)  # 1 byte per uint8
                if not data:
                    break
                samples.append(struct.unpack('B', data)[0])

        elif data_type == "timestamp":
            # Extract int64 (timestamps)
            for _ in range(num_samples):
                data = f.read(8)  # 8 bytes per int64
                if not data:
                    break
                samples.append(struct.unpack('q', data)[0])

    return samples

# Function to save the samples as a CSV
def save_as_csv(folder_name, samples):
    output_file = os.path.join(OUTPUT_DIR, f"{folder_name}.csv")
    with open(output_file, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([folder_name])  # Write header with the folder name
        for sample in samples:
            writer.writerow([sample])  # Write each sample as a new row

def process_folders(base_dir, meta_config_path):
    # Load the metaconfig.json file
    with open(meta_config_path, "r") as f:
        meta_config = json.load(f)

    # Process each data type group in the metaconfig
    for data_type, folders in meta_config.items():
        for folder_name in folders:
            folder_path = os.path.join(base_dir, str(folder_name))
            domain_file = os.path.join(folder_path, "1.domain")

            # Only process if '1.domain' file exists and has enough data
            if os.path.exists(domain_file) and has_enough_data(domain_file, data_type):
                print(f"Processing folder {folder_name} for data_type {data_type}...")

                # Extract samples based on the data type
                samples = extract_samples_from_end(domain_file, data_type, SAMPLES_TO_EXTRACT)

                # Save the samples to CSV
                save_as_csv(folder_name, samples)
            else:
                print(f"Skipping folder {folder_name}: Insufficient data in '1.domain'.")

if __name__ == "__main__":
    process_folders(BASE_DIR, META_CONFIG_PATH)