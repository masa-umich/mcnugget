#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax>=0.40.0",
#     "termcolor",
#     "yaspin",
#   ]
# ///

#
# rt-flowmeter.py
# 
# Last updated: Oct 20, 2025
# Author(s): <author's uniqname>
#

from termcolor import colored
from yaspin import yaspin
# Adds a fun spinner :)
spinner = yaspin()
spinner.text = colored("Connecting to cluster...", "yellow")
spinner.start()

# Connect to the cluster
import synnax as sy

try:
    client = sy.Synnax()
except:
    try:
        client = sy.Synnax(
            host="synnax.masa.engin.umich.edu", port=9090, username="synnax", password="seldon"
        )
    except:
        spinner.stop()
        raise Exception(colored("Error initializing Synnax client, are you sure you're connected? Type `sy login` to login", "red"))

def main():
    pass # put code here
    # 1. Go over every entry in `config.json` and make a new channel for it or grab one if it already exists
    # 2. Calculate flowrate based on venturi flowrate equation for each flowmeter
    # 3. Write those values to Synnax continuously


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("Shutting down...", "red"))
        exit()
    spinner.stop()
