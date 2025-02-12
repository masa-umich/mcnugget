import serial.tools.list_ports
import serial
import time
# Note: close the serial monitor in Arduino IDE before running this script.
# Otherwise, the port will be busy and you will get an error.

global default_data_file_name
default_data_file_name = 'data_rpm'

def get_ports():
    boards = []
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if p.vid == 1155: # STM Vendor ID 1155
            boards.append(p.device)
    return boards

def main():
    if not get_ports():
        while not get_ports():
            print('No boards found. Make sure the board is connected. Retrying...', end='\r', flush=True)
        print()
    time.sleep(1) # The serial port takes a second before we can open it
    board = serial.Serial(get_ports()[0], 460800) # Open the serial port
    print("Connected to", get_ports()[0])
    
    bytes_read_total = 0
    data = []
    
    # Messy code that finds the next available data file name if the default is already taken
    i = 0
    data_file_name = default_data_file_name
    while True:
        try: 
            if open(data_file_name + '.csv', 'rb'):
                i += 1
                data_file_name = default_data_file_name + str(i)
        except:
            break

    with open(data_file_name + '.csv', 'wb') as bin:
        try:
            while True:
                data.append(board.read(2048)) # Read 2048 bytes

                # Print the amount of data read
                bytes_read_total += len(data)
                data_read = bytes_read_total / 1024
                print(f"Amount of data read: {data_read:.2f} KB", end='\r', flush=True)

                # If all the data is 0xFF, we've reached the end of the file
                if data[-1] == (b'\xff' * len(data[-1])):
                    print("\nBad block of data, probably end of file", end='\r', flush=True)
                    break
        except KeyboardInterrupt:
            pass
        for data in data:
            bin.write(data)
        board.close()
        print('\nExiting...')

if __name__ == '__main__':
    main()