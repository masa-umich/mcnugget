import time
import random
import synnax as sy

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

DAQ_TIME = "daq_time"

# valves for fuel system
FUEL_VENT_IN = "gse_doa_15"  # Fuel vent input,
FUEL_VENT_OUT = "gse_doc_15"  # Fuel vent output
FUEL_PREVALVE_IN = "gse_doa_22"  # Fuel pre-valve input
FUEL_PREVALVE_OUT = "gse_doc_22"  # Fuel pre-valve output

# valves for purge system
FUEL_FEEDLINE_PURGE_IN = "gse_doa_7"  # Fuel feedline purge
FUEL_FEEDLINE_PURGE_OUT = "gse_doc_7"  # Fuel feedline purge
OX_FILL_PURGE_IN = "gse_doa_11"  # Ox fill purge
OX_FILL_PURGE_OUT = "gse_doc_11"  # Ox fill purge
FUEL_PRE_PRESS_IN = "gse_doa_9"  # Fuel pre-press
FUEL_PRE_PRESS_OUT = "gse_doc_9"  # Fuel press press
OX_PRE_PRESS_IN = "gse_doa_10"  # Ox pre-press
OX_PRE_PRESS_OUT = "gse_doc_10"  # Ox press press
OX_FEEDLINE_PURGE_IN = "gse_doa_8"  # Ox feedline purge
OX_FEEDLINE_PURGE_OUT = "gse_doc_8"  # Ox feedline purge

# valves for pneumatics
ENGINE_PNEUMATICS_ISO_IN = "gse_doa_12"  # Engine pneumatics ISO
ENGINE_PNEUMATICS_ISO_OUT = "gse_doc_12"  # Engine pneumatics ISO
ENGINE_PNEUMATICS_VENT_IN = "gse_doa_13"  # Engine pneumatics vent
ENGINE_PNEUMATICS_VENT_OUT = "gse_doc_13"  # Engine pneumatics vent

# valves for press system
AIR_DRIVE_ISO_1_IN = "gse_doa_3"  # Air drive ISO 1
AIR_DRIVE_ISO_1_OUT = "gse_doc_3"  # Air drive ISO 1
AIR_DRIVE_ISO_2_IN = "gse_doa_4"  # Air drive ISO 2
AIR_DRIVE_ISO_2_OUT = "gse_doc_4"  # Air drive ISO 2
GAS_BOOSTER_FILL_IN = "gse_doa_20"  # Gas booster fill
GAS_BOOSTER_FILL_OUT = "gse_doc_20"  # Gas booster fill
PRESS_FILL_IN = "gse_doa_23"  # Press fill
PRESS_FILL_OUT = "gse_doc_23"  # Press fill
PRESS_VENT_IN = "gse_doa_18"  # Press vent
PRESS_VENT_OUT = "gse_doc_18"  # Press vent
FUEL_PRESS_ISO_IN = "gse_doa_2"  # Fuel press ISO
FUEL_PRESS_ISO_OUT = "gse_doc_2"  # Fuel press ISO
OX_PRESS_IN = "gse_doa_1"  # Ox press
OX_PRESS_OUT = "gse_doc_1"  # Ox press

# Ox system pressure valves
OX_LOW_VENT_IN = "gse_doa_16"  # Ox low vent
OX_LOW_VENT_OUT = "gse_doc_16"  # Ox low vent
OX_FILL_VALVE_IN = "gse_doa_19"  # Ox fill valve
OX_FILL_VALVE_OUT = "gse_doc_19"  # Ox fill valve
OX_HIGH_FLOW_VENT_IN = "gse_doa_17"  # Ox high vent
OX_HIGH_FLOW_VENT_OUT = "gse_doc_17"  # Ox high vent
OX_PRE_VALVE_IN = "gse_doa_21"  # Ox pre-valve
OX_PRE_VALVE_OUT = "gse_doc_21"  # Ox pre-valve
OX_DOME_ISO_IN = "gse_doa_5"  # Ox dome reg pilot ISO
OX_DOME_ISO_OUT = "gse_doc_5"  # Ox dome reg pilot ISO
OX_DRAIN_IN = "gse_doa_14"
OX_DRAIN_OUT = "gse_doc_14"


vent_command_channels = [FUEL_VENT_OUT, PRESS_VENT_OUT, OX_LOW_VENT_OUT, 
                         OX_HIGH_FLOW_VENT_OUT, ENGINE_PNEUMATICS_VENT_OUT]

vent_acknowledgement_channels = [FUEL_VENT_IN, PRESS_VENT_IN, OX_LOW_VENT_IN, 
                         OX_HIGH_FLOW_VENT_IN, ENGINE_PNEUMATICS_VENT_IN]

command_channels = [FUEL_VENT_OUT, FUEL_PREVALVE_OUT, FUEL_FEEDLINE_PURGE_OUT,
                    OX_FILL_PURGE_OUT, FUEL_PRE_PRESS_OUT, OX_PRE_PRESS_OUT, OX_FEEDLINE_PURGE_OUT,
                    ENGINE_PNEUMATICS_ISO_OUT, ENGINE_PNEUMATICS_VENT_OUT,
                    AIR_DRIVE_ISO_1_OUT, AIR_DRIVE_ISO_2_OUT, GAS_BOOSTER_FILL_OUT, PRESS_FILL_OUT,
                    PRESS_VENT_OUT, FUEL_PRESS_ISO_OUT, OX_PRESS_OUT, OX_LOW_VENT_OUT, OX_FILL_VALVE_OUT,
                    OX_HIGH_FLOW_VENT_OUT, OX_PRE_VALVE_OUT, OX_DOME_ISO_OUT]

ack_channels = [FUEL_VENT_IN, FUEL_PREVALVE_IN, FUEL_FEEDLINE_PURGE_IN,
                OX_FILL_PURGE_IN, FUEL_PRE_PRESS_IN, OX_PRE_PRESS_IN, OX_FEEDLINE_PURGE_IN,
                ENGINE_PNEUMATICS_ISO_IN, ENGINE_PNEUMATICS_VENT_IN,
                AIR_DRIVE_ISO_1_IN, AIR_DRIVE_ISO_2_IN, GAS_BOOSTER_FILL_IN, PRESS_FILL_IN,
                PRESS_VENT_IN, FUEL_PRESS_ISO_IN, OX_PRESS_IN, OX_LOW_VENT_IN, OX_FILL_VALVE_IN,
                OX_HIGH_FLOW_VENT_IN, OX_PRE_VALVE_IN, OX_DOME_ISO_IN]

# Pressure sensors
OX_PRE_FILL_PT = "gse_ai_1"  # Ox pre-fill pressure
OX_PRESS_DOME_PILOT_REG_PT = "gse_ai_2"  # Ox press dome pilot reg pressure
FUEL_PT_1_PRESSURE = "gse_ai_3"  # Fuel tank 1 pressure
FUEL_PT_2_PRESSURE = "gse_ai_4"  # Fuel tank 2 pressure
OX_PRESS_PT = "gse_ai_5"  # Ox press pressure
OX_TANK_1_PRESSURE = "gse_ai_6"  # Ox tank 1 pressure
OX_TANK_2_PRESSURE = "gse_ai_7"  # Ox tank 2 pressure
OX_TANK_3_PRESSURE = "gse_ai_8"  # Ox tank 3 pressure
OX_FLOWMETER_INLET_PT = "gse_ai_9"  # Ox flowmeter throat pressure
OX_FLOWMETER_THROAT_PT = "gse_ai_10"  # Ox flowmeter inlet pressure
OX_LEVEL_SENSOR = "gse_ai_11"  # Ox level sensor
FUEL_FLOWMETER_INLET_PT = "gse_ai_12"  # Fuel flowmeter inlet pressure
FUEL_FLOWMETER_THROAT_PT = "gse_ai_13"  # Fuel flowmeter throat pressure
FUEL_LEVEL_SENSOR = "gse_ai_14"  # Fuel level sensor
TRICKLE_PURGE_POST_REG_PT = "gse_ai_15"  # Trickle purge post reg pressure
TRICKLE_PURGE_PRE_2K_PT = "gse_ai_16"  # Trickle purge pre reg pressure
AIR_DRIVE_2K_PT = "gse_ai_20"  # Air drive 2k pressure
AIR_DRIVE_POST_REG_PT = "gse_ai_21"  # Air drive post reg pressure
PRESS_TANK_SUPPLY = "gse_ai_23"  # Press tank pressure
GAS_BOOSTER_OUTLET_PT = "gse_ai_25"  # Gas booster outlet pressure
PRESS_TANK_2K_BOTTLE_PRE_FILL_PT = "gse_ai_27"  # Press tank 2k bottle pre-fill pressure
PNEUMATICS_BOTTLE_PT = "gse_ai_30"  # Pneumatics bottle pressure
TRAILER_PNEMATICS_PT = "gse_ai_31"  # Trailer pneumatics pressure
ENGINE_PNEUMATICS_PT = "gse_ai_33"  # Engine pneumatics pressure
PURGE_2K_BOTTLE_PT = "gse_ai_34"  # Purge 2k bottle pressure
PURGE_POST_REG_PT = "gse_ai_36"  # Purge post reg pressure
FUEL_PT_3_PRESSURE = "gse_ai_35"  # Fuel tank 3 pressure
PRESS_TANK_PT_1 = "gse_ai_26"  # Press tank pressure
PRESS_TANK_PT_2 = "gse_ai_24"  # Press tank pressure
PRESS_TANK_PT_3 = "gse_ai_22"  # Press tank pressure

PTs = [OX_PRE_FILL_PT, OX_PRESS_DOME_PILOT_REG_PT, FUEL_PT_1_PRESSURE, FUEL_PT_2_PRESSURE, FUEL_PT_3_PRESSURE, OX_PRESS_PT,
       OX_TANK_1_PRESSURE, OX_TANK_2_PRESSURE, OX_TANK_3_PRESSURE, OX_FLOWMETER_INLET_PT, OX_FLOWMETER_THROAT_PT,
       OX_LEVEL_SENSOR, FUEL_FLOWMETER_INLET_PT, FUEL_FLOWMETER_THROAT_PT, FUEL_LEVEL_SENSOR, TRICKLE_PURGE_POST_REG_PT,
       TRICKLE_PURGE_PRE_2K_PT, AIR_DRIVE_2K_PT, AIR_DRIVE_POST_REG_PT, PRESS_TANK_SUPPLY,
       GAS_BOOSTER_OUTLET_PT, PRESS_TANK_PT_1, PRESS_TANK_PT_2, PRESS_TANK_PT_3, PRESS_TANK_2K_BOTTLE_PRE_FILL_PT,
       PNEUMATICS_BOTTLE_PT, TRAILER_PNEMATICS_PT, ENGINE_PNEUMATICS_PT, PURGE_2K_BOTTLE_PT, PURGE_POST_REG_PT]

# Parameters for testing
INITIAL_FUEL_TANK_PRESSURE = 0
INITIAL_OX_TANK_PRESSURE = 0
INITIAL_PRESS_TANK_PRESSURE = 0
INITIAL_2K_PRESSURE = 2000

daq_time = client.channels.create(
    name=DAQ_TIME,
    data_type=sy.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

for i in range(1, 30):
    idx = client.channels.create(
        name=f"gse_doc_{i}_cmd_time",
        data_type=sy.DataType.TIMESTAMP,
        is_index=True,
        retrieve_if_name_exists=True
    )
    # creates valve channels
    client.channels.create(
        [
            sy.Channel(
                name=f"gse_doc_{i}",
                data_type=sy.DataType.UINT8,
                index=idx.key
            ),
            sy.Channel(
                name=f"gse_doa_{i}",
                data_type=sy.DataType.UINT8,
                index=daq_time.key
            ),
        ],
        retrieve_if_name_exists=True,
    )

for pt in PTs:
    client.channels.create(
        name=pt,
        data_type=sy.DataType.FLOAT32,
        index=daq_time.key,
        retrieve_if_name_exists=True
    )

rate = (sy.Rate.HZ * 50).period.seconds

# Create DAQ_STATE dictionary
DAQ_STATE = {}

# starts with valves open
for cmd_chan in command_channels:
    DAQ_STATE[cmd_chan] = 0  # open

# starts with vents closed
for cmd_chan in vent_command_channels:
    DAQ_STATE[cmd_chan] = 1  # closed

# starts with PTs at 0
for pt in PTs:
    DAQ_STATE[pt] = 0

# updates pressure sensors
DAQ_STATE.update({
    FUEL_PT_1_PRESSURE: INITIAL_FUEL_TANK_PRESSURE,
    FUEL_PT_2_PRESSURE: INITIAL_FUEL_TANK_PRESSURE,
    FUEL_PT_3_PRESSURE: INITIAL_FUEL_TANK_PRESSURE,
    PRESS_TANK_PT_1: INITIAL_PRESS_TANK_PRESSURE,
    PRESS_TANK_PT_2: INITIAL_PRESS_TANK_PRESSURE,
    PRESS_TANK_PT_3: INITIAL_PRESS_TANK_PRESSURE,
    OX_TANK_1_PRESSURE: 0,
    OX_TANK_2_PRESSURE: 0,
    OX_TANK_3_PRESSURE: 0
})

true_fuel_pressure = INITIAL_FUEL_TANK_PRESSURE
fuel_PT_1_pressure = true_fuel_pressure + random.uniform(-20, 20)
fuel_PT_2_pressure = true_fuel_pressure + random.uniform(-20, 20)
fuel_PT_3_pressure = true_fuel_pressure + random.uniform(-20, 20)

true_ox_pressure = INITIAL_OX_TANK_PRESSURE
ox_tank_1_pressure = true_ox_pressure + random.uniform(-20, 20)
ox_tank_2_pressure = true_ox_pressure + random.uniform(-20, 20)
ox_tank_3_pressure = true_ox_pressure + random.uniform(-20, 20)

true_press_pressure = INITIAL_PRESS_TANK_PRESSURE
press_tank_PT_1 = true_press_pressure + random.uniform(-20, 20)
press_tank_PT_2 = true_press_pressure + random.uniform(-20, 20)
press_tank_PT_3 = true_press_pressure + random.uniform(-20, 20)


# fuel_flowmeter_inlet_pressure = 0
# fuel_flowmeter_throat_pressure = 0
# fuel_level_sensor = 0

# ox_pre_fill_pressure = 0
# ox_dome_reg_pilot_pressure = 0
# ox_press_pressure = 0
# ox_flowmeter_inlet_pressure = 0
# ox_flowmeter_throat_pressure = 0
# ox_level_sensor = 0

supply_2k = INITIAL_2K_PRESSURE
# air_drive_2k_pressure = 0
# air_drive_post_reg_pressure = 0
# press_tank_2k_pressure = 0
# press_tank_bottle_pre_fill_pressure = 0

# trickle_purge_post_reg_pressure = 0
# trickle_purge_pre_2k_pressure = 0
# gas_booster_outlet_pressure = 0
# pneumatics_bottle_pt = 0
# engine_pneumatics_pressure = 0
# purge_2k_bottle_pressure = 0
# purge_post_reg_pressure = 0
# trailer_pneumatics_pressure = 0

FUEL_PREVALVE_LAST_OPEN = None

with client.new_streamer(command_channels) as streamer:
    READ_CHANNELS = command_channels
    WRITE_CHANNELS = ack_channels + PTs + [DAQ_TIME]  # + TCs
    print(f"writing to {len(WRITE_CHANNELS)} channels")
    with client.new_writer(
            sy.TimeStamp.now(),
            channels = WRITE_CHANNELS
    ) as w:
        i = 0
        while True:
            try:
                time.sleep(rate)
                if streamer.received:
                    while streamer.received:
                        f = streamer.read()
                        for k in f.columns:
                            DAQ_STATE[k] = f[k][0]

                fuel_vent_energized = DAQ_STATE[FUEL_VENT_OUT] == 1
                fuel_prevalve_energized = DAQ_STATE[FUEL_PREVALVE_OUT] == 1
                fuel_feedline_purge_energized = DAQ_STATE[FUEL_FEEDLINE_PURGE_OUT] == 1
                fuel_press_iso_energized = DAQ_STATE[FUEL_PRESS_ISO_OUT] == 1
                fuel_pre_press_energized = DAQ_STATE[FUEL_PRE_PRESS_OUT] == 1

                ox_pre_press_energized = DAQ_STATE[OX_PRE_PRESS_OUT] == 1
                ox_press_energized = DAQ_STATE[OX_PRESS_OUT] == 1
                ox_low_vent_energized = DAQ_STATE[OX_LOW_VENT_OUT] ==1
                ox_fill_valve_energized = DAQ_STATE[OX_FILL_VALVE_OUT] == 1
                ox_high_flow_vent_energized = DAQ_STATE[OX_HIGH_FLOW_VENT_OUT] == 1
                ox_pre_valve_energized = DAQ_STATE[OX_PRE_VALVE_OUT] == 1
                ox_pre_fill_energized = DAQ_STATE[OX_PRE_FILL_PT] == 1
                ox_dome_iso_energized = DAQ_STATE[OX_DOME_ISO_OUT] == 1

                air_drive_iso_1_energized = DAQ_STATE[AIR_DRIVE_ISO_1_OUT] == 1
                air_drive_iso_2_energized= DAQ_STATE[AIR_DRIVE_ISO_2_OUT] == 1
                gas_booster_fill_energized = DAQ_STATE[GAS_BOOSTER_FILL_OUT] == 1

                press_fill_energized = DAQ_STATE[PRESS_FILL_OUT] == 1
                press_vent_energized= DAQ_STATE[PRESS_VENT_OUT] == 1

                fuel_tank_delta = 0
                trailer_pneumatics_delta = 0
                press_tank_delta = 0
                ox_tank_delta = 0

                ### PRESS ###
                if press_fill_energized:
                    if supply_2k > true_press_pressure:
                        true_press_pressure += 2.5
                        supply_2k -= 1
                    if gas_booster_fill_energized:
                        if air_drive_iso_1_energized and air_drive_iso_2_energized:
                            supply_2k -= 1
                            true_press_pressure += 1.5

                if press_vent_energized:
                    press_tank_delta -= 4

                ### FUEL ###
                if fuel_prevalve_energized and FUEL_PREVALVE_LAST_OPEN is None:
                    FUEL_PREVALVE_LAST_OPEN = sy.TimeStamp.now()
                elif not fuel_prevalve_energized:
                    FUEL_PREVALVE_LAST_OPEN = None
            
                if fuel_pre_press_energized:
                    fuel_tank_delta += 3.0

                if fuel_press_iso_energized:
                    fuel_tank_delta += 1.5
                
                if fuel_prevalve_energized:
                    fuel_tank_delta -= 0.1 * sy.TimeSpan(sy.TimeStamp.now() - FUEL_PREVALVE_LAST_OPEN).seconds

                if not fuel_vent_energized:
                    fuel_tank_delta -= 3


                ### OX ###
                if ox_pre_valve_energized and OX_PREVALVE_LAST_OPEN is None:
                    OX_PREVALVE_LAST_OPEN = sy.TimeStamp.now()
                elif not ox_pre_valve_energized:
                    OX_PREVALVE_LAST_OPEN = None

                if ox_pre_press_energized:
                    ox_tank_delta += 3

                if ox_press_energized:
                    ox_tank_delta += 1.5

                if ox_pre_valve_energized:
                    ox_tank_delta += 0.1 * sy.TimeSpan(sy.TimeStamp.now() - OX_PREVALVE_LAST_OPEN).seconds

                if not ox_low_vent_energized:
                    ox_tank_delta -= 2.0

                if not ox_high_flow_vent_energized:
                    ox_tank_delta -= 5.0

                ox_tank_1_pressure += ox_tank_delta
                ox_tank_2_pressure += ox_tank_delta
                ox_tank_3_pressure += ox_tank_delta
                fuel_PT_1_pressure += fuel_tank_delta 
                fuel_PT_2_pressure += fuel_tank_delta 
                fuel_PT_3_pressure += fuel_tank_delta 
                press_tank_PT_1 += press_tank_delta
                press_tank_PT_2 += press_tank_delta
                press_tank_PT_3 += press_tank_delta

                # no negative pressures pls ;-;
                ox_tank_1_pressure = max(0, ox_tank_1_pressure)
                ox_tank_2_pressure = max(0, ox_tank_2_pressure)
                ox_tank_3_pressure = max(0, ox_tank_3_pressure)
                fuel_PT_1_pressure = max(0, fuel_PT_1_pressure)
                fuel_PT_2_pressure = max(0, fuel_PT_2_pressure)
                fuel_PT_3_pressure = max(0, fuel_PT_3_pressure)
                press_tank_PT_1 = max(0, press_tank_PT_1)
                press_tank_PT_2 = max(0, press_tank_PT_2)
                press_tank_PT_3 = max(0, press_tank_PT_3)

                now = sy.TimeStamp.now()

                ok = w.write({
                    DAQ_TIME: now,

                    # writes to 21 valves
                    FUEL_VENT_IN: int(fuel_vent_energized),
                    FUEL_PREVALVE_IN: int(fuel_prevalve_energized),
                    FUEL_FEEDLINE_PURGE_IN: int(fuel_feedline_purge_energized),
                    OX_FILL_PURGE_IN: 0,
                    FUEL_PRE_PRESS_IN: int(fuel_pre_press_energized),
                    OX_PRE_PRESS_IN: int(ox_pre_press_energized),
                    OX_FEEDLINE_PURGE_IN: 0,
                    ENGINE_PNEUMATICS_ISO_IN: 0,
                    ENGINE_PNEUMATICS_VENT_IN: 0,
                    AIR_DRIVE_ISO_1_IN: int(air_drive_iso_1_energized),
                    AIR_DRIVE_ISO_2_IN: int(air_drive_iso_2_energized),
                    GAS_BOOSTER_FILL_IN: int(gas_booster_fill_energized),
                    PRESS_FILL_IN: int(press_fill_energized),
                    PRESS_VENT_IN: int(press_vent_energized),
                    FUEL_PRESS_ISO_IN: int(fuel_press_iso_energized),
                    OX_PRESS_IN: int(ox_press_energized),
                    OX_LOW_VENT_IN: int(ox_low_vent_energized),
                    OX_FILL_VALVE_IN: int(ox_fill_valve_energized),
                    OX_HIGH_FLOW_VENT_IN: int(ox_high_flow_vent_energized),
                    OX_PRE_VALVE_IN: int(ox_pre_valve_energized),
                    OX_DOME_ISO_IN: ox_dome_iso_energized,

                    # writes to all 30 PTs
                    FUEL_PT_1_PRESSURE: true_fuel_pressure + random.uniform(-20, 20),
                    FUEL_PT_2_PRESSURE: true_fuel_pressure + random.uniform(-20, 20),
                    FUEL_PT_3_PRESSURE: true_fuel_pressure + random.uniform(-20, 20),
                    OX_TANK_1_PRESSURE: true_ox_pressure + random.uniform(-20,20),
                    OX_TANK_2_PRESSURE: true_ox_pressure + random.uniform(-20,20),
                    OX_TANK_3_PRESSURE: true_ox_pressure + random.uniform(-20,20),
                    PRESS_TANK_PT_1: true_press_pressure + random.uniform(-20, 20),
                    PRESS_TANK_PT_2: true_press_pressure + random.uniform(-20, 20),
                    PRESS_TANK_PT_3: true_press_pressure + random.uniform(-20, 20),
                    OX_PRE_FILL_PT: 0,
                    OX_PRESS_DOME_PILOT_REG_PT: 0,
                    OX_PRESS_PT: 0,
                    OX_FLOWMETER_INLET_PT: 0,
                    OX_FLOWMETER_THROAT_PT: 0,
                    OX_LEVEL_SENSOR: 0,
                    FUEL_FLOWMETER_INLET_PT: 0,
                    FUEL_FLOWMETER_THROAT_PT: 0,
                    FUEL_LEVEL_SENSOR: 0,
                    TRICKLE_PURGE_POST_REG_PT: 0,
                    TRICKLE_PURGE_PRE_2K_PT: 0,
                    AIR_DRIVE_2K_PT: 0,
                    AIR_DRIVE_POST_REG_PT: 0,
                    PRESS_TANK_SUPPLY: supply_2k + random.uniform(-20, 20),
                    GAS_BOOSTER_OUTLET_PT: 0,
                    PRESS_TANK_2K_BOTTLE_PRE_FILL_PT: 0,
                    PNEUMATICS_BOTTLE_PT: 0,
                    TRAILER_PNEMATICS_PT: 0,
                    ENGINE_PNEUMATICS_PT: 0,
                    PURGE_2K_BOTTLE_PT: 0,
                    PURGE_POST_REG_PT: 0,
                })

                i += 1
                if (i % 40) == 0:
                    print(f"Committing {i} samples")
                    ok = w.commit()
                    print(ok)

            except Exception as e:
                print(e)
                raise e