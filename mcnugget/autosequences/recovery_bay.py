"""
Overview of the recovery bay sequence
1. Set initial system state
    - If the valves are not already denergized, denergize them

2. Energize(Open) valve 1 for 0.5 seconds
3. Denergize(Close) valve 1
4. Wait 1 second

5. Energize(Open) valve 2 for 0.5 seconds
6. Deenergize valve 2

If an abort is triggered, energize(open) valve 2 and denergize(close) valve 1

"""
import syauto
import time
from synnax.control.controller import Controller
import synnax as sy
from datetime import datetime, timedelta
import signal #Handling keyboard interruptions on windows 
import sys

#Define valves here || TODO: CHANGE THESE CHANNELS FOR TESTING
VALVE_1_ACK = "gse_doa_1" 
VALVE_1_CMD = "gse_doc_1"
VALVE_2_ACK = "gse_doa_2"
VALVE_2_CMD = "gse_doc_2"

#Function to handle keyboard ctrl+C interrupts (for windows)
def signal_handler(sig, frame):
    print('You manually interrupted this test')
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
    print("INVALID INPUT: Enter 'real' or 'sim'")
    exit()

CMD_Channels = [VALVE_1_CMD, VALVE_2_CMD]
ACK_Channels = [VALVE_1_ACK, VALVE_2_ACK]

with client.control.acquire(name= "Recovery bay sequence", write= CMD_Channels, read= ACK_Channels, write_authorities= 200) as ctrl:
    #Handling keyboard interrupts on windows 
    signal.signal(signal.SIGINT, signal_handler)  # LOOK INTO HOW THIS WORKS!

    #create valve objects here
    valve_1 = syauto.Valve(auto=ctrl, cmd=VALVE_1_CMD, ack=VALVE_1_ACK, normally_open=False)
    valve_2 = syauto.Valve(auto=ctrl, cmd=VALVE_2_CMD, ack=VALVE_2_ACK, normally_open=False)

    
    def recovery_sequence(state_var:Controller):

        #we set the starting state
        valve_1_energ = state_var[VALVE_1_ACK] 
        valve_2_energ = state_var[VALVE_2_ACK]

        # if bool is 1, valve is energised(closed) - we close valves manually if not energised
        if not valve_1_energ: 
            valve_1.close()

        if not valve_2_energ:  
            valve_2.close()

        print("Starting state set(Both valves closed)")


        # recovery
        print("Energizing valve 1 for 0.5 seconds")
        valve_1.open()
        time.sleep(0.5)
        print("De-Energizing valve 1")
        valve_1.close()
        time.sleep(1)

        print("Energizing valve 2 for 0.5 seconds")
        valve_2.open()
        time.sleep(0.5)
        print("Denergizing valve 2")
        valve_2.close()
        return True
    



    try: 
        start = datetime.now()
        ctrl.wait_until(recovery_sequence)
        end = datetime.now()
        print("Autosequence complete :)")

    except KeyboardInterrupt:
        print("Manual interrupt")
        
    

        





