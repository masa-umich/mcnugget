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

PRE_VALVE1_IN = "gse_doa_5" # Pre-valve 1
PRE_VALVE1_OUT = "gse_doc_5" # Pre-valve 1
PRE_VALVE2_IN = "gse_doa_6" # Pre-valve 2
PRE_VALVE2_OUT = "gse_doc_6" # Pre-valve 2

PRESS1_VALVE_IN = "gse_doa_7" # Press valve
PRESS1_VALVE_OUT = "gse_doc_7" # Press valve
PRESS2_VALVE_IN = "gse_doa_8" # Ox1 valve
PRESS2_VALVE_OUT = "gse_doc_8" # Ox1 valve

L_STAND_PT = "gse_ai_1" # L-stand pressure
SCUBA_PT = "gse_ai_8" # SCUBA pressure

WRITE_TO = [FUEL_VENT_OUT, PRESS_VENT_OUT, OX1_VENT_OUT, OX2_VENT_OUT]
READ_FROM = [FUEL_VENT_IN, PRESS_VENT_IN, OX1_VENT_IN, OX2_VENT_IN]

#Time, pressure, and other parameters to defind during testing
TEST_DURATION = 10 #seconds to run the test
MAX_PRESSURE = 500 #maximum pressure in the system
MIN_PRESSURE = 250 #minimum pressure in the system

print("Starting autosequence")
with client.control.acquire(name="shakedown", write=WRITE_TO, read=READ_FROM) as auto:
    
    fuel_vent = syauto.Valve(auto=auto, cmd=FUEL_VENT_OUT, ack=FUEL_VENT_IN)
    press_vent = syauto.Valve(auto=auto, cmd=PRESS_VENT_OUT, ack=PRESS_VENT_IN)
    ox1_vent = syauto.Valve(auto=auto, cmd=OX1_VENT_OUT, ack=OX1_VENT_IN)
    ox2_vent = syauto.Valve(auto=auto, cmd=OX2_VENT_OUT, ack=OX2_VENT_IN)
    vents = [fuel_vent, press_vent, ox1_vent, ox2_vent]

    prevalve1 = syauto.Valve(auto=auto, cmd=PRE_VALVE1_OUT, ack=PRE_VALVE1_IN)
    prevalve2 = syauto.Valve(auto=auto, cmd=PRE_VALVE2_OUT, ack=PRE_VALVE2_IN)
    pressvalve1 = syauto.Valve(auto=auto, cmd=PRESS1_VALVE_OUT, ack=PRESS1_VALVE_IN)
    pressvalve2 = syauto.Valve(auto=auto, cmd=PRESS2_VALVE_OUT, ack=PRESS2_VALVE_IN)
    valves = [prevalve1, prevalve2, pressvalve1, pressvalve2]

    pressure = [auto[L_STAND_PT]] #initial pressure, change this based on P&ID

    def run_shakedown(auto_: Controller):
        
        # aborts if the pressure is above the accepted maximum
        if pressure > MAX_PRESSURE:
            print("pressure has exceeded acceptable range - ABORTING and opening all vents")
            syauto.open_all_valves(vents)

        # aborts if the pressure is below the accepted minimum
        if pressure < MIN_PRESSURE:
            print(f"pressure below {MIN_PRESSURE} - ABORTING and opening all vents")
            syauto.open_all_valves(vents)
            print(f"All vents open, closing pre-valves")

        # if the pressure drops below 15, the tanks are mostly empty and the test is finished
        return pressure < 15

    try:
        print("Starting TPC Test. Setting initial system state.")
        #starting opening all valves and closing all vents
        syauto.open_all_valves(valves)
        syauto.close_all_valves(vents)
        time.sleep(2)
       
        print("Purging system for " + TEST_DURATION + " seconds")
        auto.wait_until(TEST_DURATION, run_shakedown(auto))

        print("Test complete. Safing System")

        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} shakedown Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )
    except KeyboardInterrupt as e:
        # Handle Ctrl+C interruption
        if str(e) == "Interrupted by user.":
            print("Test interrupted. Safeing System")
            syauto.open_close_many_valves(auto, valves, vents)

        # Handle 'x' key interruption
        elif str(e) == "Interrupted by user. (x)":
            print("Test interrupted. Safeing System")
            syauto.open_close_many_valves(auto, valves, vents)

    time.sleep(60)