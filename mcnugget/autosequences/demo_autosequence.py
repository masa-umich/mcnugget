"""

This is an example file intended to explain how autosequences work. 

The summary of what the test does is below and each step in the autosequence explains what it is intended to accomplish. 
Reach out to someone with any questions, and try to follow this general framework when writing your own autosequences:

1. Talk with a Prop RE or ATLO person to find out what the test is intended to do (if you don't already know)
2. Find out the specifics of the test - specifically
    - which valves are used (and what they in the system)
    - when they open
    - how long they open
    - valves/vents should be normally_open = False or normally_open = True
    - how to start and end the test ('safe the system')
    - how to handle the abort case or abort cases
3. Once you know how the test will work and have a plan for how to do it all, 
    copy the boilerplate/setup from an existing autosequence (unless you really want to do it yourself)
4. Then, use the functionality provided in `syauto` to implement the autosequence.

"""

# IMPORT STATEMENTS
import time  # used to specify delays in test
import synnax as sy  # this is synnax
from synnax.control.controller import Controller  # this is the library used to control everything via synnax
import syauto  # this is the autosequence utility library


# CONNECTION PARAMETERS
# you should only use one of the two to connect to local or Ebox.

# these connection parameters connect to a local synnax running on your computer
client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

# these connection parameters connect to the real deal synnax (on the Ebox)
# client = sy.Synnax(
#     host="synnax.masa.engin.umich.edu",
#     port=80,
#     username="synnax",
#     password="seldon",
#     secure=True
# )


# A PNID is a Piping and Instrumentation Diagram. They are very complicated drawings - below is a code representation of one.
"""
                                   ____
                                  |    |
           ---<<<---[A]---<<<-----| P1 |---<<<---[C]---<<<---
          /                       |    |
         /                         ‾‾‾‾
--<<-----
         \                         ____
          \                       |    |
           ---<<<---[B]---<<<-----| P2 |---<<<---[D]---<<<---[E]---<<<---
                                  |    |
                                   ‾‾‾‾


[A] is the FUEL_ISO. It opens to allow pressure to flow from the fuel tanks (not shown) into the Pressure tank. 
[B] is the OX_ISO. It opens to allow pressure to flow from the fuel tanks (not shown) into the Pressure tank.
[C] is the FUEL_PRESS. It opens to allow pressure to flow into a tank which will force the fuel into the combustion chamber.
[D] is the OX_PRESS. It opens to allow pressure to flow into a tank which will force the oxygen into the combustion chamber.
[E] is the OX_PRE_PRESS. It opens before the OX_PRESS to help pressurize the tank which forces the oxygen into the combustion chamber.

P1 is a pressure tank which is used to force fuel into the combustion chamber. 
P2 is a pressure tank which is used to force oxygen into the combustion chamber. 
The contents of these pressure tanks don't actually go into the combustion chamber, but are needed to push fuel and oxygen into the combustion chamber.

"""


# CHANNEL NAMES
# This is just some aliasing to make channel names more readable. The way it actually works is this:
# Each channel has a unique name, and sending data via these channels
#       - allows us to send commands to open/close valves
#       - allows us to read acknoledgements from valves to know whether they are open/closed
#       - allows us to read analog data from PT or TC channels (explained more below)
# There are 5 types of channels you should know
#       - DOC (Digital Output Commands) channels send UINT8 data for 
#       - DOA (Digital Output Acknowledgement) channels send UINT8 data
#       - TIME channels send Synnax TIMESTAMPS to index other types of data (so we know when it was sent)
#       - AI (Analog Input) channels send FLOAT32 data representing 'analog' data
#       - AI channels can represent PTs (Pressure Transducers) or TCs (Thermocouples) to measure pressure or temperature respectively
#
# This part specifies which channels we will read/write to
#       - we will READ from DOA channels (to know whether commands went through)
#       - we will WRITE to DOC channels (to tell valves to open/close)
#       - we will READ from AI/TC channels (to tell what pressure is like in the system)
#       - we will use the TIME channels as INDEXES for other channels (we don't read/write directly with the time channels)

WRITE_TO = []  # the list we will write to (DOC)
READ_FROM = []  # the list we will read from (DOA, PT/TC)

# if we are using a lot of channels of a certain type, we can create them with a loop
for i in range(1, 28):  # 1-28 because that's how many channels are on the Ebox
    WRITE_TO.append(f"gse_doc_{i}")
    READ_FROM.append(f"gse_doa_{i}")

# we can also add channels specifically 
OX_PT = "gse_ai_1"
FUEL_PT = "gse_ai_2"

PTs = [OX_PT, FUEL_PT]

READ_FROM += PTs  # don't forget to add all channels to the applicable write and read lists

# this takes control of synnax under the name "Demo Autosequence". 
# it has authority to write to channels in WRITE_TO and read to channels in READ_TO with an authority level of 250
# throughout the rest of the autosequence we use this object as `auto`.
with client.control.acquire(name="Demo Autosequence",
                             write=WRITE_TO, read=READ_FROM, write_authorities=250 ) as auto:

    # Here we declare valve objects which we will rely on throughout the rest of the autosequence.

    # `syauto.Valve` objects have 2 important methods:
    #       - open()
    #       - close()
    # the `syauto` library also includes functions to do more complicated valve things, like 
    #       - automate pressurizing a tank to a certiain pressure with specified valves
    #       - open/close many valves at the same time

    # prevalves
    fuel_press = syauto.Valve(
        auto=auto, cmd="gse_doc_1", ack="gse_doa_1", normally_open=False, name="fuel_press")
    ox_press = syauto.Valve(
        auto=auto, cmd="gse_doc_2", ack="gse_doa_2", normally_open=False, name="ox_press")
    ox_pre_press = syauto.Valve(
        auto=auto, cmd="gse_doc_3", ack="gse_doa_3", normally_open=False, name="ox_pre_press")
    
    # ISO valves
    fuel_press_ISO = syauto.Valve(
        auto=auto, cmd="gse_doc_4", ack="gse_doa_4",  normally_open=False, name="fuel_press_ISO")
    ox_press_ISO = syauto.Valve(
        auto=auto, cmd="gse_doc_5", ack="gse_doa_5", normally_open=False, name="ox_press_ISO")
    
    # there are no vents in this autosequence, but this is an example of how to declare one
    nonexistent_vent = syauto.Valve(
        auto=auto, cmd="gse_doc_18", ack="gse_doa_18", normally_open=True, name="nonexistent_vent")
    
    # Look at the `syauto` library to learn more about the specifics.
    #       - `auto=auto` assigns the controller to the valve, so all valves are on the same 'network'
    #       - `cmd=gse_doc_X` tells the valve to write commands to `gse_doc_X`
    #       - `ack=gse_doa_X` tells the valve to read acknowledgements from `gse_doa_X`
    #       - `normally_open=True/False` sets the valve to be open/closed in the default state, respectively
    #       - `name="name"` is purely an alias used for recognizing what vent you are dealing with (when needed)


    ###     THIS SECTION RUNS THE AUTOSEQUENCE AS FOLLOWS       ###
    ###         - opens the FUEL_PRESS valve until FUEL_PT reaches TARGET_1
    ###         - opens the OX_PREPRESS and OX_PRESS valves until OX_PT reaches TARGET_2
    ###         - waits for user confirmation to continue autosequence
    ###         - opens the FUEL_ISO and OX_ISO at the same time for DELAY_1 seconds
    ###         - closes the FUEL_ISO and OX_ISO


    # Always confirm test specs like these are correct before running the autosequence
    TARGET_1 = 500  # psi
    TARGET_2 = 600  # psi
    DELAY_1 = 20  # seconds

    print("starting autosequence")

    print(f"pressurizing FUEL_PT:{FUEL_PT} using {fuel_press.name}")   # useful for debugging to know what's happening

    # this opens and closes fuel_press to pressurize the fuel tank to TARGET_1 pressure in 10 increments
    syauto.pressurize(auto=auto, valve_s=fuel_press, pressure_s=FUEL_PT, target=TARGET_1, inc=(TARGET_1 / 10))

    print(f"pressurizing OX_PT:{OX_PT} using {ox_press.name}:{ox_press.cmd_chan} and {ox_pre_press.name}:{ox_pre_press.cmd_chan}")   
    # The above statement is just useful for debugging to know what's happening
    # It's not strictly necessary and you only need to use it if you think its a good idea

    syauto.pressurize(auto=auto, valve_s=[ox_press, ox_pre_press], pressure_s=OX_PT, target=TARGET_2, inc=(TARGET_2 / 20))

    input("both tanks are pressurized - press any key to continue")

    # this function takes a list and opens all the specified valves at the same time
    print("opening both ISOs")
    syauto.open_all(auto, [ox_press_ISO, fuel_press_ISO])

    print(f"waiting {DELAY_1} seconds")
    time.sleep(DELAY_1)

    # this function takes a list and closes all the specified valves at the same time
    print("closing both ISOs")
    syauto.close_all(auto, [ox_press_ISO, fuel_press_ISO])

    print("autosequence completed")
