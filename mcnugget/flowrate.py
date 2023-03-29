import synnax
from mcnugget.query import read 
from mcnugget.time import elapsed_seconds
import numpy as np
import matplotlib.pyplot as plt
TR = synnax.TimeRange(1677367953382773500, 1677367965922904600)



# Read in Data
DATA = read(TR,"ec.pressure[7]", "Time")

# Set Variables for Pressure (also convert it to Pa) and Time
Time = elapsed_seconds(DATA["Time"])
DPs = DATA["ec.pressure[7]"] * 6895

















