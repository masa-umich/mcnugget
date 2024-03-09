import time
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
# FUEL_MPV_IN = "gse_doa_25"  # Fuel MPV input (ghost channel for now)
# FUEL_MPV_OUT = "gse_doc_25"  # Fuel MPV output

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
# OX_MPV_IN = "gse_doa_26"  # Ox MPV
# OX_MPV_OUT = "gse_doc_26"  # Ox MPV
OX_PRE_VALVE_IN = "gse_doa_21"  # Ox pre-valve
OX_PRE_VALVE_OUT = "gse_doc_21"  # Ox pre-valve

command_channels = [FUEL_VENT_OUT, FUEL_PREVALVE_OUT, FUEL_FEEDLINE_PURGE_OUT,
                    OX_FILL_PURGE_OUT, FUEL_PRE_PRESS_OUT, OX_PRE_PRESS_OUT, OX_FEEDLINE_PURGE_OUT,
                    ENGINE_PNEUMATICS_ISO_OUT, ENGINE_PNEUMATICS_VENT_OUT,
                    AIR_DRIVE_ISO_1_OUT, AIR_DRIVE_ISO_2_OUT, GAS_BOOSTER_FILL_OUT, PRESS_FILL_OUT,
                    PRESS_VENT_OUT, FUEL_PRESS_ISO_OUT, OX_PRESS_OUT, OX_LOW_VENT_OUT, OX_FILL_VALVE_OUT,
                    OX_HIGH_FLOW_VENT_OUT, OX_PRE_VALVE_OUT]
ack_channels = [FUEL_VENT_IN, FUEL_PREVALVE_IN, FUEL_FEEDLINE_PURGE_IN,
                OX_FILL_PURGE_IN, FUEL_PRE_PRESS_IN, OX_PRE_PRESS_IN, OX_FEEDLINE_PURGE_IN,
                ENGINE_PNEUMATICS_ISO_IN, ENGINE_PNEUMATICS_VENT_IN,
                AIR_DRIVE_ISO_1_IN, AIR_DRIVE_ISO_2_IN, GAS_BOOSTER_FILL_IN, PRESS_FILL_IN,
                PRESS_VENT_IN, FUEL_PRESS_ISO_IN, OX_PRESS_IN, OX_LOW_VENT_IN, OX_FILL_VALVE_IN,
                OX_HIGH_FLOW_VENT_IN, OX_PRE_VALVE_IN]

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

PRESS_TANK_TC_1 = "gse_tc_5"
PRESS_TANK_TC_2 = "gse_tc_6"
PRESS_TANK_TC_3 = "gse_tc_7"
PRESS_TANK_TC_4 = "gse_tc_8"

PTs = [OX_PRE_FILL_PT, OX_PRESS_DOME_PILOT_REG_PT, FUEL_PT_1_PRESSURE, FUEL_PT_2_PRESSURE, FUEL_PT_3_PRESSURE, OX_PRESS_PT,
       OX_TANK_1_PRESSURE, OX_TANK_2_PRESSURE, OX_TANK_3_PRESSURE, OX_FLOWMETER_INLET_PT, OX_FLOWMETER_THROAT_PT,
       OX_LEVEL_SENSOR, FUEL_FLOWMETER_INLET_PT, FUEL_FLOWMETER_THROAT_PT, FUEL_LEVEL_SENSOR, TRICKLE_PURGE_POST_REG_PT,
       TRICKLE_PURGE_PRE_2K_PT, AIR_DRIVE_2K_PT, AIR_DRIVE_POST_REG_PT, PRESS_TANK_SUPPLY,
       GAS_BOOSTER_OUTLET_PT, PRESS_TANK_PT_1, PRESS_TANK_PT_2, PRESS_TANK_PT_3, PRESS_TANK_2K_BOTTLE_PRE_FILL_PT,
       PNEUMATICS_BOTTLE_PT, TRAILER_PNEMATICS_PT, ENGINE_PNEUMATICS_PT, PURGE_2K_BOTTLE_PT, PURGE_POST_REG_PT]

TCs = [PRESS_TANK_TC_1, PRESS_TANK_TC_2, PRESS_TANK_TC_3, PRESS_TANK_TC_4]

daq_time = client.channels.create(
    name=DAQ_TIME,
    data_type=sy.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

for i in range(1, 27):
    idx = client.channels.create(
        name=f"gse_doc_{i}_cmd_time",
        data_type=sy.DataType.TIMESTAMP,
        is_index=True,
        retrieve_if_name_exists=True
    )
    #creates valve channels
    client.channels.create(
        [
            sy.Channel(
                name=f"gse_doc_{i}",
                data_type=sy.DataType.UINT8,
                index=idx.key
            ),
            sy.Channel(
                name=f"gse_doa_{i}",
                data_type=sy.DataType.FLOAT32,
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

for tc in TCs:
    client.channels.create(
        name=tc,
        data_type=sy.DataType.FLOAT32,
        index=daq_time.key,
        retrieve_if_name_exists=True
    )

rate = (sy.Rate.HZ * 50).period.seconds

# Assuming `command_channels` is already defined
# Rest of the code remains the same as before...

# Create DAQ_STATE dictionary
DAQ_STATE = {}

# Set values for all channels
for cmd_chan in command_channels:
    DAQ_STATE[cmd_chan] = 0 #de-energized

for pt in PTs:
    DAQ_STATE[pt]= 0 #start with no pressure

#Set values for pressure sensors
DAQ_STATE.update({
    FUEL_PT_1_PRESSURE: 0,
    FUEL_PT_2_PRESSURE: 0,
    FUEL_PT_3_PRESSURE: 0,
    PRESS_TANK_PT_1: 0,
    PRESS_TANK_PT_2: 0,
    PRESS_TANK_PT_3: 0,
    OX_TANK_1_PRESSURE: 0,
    OX_TANK_2_PRESSURE: 0,
    OX_TANK_3_PRESSURE: 0
})
ox_pre_fill_pressure = 0
ox_dome_reg_pilot_pressure = 0
fuel_PT_1_pressure = 0
fuel_PT_2_pressure = 0
ox_press_pressure = 0
ox_tank_1_pressure = 0
ox_tank_2_pressure = 0
ox_tank_3_pressure = 0
ox_flowmeter_inlet_pressure = 0
ox_flowmeter_throat_pressure = 0
ox_level_sensor = 0
fuel_flowmeter_inlet_pressure = 0
fuel_flowmeter_throat_pressure = 0
fuel_level_sensor = 0
trickle_purge_post_reg_pressure = 0
trickle_purge_pre_2k_pressure = 0
air_drive_2k_pressure = 0
air_drive_post_reg_pressure = 0
press_tank_2k_pressure = 0
gas_booster_outlet_pressure = 0
press_tank_PT_1 = 0
press_tank_bottle_pre_fill_pressure = 0
pneumatics_bottle_pt = 0
engine_pneumatics_pressure = 0
purge_2k_bottle_pressure = 0
fuel_PT_3_pressure = 0
purge_post_reg_pressure = 0
trailer_pneumatics_pressure = 0
press_tank_PT_2 = 0
press_tank_PT_3 = 0

with client.new_streamer(command_channels) as streamer:
    with client.new_writer(
            sy.TimeStamp.now(),
            channels=ack_channels+PTs+[DAQ_TIME]
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

                fuel_vent_open = DAQ_STATE[FUEL_VENT_OUT] == 1
                fuel_prevalve_open = DAQ_STATE[FUEL_PREVALVE_OUT] == 1
                # fuel_mpv_open = DAQ_STATE[FUEL_MPV_OUT] == 1
                fuel_feedline_purge_open = DAQ_STATE[FUEL_FEEDLINE_PURGE_OUT] == 1
                ox_fill_purge_open = DAQ_STATE[OX_FILL_PURGE_OUT] == 1
                fuel_pre_press_open = DAQ_STATE[FUEL_PRE_PRESS_OUT] == 1
                ox_pre_press_open = DAQ_STATE[OX_PRE_PRESS_OUT] == 1
                ox_feedline_purge_open = DAQ_STATE[OX_FEEDLINE_PURGE_OUT] == 1
                engine_pneumatics_iso_open = DAQ_STATE[ENGINE_PNEUMATICS_ISO_OUT] == 1
                engine_pneumatics_vent_open = DAQ_STATE[ENGINE_PNEUMATICS_VENT_OUT] == 1
                air_drive_iso_1_open = DAQ_STATE[AIR_DRIVE_ISO_1_OUT] == 1
                air_drive_iso_2_open = DAQ_STATE[AIR_DRIVE_ISO_2_OUT] == 1
                gas_booster_fill_open = DAQ_STATE[GAS_BOOSTER_FILL_OUT] == 1
                press_fill_open = DAQ_STATE[PRESS_FILL_OUT] == 1
                press_vent_open = DAQ_STATE[PRESS_VENT_OUT] == 1
                fuel_press_iso_open = DAQ_STATE[FUEL_PRESS_ISO_OUT] == 1
                ox_press_open = DAQ_STATE[OX_PRESS_OUT] == 1
                ox_low_vent_open = DAQ_STATE[OX_LOW_VENT_OUT] == 1
                ox_fill_valve_open = DAQ_STATE[OX_FILL_VALVE_OUT] == 1
                ox_high_flow_vent_open = DAQ_STATE[OX_HIGH_FLOW_VENT_OUT] == 1
                # ox_mpv_open = DAQ_STATE[OX_MPV_OUT] == 1
                ox_pre_valve_open = DAQ_STATE[OX_PRE_VALVE_OUT] == 1
                ox_pre_fill_open = DAQ_STATE[OX_PRE_FILL_PT] ==1

                fuel_tank_delta = 0
                trailer_pneumatics_delta = 0
                press_tank_delta = 0
                ox_tank_delta = 0

                if fuel_prevalve_open:
                    fuel_tank_delta -= 1.5

                if ox_pre_valve_open:
                    ox_tank_delta -= 1.5

                if ox_press_open and not ox_low_vent_open:
                    ox_tank_delta = 0

                if fuel_press_iso_open and not fuel_vent_open:
                    fuel_tank_delta = 0

                if engine_pneumatics_iso_open and not engine_pneumatics_vent_open:
                    trailer_pneumatics_delta = 0

                if fuel_vent_open:
                    fuel_tank_delta -= 4

                if ox_low_vent_open:
                    ox_tank_delta -= 2.0

                if ox_high_flow_vent_open:
                    ox_tank_delta -= 3.0

                if engine_pneumatics_vent_open:
                    trailer_pneumatics_delta -= 1.5

                if press_fill_open:
                    if (gas_booster_fill_open and 
                    (air_drive_iso_1_open or air_drive_iso_2_open)):
                        press_tank_delta += 3.5
                    else:
                        press_tank_delta += 2.5

                if press_vent_open:
                    press_tank_delta -= 4


                ox_tank_1_pressure += ox_tank_delta
                ox_tank_2_pressure += ox_tank_delta
                ox_tank_3_pressure += ox_tank_delta
                fuel_PT_1_pressure += fuel_tank_delta
                fuel_PT_2_pressure += fuel_tank_delta
                fuel_PT_3_pressure += fuel_tank_delta
                trailer_pneumatics_pressure += trailer_pneumatics_delta
                press_tank_PT_1 += press_tank_delta
                press_tank_PT_2 += press_tank_delta
                press_tank_PT_3 += press_tank_delta

                # no negative pressures pls ;-;
                if ox_tank_1_pressure <= 0:
                    ox_tank_1_pressure = 0

                if ox_tank_2_pressure <= 0:
                    ox_tank_2_pressure = 0

                if ox_tank_3_pressure <= 0:
                    ox_tank_3_pressure = 0

                if fuel_PT_1_pressure <= 0:
                    fuel_PT_1_pressure = 0

                if fuel_PT_2_pressure <= 0:
                    fuel_PT_2_pressure = 0

                if fuel_PT_3_pressure <= 0:
                    fuel_PT_3_pressure = 0

                if trailer_pneumatics_pressure <= 0:
                    trailer_pneumatics_pressure = 0

                if press_tank_PT_1 <= 0:
                    press_tank_PT_1 = 0

                if press_tank_PT_2 <= 0:
                    press_tank_PT_2 = 0

                if press_tank_PT_3 <= 0:
                    press_tank_PT_3 = 0

                now = sy.TimeStamp.now()

                ok = w.write({
                    DAQ_TIME: now,
                    FUEL_VENT_IN: int(fuel_vent_open),
                    FUEL_PREVALVE_IN: int(fuel_prevalve_open),
                    FUEL_FEEDLINE_PURGE_IN: int(fuel_feedline_purge_open),
                    OX_FILL_PURGE_IN: int(ox_fill_purge_open),
                    FUEL_PRE_PRESS_IN: int(fuel_pre_press_open),
                    OX_PRE_PRESS_IN: int(ox_pre_press_open),
                    OX_FEEDLINE_PURGE_IN: int(ox_feedline_purge_open),
                    ENGINE_PNEUMATICS_ISO_IN: int(engine_pneumatics_iso_open),
                    ENGINE_PNEUMATICS_VENT_IN: int(engine_pneumatics_vent_open),
                    AIR_DRIVE_ISO_1_IN: int(air_drive_iso_1_open),
                    AIR_DRIVE_ISO_2_IN: int(air_drive_iso_2_open),
                    GAS_BOOSTER_FILL_IN: int(gas_booster_fill_open),
                    PRESS_FILL_IN: int(press_fill_open),
                    PRESS_VENT_IN: int(press_vent_open),
                    FUEL_PRESS_ISO_IN: int(fuel_press_iso_open),
                    OX_PRESS_IN: int(ox_press_open),
                    OX_LOW_VENT_IN: int(ox_low_vent_open),
                    OX_FILL_VALVE_IN: int(ox_fill_valve_open),
                    OX_HIGH_FLOW_VENT_IN: int(ox_high_flow_vent_open),
                    OX_PRE_VALVE_IN: int(ox_pre_valve_open),
                    OX_PRE_FILL_PT: ox_pre_fill_pressure,
                    OX_PRESS_DOME_PILOT_REG_PT: ox_dome_reg_pilot_pressure,
                    FUEL_PT_1_PRESSURE: fuel_PT_1_pressure,
                    FUEL_PT_2_PRESSURE: fuel_PT_2_pressure,
                    FUEL_PT_3_PRESSURE: fuel_PT_3_pressure,
                    OX_TANK_1_PRESSURE: ox_tank_1_pressure,
                    OX_TANK_2_PRESSURE: ox_tank_2_pressure,
                    OX_TANK_3_PRESSURE: ox_tank_3_pressure,
                    OX_PRESS_PT: ox_press_pressure,
                    OX_FLOWMETER_INLET_PT: ox_flowmeter_inlet_pressure,
                    OX_FLOWMETER_THROAT_PT: ox_flowmeter_throat_pressure,
                    OX_LEVEL_SENSOR: ox_level_sensor,
                    FUEL_FLOWMETER_INLET_PT: fuel_flowmeter_inlet_pressure,
                    FUEL_FLOWMETER_THROAT_PT: fuel_flowmeter_throat_pressure,
                    FUEL_LEVEL_SENSOR: fuel_level_sensor,
                    TRICKLE_PURGE_POST_REG_PT: trickle_purge_post_reg_pressure,
                    TRICKLE_PURGE_PRE_2K_PT: trickle_purge_pre_2k_pressure,
                    AIR_DRIVE_2K_PT: air_drive_2k_pressure,
                    AIR_DRIVE_POST_REG_PT: air_drive_post_reg_pressure,
                    PRESS_TANK_SUPPLY: press_tank_2k_pressure,
                    GAS_BOOSTER_OUTLET_PT: gas_booster_outlet_pressure,
                    PRESS_TANK_PT_1: press_tank_PT_1,
                    PRESS_TANK_2K_BOTTLE_PRE_FILL_PT: press_tank_bottle_pre_fill_pressure,
                    PNEUMATICS_BOTTLE_PT: pneumatics_bottle_pt,
                    TRAILER_PNEMATICS_PT: trailer_pneumatics_pressure,
                    ENGINE_PNEUMATICS_PT: engine_pneumatics_pressure,
                    PURGE_2K_BOTTLE_PT: purge_2k_bottle_pressure,
                    PRESS_TANK_PT_2: press_tank_PT_2,
                    PRESS_TANK_PT_3: press_tank_PT_3
                })

                i += 1
                if (i % 40) == 0:
                    print(f"Committing {i} samples")
                    ok = w.commit()

            except Exception as e:
                print(e)
                raise e
