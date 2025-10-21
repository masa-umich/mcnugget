#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax==0.45.0",
#     "termcolor",
#     "yaspin",
# ]
# ///

#
# fc-stress-test.py
# automatically turn on and off valve 1 indefinitely
#
# Last updated: Oct 16, 2025
# Author: jackmh
#

FC_VLV_1_CMD = "fc_vlv1_cmd"
FC_VLV_1_STATE = "fc_vlv1_state"

import time
from termcolor import colored
from yaspin import yaspin
# Adds a fun spinner :)
spinner = yaspin()
spinner.text = colored("Initializing...", "yellow")
spinner.start()

import synnax as sy

try:
    client = sy.Synnax()
except:
    try:
        client = sy.Synnax(
            host="synnax.masa.engin.umich.edu", port=5050, username="synnax", password="seldon" # port 5050 is the temporary v0.45 cluster
        )
    except:
        pass
        spinner.stop()
        raise Exception(colored("Error initializing Synnax client, are you sure you're connected? Type `synnax login` to login", "red"))
    
def main():

    with client.control.acquire(
        # A useful name that identifies the sequence to the rest of the system. We highly
        # recommend keeping these names unique across your sequences.
        name="FC Stress Test 1",
        # Defines the authorities at which the sequence controls the valve channels. This is
        # a number from 0 to 255. A writer with a higher control authority can override a
        # writer with a lower control control authority.
        write_authorities=[200],
        # We need to set the channels we'll be writing to and reading from.
        write=[FC_VLV_1_CMD],
        read=[FC_VLV_1_STATE],
    ) as ctrl:
        while True:
            ctrl[FC_VLV_1_CMD] = True
            print("Flight Computer Valve 1: " + ctrl[FC_VLV_1_STATE])
            if (ctrl[FC_VLV_1_STATE] != True):
                raise Exception("Valve state wasn't changed correctly... There's been an issue")
            time.sleep(1) # wait for 1 second
            ctrl[FC_VLV_1_CMD] = False
            print("Flight Computer Valve 1: " + ctrl[FC_VLV_1_STATE])
            if (ctrl[FC_VLV_1_STATE] != False):
                raise Exception("Valve state wasn't changed correctly... There's been an issue")
            time.sleep(1) # wait for 1 second


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("Shutting down...", "red"))
        exit()
    spinner.stop()
    