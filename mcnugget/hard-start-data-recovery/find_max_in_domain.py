import subprocess
import sys
import binascii
import numpy as np

def read_hex_with_offset(file_path, byte_count, offset):
    # Run the shell command to get the last 120KB of the file and pipe it through xxd with the given offset
    try:
        command = f"tail -c {byte_count} {file_path} | xxd -c 8 -s {offset}"  # Use xxd with -s for the offset
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print(f"Error running command: {result.stderr}")
            return None

        # Split the output by lines
        hex_output = result.stdout.splitlines()

        hex_values = []

        # Iterate through the hex dump lines and collect hex values
        for line in hex_output:
            hex_numbers = line.split()[1:]  # Skip the first column (offset)
            hex_values.extend(hex_numbers)

        return hex_values

    except Exception as e:
        print(f"Error processing file: {e}")
        return None

def hex_to_float32(hex_values):
    # Convert the hex values to float32
    float32_values = []
    for i in range(0, len(hex_values), 2):  # Each float32 is 8 hex characters (4 bytes)
        hex_string = hex_values[i] + hex_values[i+1] if i+1 < len(hex_values) else ''
        try:
            # Convert hex to binary
            binary_data = binascii.unhexlify(hex_string)
            # Convert binary data to float32 using numpy
            float_value = np.frombuffer(binary_data, dtype=np.float32)[0]
            float32_values.append(float_value)
        except Exception as e:
            # print(f"Error converting hex {hex_string}: {e}")
            continue
    
    return float32_values

def check_valid_offset(float32_values, offset):
    valid = True
    for i, value in enumerate(float32_values[:100]):  # Process the first 100 values
        # Check if the value is within the valid range
        if np.isnan(value) or value < -1000 or value > 1e6:
            valid = False
            print(f"failed on iteration {i}")
            break
        
        # Print debug information every 10 samples
        if i % 10 == 0:
            print(f"Offset {offset} - Sample {i}: Value = {value}, Valid = {valid}")
    
    return valid

if __name__ == "__main__":
    file_path = sys.argv[1]
    byte_count = 100 * 4  # Adjust as needed
    if not file_path:
        exit(1)

    # Try offsets from 0 to 8 bytes
    for offset in range(33):
        print(f"\nTesting offset {offset}...")
        hex_values = read_hex_with_offset(file_path, byte_count, offset)

        if hex_values:
            float32_values = hex_to_float32(hex_values)

            # Check if the offset produces valid float32 values
            valid = check_valid_offset(float32_values, offset)
            if valid:
                print(f"Offset {offset} is valid!")
            else:
                print(f"Offset {offset} is invalid.")
        else:
            print(f"Could not retrieve hex values for offset {offset}.")
