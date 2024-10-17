import os
import json

# Path to the main directory containing the folders (keys)
BASE_DIR = "/Users/evanhekman/masa/var/lib/docker/volumes/deploy_synnax-data/_data/cesium/"

# Output file path for metaconfig.json
OUTPUT_FILE = "metaconfig.json"

def process_folders(base_dir):
    # Dictionary to store folder keys grouped by data_type
    config = {
        "float32": [],
        "uint8": [],
        "uint64": []
    }
    
    # Loop through each folder (key) in the base directory
    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)

        # Only process if it's a folder
        if os.path.isdir(folder_path):
            # Check if the folder contains a '1.domain' file
            domain_file = os.path.join(folder_path, "1.domain")
            if os.path.exists(domain_file):
                # Check if 'meta.json' exists in the folder
                meta_file = os.path.join(folder_path, "meta.json")
                if os.path.exists(meta_file):
                    # Read the meta.json file to extract the data_type
                    with open(meta_file, "r") as f:
                        meta_data = json.load(f)
                        data_type = meta_data.get("data_type")
                    
                    # Group folder by the valid data_type
                    if data_type == "float32":
                        config["float32"].append(int(folder_name))
                    elif data_type == "uint8":
                        config["uint8"].append(int(folder_name))
                    elif data_type == "timestamp":
                        config["uint64"].append(int(folder_name))
    
    # Save the config as a JSON file
    with open(OUTPUT_FILE, "w") as outfile:
        json.dump(config, outfile, indent=4)
    
    print(f"Configuration file '{OUTPUT_FILE}' has been generated.")

if __name__ == "__main__":
    process_folders(BASE_DIR)
