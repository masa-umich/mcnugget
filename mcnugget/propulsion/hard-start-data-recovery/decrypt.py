"""
This is a script to retrieve uncommitted data from a Synnax server.
"""

import os
import struct
import csv

def extract_last_bytes(file_path, num_bytes):
    file_size = os.path.getsize(file_path)
    if file_size < num_bytes:
        raise ValueError(f"File {file_path} is smaller than {num_bytes} bytes.")
    
    with open(file_path, 'rb') as file:
        file.seek(-num_bytes, os.SEEK_END)
        return file.read(num_bytes)

def bytes_to_float32(byte_data):
    num_floats = len(byte_data) // 4
    return struct.unpack(f'{num_floats}f', byte_data)

def bytes_to_int64(byte_data):
    num_ints = len(byte_data) // 8
    return struct.unpack(f'{num_ints}q', byte_data)

def bytes_to_uint8(byte_data):
    num_ints = len(byte_data)
    return struct.unpack(f'{num_ints}B', byte_data)

def write_to_csv(output_file, data):
    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        for row in data:
            csv_writer.writerow(row)

def process_directory(dirs, num_bytes, output_file, data_type='float32'):
    data = []
    print("Processing directories:")
    for directory in dirs:
        file_path = os.path.join(directory, "1.domain")
        print(f"checking ${file_path}")
        if os.path.exists(file_path):
            last_bytes = None
            while last_bytes is None:
                try:
                    last_bytes = extract_last_bytes(file_path, num_bytes)
                except ValueError:
                    num_bytes //= 2
                    print(f"trying ${num_bytes} bytes")
            print(last_bytes)
            if last_bytes is None:
                print("no data found")
            if data_type == 'float32':
                processed_data = bytes_to_float32(last_bytes)
            elif data_type == 'int64':
                processed_data = bytes_to_int64(last_bytes)
            elif data_type == 'uint8':
                processed_data = bytes_to_uint8(last_bytes)
            else:
                raise ValueError("Unsupported data type")
            data.append([directory] + list(processed_data))
        else:
            print(f"File not found for directory {directory}")
    write_to_csv(output_file, data)

# Example usage
data_dir = '/Users/evanhekman/masa/var/lib/docker/volumes/deploy_synnax-data/_data/cesium/'
# from 65537 to 65763
dirs = [os.path.join(data_dir, str(d)) for d in range(65537, 65764)]
num_bytes = 64  # Adjust as needed
output_file = 'output.csv'
data_type = 'float32'  # Can be 'float32', 'int64', or 'uint8'
process_directory(dirs, num_bytes, output_file, data_type)
