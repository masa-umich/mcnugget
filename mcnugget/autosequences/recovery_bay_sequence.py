"""
Overview of the recovery bay sequence
1. Set initial system state
    - If the valves are not already denergized, denergize them

2. Energize valve 1 for 2 seconds
3. Denergize valve 1 for 1 second
4. Energize valve 2 for 5 seconds
5. Deenergize valve 2

If an abort is triggered, energize valve 2 and denergize valve 1

"""
import syauto
import time
from synnax.control.controller import Controller
import synnax as sy
from datetime import datetime, timedelta
import signal #Handling keyboard interruptions on windows 
import sys

#Define valves here 
VALVE_1_ACK = "gse_doa_1" #TODO: Change these to the actual channels for testing
VALVE_1_CMD = "gse_doc_1"
VALVE_2_ACK = "gse_doa_2"
VALVE_2_CMD = "gse_doc_2"

#Function to handle keyboard ctrl+C interrupts (for windows)
def signal_handler(sig, frame):
    print('Test interrupted')
    sys.exit(0)

#Prompts for user input as to whether we want to run a simulation or run an actual test
#If prompted to run a coldflow test, we will connect to the MASA remote server
mode = input("Enter 'real' for coldflow/hotfire or 'sim' to run a simulation: ")
if(mode == "real" or mode == "Real" or mode == "REAL"):
    real_test = True
    print("Testing mode")
    # this connects to the synnax testing server
    client = sy.Synnax(
    host="synnax.masa.engin.umich.edu",
    port=80,
    username="synnax",
    password="seldon",
    secure=True
    )

#If prompted to run a simulation, the delay will be 1 second and we will connect to the synnax simulation server
elif mode == "sim" or mode == "Sim" or mode == "SIM" or mode == "":
    real_test = False
    print("Simulation mode")
    # this connects to the synnax simulation server
    client = sy.Synnax(
        host="localhost",
        port=9090,
        username="synnax",
        password="seldon",
        secure=False
    )

else:
    print("Bestie what are you trying to do? If it's a typo, just try again, we're gonna close to program for now though <3")
    exit()

CMD_Channels = [VALVE_1_CMD, VALVE_2_CMD]
ACK_Channels = [VALVE_1_ACK, VALVE_2_ACK]

with client.control.acquire(name= "Recovery bay sequence", write= CMD_Channels, read= ACK_Channels, write_authorities= 200) as auto:
    #Handling keyboard interrupts on windows 
    signal.signal(signal.SIGINT, signal_handler) 

    #create valve objects here
    valve_1 = syauto.Valve(auto=auto, cmd=VALVE_1_CMD, ack=VALVE_1_ACK, normally_open=False)
    valve_2 = syauto.Valve(auto=auto, cmd=VALVE_2_CMD, ack=VALVE_2_ACK, normally_open=False)

    def recovery_sequence(auto_:Controller):

        #Defining abstractions for valve states here
        valve_1_open = auto_[VALVE_1_ACK]
        valve_2_open = auto_[VALVE_2_ACK]
        print(valve_1_open)
        print(valve_2_open)
        print("Starting autosequence setting initial system state")
        if not valve_1_open:
            valve_1.close()

        if not valve_2_open:
            valve_2.close()

        print("Energizing valve 1 for 2 seconds")
        valve_1.open()
        time.sleep(2)
        print("Denergizing valve 1")
        valve_1.close()
        print("Energizing valve 2 for 5 seconds")
        valve_2.open()
        time.sleep(5)
        print("Denergizing valve 2")
        valve_2.close()
        return True

    try: 
        start = datetime.now()
        auto.wait_until(recovery_sequence)
        end = datetime.now()
        print("Autosequence complete :)")
    
    except KeyboardInterrupt:
        print("Autosequence interrupted, energizing valve 2 and denergizing valve 1")
        syauto.open_close_many_valves(auto, [valve_2], [valve_1])