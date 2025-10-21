import os
import json
import numpy as np
import pandas as pd

def read_data(metaconfig_file, data_dir, output_dir, sample_count=1620000):
    # Load the metaconfig.json file
    with open(metaconfig_file, 'r') as f:
        config = json.load(f)

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Process float32 and uint8 keys
    # for key_type in ['float32', 'uint8']:
    for key_type in ['timestamp']:
        # dtype = np.float32 if key_type == 'float32' else np.uint8
        dtype = np.uint64

        for key in config[key_type]:
            input_file = os.path.join(data_dir, f"{key}/1.domain")  # Assume file structure
            if os.path.exists(input_file):
                try:
                    # Read the binary data from the file
                    data = np.fromfile(input_file, dtype=dtype)
                    
                    # Check if there is enough data
                    if data.size < sample_count:
                        print(f"File {input_file} contains less than {sample_count} samples.")
                        data_to_save = data
                    else:
                        # Get the last `sample_count` samples
                        data_to_save = data[-sample_count:]

                    # Convert to DataFrame for saving as CSV
                    df = pd.DataFrame(data_to_save)

                    # Save the data to a CSV file
                    output_file = os.path.join(output_dir, f"{key}.csv")
                    df.to_csv(output_file, index=False, header=False)
                    print(f"Saved {sample_count} samples from {input_file} to {output_file}")

                except Exception as e:
                    print(f"Error processing {input_file}: {e}")
            else:
                print(f"File {input_file} not found.")

if __name__ == "__main__":
    read_data('metaconfig.json', '/Users/evanhekman/masa/var/lib/docker/volumes/deploy_synnax-data/_data/cesium', 'new_data')
