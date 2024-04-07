"""
Overview of the recovery bay sequence


"""
import syauto
import time
from synnax.control.controller import Controller
import synnax as sy
from datetime import datetime, timedelta
import signal #Handling keyboard interruptions on windows 
import sys

#Define valves here 

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

CMD_Channels = []
ACK_Channels = []

with client.control.acquire("Pre Press + Reg Fire", ACK_Channels, CMD_Channels, 200) as auto:
    #Handling keyboard interrupts on windows 
    signal.signal(signal.SIGINT, signal_handler) 

    #create valve objects here

    print("Starting autosequence ... ")
    #open valves we want to open

    try: 
        start = datetime.now()

    except KeyboardInterrupt:
        print("Autosequence interrupted")