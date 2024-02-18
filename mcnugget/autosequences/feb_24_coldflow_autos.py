import time
import synnax as sy
from synnax.control.controller import Controller


# this connects to Synnax so we're workign with the real deal
client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

#List of channels we're going to read from and write to
#change names and numbers to match the actual channels
FUEL_VENT_IN = "gse_doa_1" # Fuel vent input, 
FUEL_VENT_OUT = "gse_doc_1" # Fuel vent output
PRESS_VENT_IN = "gse_doa_2" # Press vent input
PRESS_VENT_OUT = "gse_doc_2" # Press vent output
OX1_VENT_IN = "gse_doa_3" # Ox vent input
OX1_VENT_OUT = "gse_doc_3" # Ox vent output
OX2_VENT_IN = "gse_doa_4" # Ox vent input
OX2_VENT_OUT = "gse_doc_4" # Ox vent output

WRITE_TO = [FUEL_VENT_OUT, PRESS_VENT_OUT, OX1_VENT_OUT, OX2_VENT_OUT]
READ_FROM = [FUEL_VENT_IN, PRESS_VENT_IN, OX1_VENT_IN, OX2_VENT_IN]

TEST_DURATION = 10 #seconds to run the test

print("Starting autosequence")
