import synnax as sy
import getpass
import time

# --- Configuration ---
HOST = "masasynnax.ddns.net"
PORT = 9090
STATE_CH = "gse_state_1"  # For monitoring
CMD_CH   = "gse_vlv_1"    # For commanding

def run_timed_sequence():
    print(f"Connecting to Synnax at {HOST}:{PORT}...")
    
    # 1. Credentials
    user = "synnax"
    pwd = "seldon"

    # 2. Initialize Client
    client = sy.Synnax(
        host=HOST, 
        port=PORT, 
        username=user, 
        password=pwd
    )

    print("Authenticating and acquiring control...")
    print("Press CTRL+C to stop the sequence safely.")

    # 3. Control Context
    # Name "Timed Valve Sequence" is passed as the first positional argument
    with client.control.acquire(
        "Timed Valve Sequence",
        read=[STATE_CH], 
        write=[CMD_CH], 
        write_authorities=[sy.Authority.ABSOLUTE]
    ) as controller:
        
        try:
            while True:
                # --- PHASE 1: OPEN (5 Seconds) ---
                print(f"[{time.strftime('%H:%M:%S')}] Opening valve...")
                controller[CMD_CH] = 1
                
                # Optional: specific check to see if it actually opened
                # time.sleep(0.5)
                # print(f"   State is: {controller[STATE_CH]}")

                time.sleep(5)

                # --- PHASE 2: CLOSE (55 Seconds) ---
                print(f"[{time.strftime('%H:%M:%S')}] Closing valve...")
                controller[CMD_CH] = 0
                
                print("   Waiting 55 seconds for next cycle...")
                time.sleep(55)

        except KeyboardInterrupt:
            print("\nSequence interrupted by user!")
            
            # --- SAFETY SHUTDOWN ---
            print("Safety: Forcing valve CLOSED before release...")
            controller[CMD_CH] = 0
            time.sleep(0.5) # Give it a moment to process
            
            print("Valve closed. Exiting.")

if __name__ == "__main__":
    try:
        run_timed_sequence()
    except Exception as e:
        print(f"\nAn error occurred: {e}")