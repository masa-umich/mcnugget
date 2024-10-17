from synnax import Synnax

# Replace this with the address of your Synnax server
SYN_SERVER_ADDRESS = "localhost:9090"

# Define the channel name patterns
PATTERN_AI = "gse_ai_{}"
PATTERN_DOA = "gse_doa_{}"

def check_channels():
    # Connect to the Synnax server
    client = Synnax(SYN_SERVER_ADDRESS)

    try:
        # Loop through values of N from 1 to 99
        for N in range(1, 100):
            # Format the channel names
            channel_ai_name = PATTERN_AI.format(N)
            channel_doa_name = PATTERN_DOA.format(N)
            
            # Check if the 'gse_ai_N' channel exists
            try:
                channel_ai = client.channels.retrieve(channel_ai_name)
                print(f"Found channel: Key: {channel_ai.key}, Name: {channel_ai.name}")
            except Exception:
                print(f"Channel {channel_ai_name} not found.")

            # Check if the 'gse_doa_N' channel exists
            try:
                channel_doa = client.channels.retrieve(channel_doa_name)
                print(f"Found channel: Key: {channel_doa.key}, Name: {channel_doa.name}")
            except Exception:
                print(f"Channel {channel_doa_name} not found.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    check_channels()
