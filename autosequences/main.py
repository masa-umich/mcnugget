"""

### OVERVIEW ###

This combines running coldflow, press_fill, and hotfire

To be used for test cases! 
"""

import subprocess
import time
import os

try:
    # start the coldflow and press_fill autosequence
    cold_flow = subprocess.Popen(["python3", "coldflow_auto_sims.py"])
    time.sleep(3)
    press_fill = subprocess.Popen(["python3", "press_fill.py"], stdin = subprocess.PIPE, text=True)
    time.sleep(1)

    # simulates user input that is required for the press_fill autosequence
    press_fill.stdin.write("sim\n")
    press_fill.stdin.flush()
    time.sleep(2)
    press_fill.stdin.write("start\n")
    press_fill.stdin.flush()
    time.sleep(10)
    press_fill.stdin.write("\n")
    press_fill.stdin.flush()
    time.sleep(70)

    # start the hotfire autosequence
    hotfire = subprocess.Popen(["python3", "hotfire.py", "noox"], stdin = subprocess.PIPE, text = True)
    time.sleep(2)
    hotfire.stdin.write("sim\n")
    hotfire.stdin.flush()
    time.sleep(2)
    hotfire.stdin.write("bypass\n")
    hotfire.stdin.flush()
    time.sleep(2)
    hotfire.stdin.write("start\n")
    hotfire.stdin.flush()
    time.sleep(10)

    # ensures that the autosequences keep running
    cold_flow.wait()
    press_fill.wait()
    hotfire.wait()

except KeyboardInterrupt as e: 
    # kills all the processes
    cold_flow.kill()
    press_fill.kill()
    hotfire.kill()