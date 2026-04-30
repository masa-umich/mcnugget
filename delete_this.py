import os
import time
import sys

def monitor_growth(filename):
    full_path = os.path.expanduser(filename)

    if not os.path.exists(full_path):
        print(f"Error: File not found at {full_path}")
        return

    print(f"Monitoring: {full_path}")
    print("Press Ctrl+C to stop.\n")

    last_size = os.path.getsize(full_path)
    last_time = time.time()

    try:
        while True:
            current_time = time.time()
            current_size = os.path.getsize(full_path)
            
            # Calculate duration and delta
            elapsed = current_time - last_time
            size_diff = current_size - last_size
            
            # Calculate speed (bytes per second)
            # Avoid division by zero just in case
            speed = size_diff / elapsed if elapsed > 0 else 0
            
            # Formatting the speed for readability
            if speed < 1024:
                speed_str = f"{speed:,.2f} B/s"
            elif speed < 1024**2:
                speed_str = f"{speed/1024:,.2f} KB/s"
            else:
                speed_str = f"{speed/(1024**2):,.2f} MB/s"

            # Clear line and print status
            output = f"\rSize: {current_size:,} bytes | Speed: {speed_str}      "
            sys.stdout.write(output)
            sys.stdout.flush()

            # Update state for next iteration
            last_size = current_size
            last_time = current_time
            
            time.sleep(0.5) # 2Hz
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    # Change this to your target file in the ~ directory
    target = "/mnt/c/Users/brynp/limewire/src/log_parser/serial_dump.bin"
    monitor_growth(target)
