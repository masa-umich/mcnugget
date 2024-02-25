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
FUEL_VENT_IN = "gse_doa_1"  # Fuel vent input,
FUEL_VENT_OUT = "gse_doc_1"  # Fuel vent output
FUEL_PREVALVE_IN = "gse_doa_2"  # Fuel pre-valve input
FUEL_PREVALVE_OUT = "gse_doc_2"  # Fuel pre-valve output
FUEL_MPV_IN = "gse_doa_3"  # Fuel MPV input
FUEL_MPV_OUT = "gse_doc_3"  # Fuel MPV output

# valves for purge system
FUEL_FEEDLINE_PURGE_IN = "gse_doa_4"  # Fuel feedline purge
FUEL_FEEDLINE_PURGE_OUT = "gse_doc_4"  # Fuel feedline purge
OX_FILL_PURGE_IN = "gse_doa_5"  # Ox fill purge
OX_FILL_PURGE_OUT = "gse_doc_5"  # Ox fill purge
FUEL_PRE_PRESS_IN = "gse_doa_6"  # Fuel pre-press
FUEL_PRE_PRESS_OUT = "gse_doc_6"  # Fuel press press
OX_PRE_PRESS_IN = "gse_doa_7"  # Ox pre-press
OX_PRE_PRESS_OUT = "gse_doc_7"  # Ox press press
OX_FEEDLINE_PURGE_IN = "gse_doa_8"  # Ox feedline purge
OX_FEEDLINE_PURGE_OUT = "gse_doc_8"  # Ox feedline purge

# valves for pneumatics
ENGINE_PNEUMATICS_ISO_IN = "gse_doa_9"  # Engine pneumatics ISO
ENGINE_PNEUMATICS_ISO_OUT = "gse_doc_9"  # Engine pneumatics ISO
ENGINE_PNEUMATICS_VENT_IN = "gse_doa_10"  # Engine pneumatics vent
ENGINE_PNEUMATICS_VENT_OUT = "gse_doc_10"  # Engine pneumatics vent
SOLENOID_MANIFOLD_IN = "gse_doa_11"  # Solenoid manifold
SOLENOID_MANIFOLD_OUT = "gse_doc_11"  # Solenoid manifold

# valves for press system
AIR_DRIVE_ISO_1_IN = "gse_doa_12"  # Air drive ISO 1
AIR_DRIVE_ISO_1_OUT = "gse_doc_12"  # Air drive ISO 1
AIR_DRIVE_ISO_2_IN = "gse_doa_13"  # Air drive ISO 2
AIR_DRIVE_ISO_2_OUT = "gse_doc_13"  # Air drive ISO 2
GAS_BOOSTER_FILL_IN = "gse_doa_14"  # Gas booster fill
GAS_BOOSTER_FILL_OUT = "gse_doc_14"  # Gas booster fill
PRESS_FILL_IN = "gse_doa_15"  # Press fill
PRESS_FILL_OUT = "gse_doc_15"  # Press fill
PRESS_VENT_IN = "gse_doa_16"  # Press vent
PRESS_VENT_OUT = "gse_doc_16"  # Press vent
FUEL_PRESS_ISO_IN = "gse_doa_17"  # Fuel press ISO
FUEL_PRESS_ISO_OUT = "gse_doc_17"  # Fuel press ISO
OX_PRESS_IN = "gse_doa_18"  # Ox press
OX_PRESS_OUT = "gse_doc_18"  # Ox press

# Ox system pressure valves
OX_LOW_VENT_IN = "gse_doa_19"  # Ox low vent
OX_LOW_VENT_OUT = "gse_doc_19"  # Ox low vent
OX_FILL_VALVE_IN = "gse_doa_20"  # Ox fill valve
OX_FILL_VALVE_OUT = "gse_doc_20"  # Ox fill valve
OX_HIGH_FLOW_VENT_IN = "gse_doa_21"  # Ox high vent
OX_HIGH_FLOW_VENT_OUT = "gse_doc_21"  # Ox high vent
OX_MPV_IN = "gse_doa_22"  # Ox MPV
OX_MPV_OUT = "gse_doc_22"  # Ox MPV

command_channels = [FUEL_VENT_OUT, FUEL_PREVALVE_OUT, FUEL_MPV_OUT, FUEL_FEEDLINE_PURGE_OUT,
                    OX_FILL_PURGE_OUT, FUEL_PRE_PRESS_OUT, OX_PRE_PRESS_OUT, OX_FEEDLINE_PURGE_OUT,
                    ENGINE_PNEUMATICS_ISO_OUT, ENGINE_PNEUMATICS_VENT_OUT, SOLENOID_MANIFOLD_OUT,
                    AIR_DRIVE_ISO_1_OUT, AIR_DRIVE_ISO_2_OUT, GAS_BOOSTER_FILL_OUT, PRESS_FILL_OUT,
                    PRESS_VENT_OUT, FUEL_PRESS_ISO_OUT, OX_PRESS_OUT, OX_LOW_VENT_OUT, OX_FILL_VALVE_OUT,
                    OX_HIGH_FLOW_VENT_OUT, OX_MPV_OUT]


# Pressure sensors
FUEL_TANK_1_PRESSURE = "gse_ai_1"  # Fuel tank 1 pressure
FUEL_TANK_2_PRESSURE = "gse_ai_2"  # Fuel tank 2 pressure
TRAILER_PNEUMATICS_PRESSURE = "gse_ai_3"  # Trailer pneumatics pressure
PRESS_TANK_PRESSURE = "gse_ai_4"  # Press tank pressure
OX_TANK_1_PRESSURE = "gse_ai_5"  # Ox tank 1 pressure
OX_TANK_2_PRESSURE = "gse_ai_6"  # Ox tank 2 pressure
OX_TANK_3_PRESSURE = "gse_ai_7"  # Ox tank 3 pressure

daq_time = client.channels.create(
    name=DAQ_TIME,
    data_type=sy.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

for i in range(1, 26):
    idx = client.channels.create(
        name=f"gse_doc_{i}_cmd_time",
        data_type=sy.DataType.TIMESTAMP,
        is_index=True,
        retrieve_if_name_exists=True
    )

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
client.channels.create(
    name=OX_TANK_1_PRESSURE,
    data_type=sy.DataType.FLOAT32,
    index=daq_time.key,
    retrieve_if_name_exists=True
)

client.channels.create(
    name=OX_TANK_2_PRESSURE,
    data_type=sy.DataType.FLOAT32,
    index=daq_time.key,
    retrieve_if_name_exists=True
)

client.channels.create(
    name=OX_TANK_3_PRESSURE,
    data_type=sy.DataType.FLOAT32,
    index=daq_time.key,
    retrieve_if_name_exists=True
)

client.channels.create(
    name=FUEL_TANK_1_PRESSURE,
    data_type=sy.DataType.FLOAT32,
    index=daq_time.key,
    retrieve_if_name_exists=True
)

client.channels.create(
    name=FUEL_TANK_2_PRESSURE,
    data_type=sy.DataType.FLOAT32,
    index=daq_time.key,
    retrieve_if_name_exists=True
)

client.channels.create(
    name=TRAILER_PNEUMATICS_PRESSURE,
    data_type=sy.DataType.FLOAT32,
    index=daq_time.key,
    retrieve_if_name_exists=True
)

client.channels.create(
    name=PRESS_TANK_PRESSURE,
    data_type=sy.DataType.FLOAT32,
    index=daq_time.key,
    retrieve_if_name_exists=True
)

rate = (sy.Rate.HZ * 50).period.seconds

DAQ_STATE = {
    # Valves
    FUEL_VENT_OUT: 0,
    FUEL_PREVALVE_OUT: 0,
    FUEL_MPV_OUT: 0,
    FUEL_FEEDLINE_PURGE_OUT: 0,
    OX_FILL_PURGE_OUT: 0,
    FUEL_PRE_PRESS_OUT: 0,
    OX_PRE_PRESS_OUT: 0,
    OX_FEEDLINE_PURGE_OUT: 0,
    ENGINE_PNEUMATICS_ISO_OUT: 0,
    ENGINE_PNEUMATICS_VENT_OUT: 0,
    SOLENOID_MANIFOLD_OUT: 0,
    AIR_DRIVE_ISO_1_OUT: 0,
    AIR_DRIVE_ISO_2_OUT: 0,
    GAS_BOOSTER_FILL_OUT: 0,
    PRESS_FILL_OUT: 0,
    PRESS_VENT_OUT: 0,
    FUEL_PRESS_ISO_OUT: 0,
    OX_PRESS_OUT: 0,
    OX_LOW_VENT_OUT: 0,
    OX_FILL_VALVE_OUT: 0,
    OX_HIGH_FLOW_VENT_OUT: 0,
    OX_MPV_OUT: 0,

    # Pts
    FUEL_TANK_1_PRESSURE: 0,
    FUEL_TANK_2_PRESSURE: 0,
    TRAILER_PNEUMATICS_PRESSURE: 0,
    PRESS_TANK_PRESSURE: 0,
    OX_TANK_1_PRESSURE: 0,
    OX_TANK_2_PRESSURE: 0,
    OX_TANK_3_PRESSURE: 0,
}

OX_MPV_LAST_OPEN = None
FUEL_MPV_LAST_OPEN = None
fuel_tank_1_pressure = 0
fuel_tank_2_pressure = 0
trailer_pneumatics_pressure = 0
press_tank_pressure = 0
ox_tank_1_pressure = 0
ox_tank_2_pressure = 0
ox_tank_3_pressure = 0

with client.new_streamer(command_channels) as streamer:
    with client.new_writer(
            sy.TimeStamp.now(),
            channels=[DAQ_TIME,
                      FUEL_VENT_IN, 
                      FUEL_PREVALVE_IN, 
                      FUEL_MPV_IN, 
                      FUEL_FEEDLINE_PURGE_IN,
                      OX_FILL_PURGE_IN, 
                      FUEL_PRE_PRESS_IN, 
                      OX_PRE_PRESS_IN, 
                      OX_FEEDLINE_PURGE_IN,
                      ENGINE_PNEUMATICS_ISO_IN, 
                      ENGINE_PNEUMATICS_VENT_IN, 
                      SOLENOID_MANIFOLD_IN,
                      AIR_DRIVE_ISO_1_IN, 
                      AIR_DRIVE_ISO_2_IN, 
                      GAS_BOOSTER_FILL_IN, 
                      PRESS_FILL_IN,
                      PRESS_VENT_IN, 
                      FUEL_PRESS_ISO_IN, 
                      OX_PRESS_IN, 
                      OX_LOW_VENT_IN, 
                      OX_FILL_VALVE_IN,
                      OX_HIGH_FLOW_VENT_IN, 
                      OX_MPV_IN, 
                      FUEL_TANK_1_PRESSURE, 
                      FUEL_TANK_2_PRESSURE,
                      TRAILER_PNEUMATICS_PRESSURE, 
                      PRESS_TANK_PRESSURE,
                      OX_TANK_1_PRESSURE,
                      OX_TANK_2_PRESSURE,
                      OX_TANK_3_PRESSURE]
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

                fuel_vent_open = DAQ_STATE[FUEL_VENT_OUT] == 0
                fuel_prevalve_open = DAQ_STATE[FUEL_PREVALVE_OUT] == 1
                fuel_mpv_open = DAQ_STATE[FUEL_MPV_OUT] == 1
                fuel_feedline_purge_open = DAQ_STATE[FUEL_FEEDLINE_PURGE_OUT] == 1
                ox_fill_purge_open = DAQ_STATE[OX_FILL_PURGE_OUT] == 1
                fuel_pre_press_open = DAQ_STATE[FUEL_PRE_PRESS_OUT] == 1
                ox_pre_press_open = DAQ_STATE[OX_PRE_PRESS_OUT] == 1
                ox_feedline_purge_open = DAQ_STATE[OX_FEEDLINE_PURGE_OUT] == 1
                engine_pneumatics_iso_open = DAQ_STATE[ENGINE_PNEUMATICS_ISO_OUT] == 1
                engine_pneumatics_vent_open = DAQ_STATE[ENGINE_PNEUMATICS_VENT_OUT] == 0
                solenoid_manifold_open = DAQ_STATE[SOLENOID_MANIFOLD_OUT] == 1
                air_drive_iso_1_open = DAQ_STATE[AIR_DRIVE_ISO_1_OUT] == 1
                air_drive_iso_2_open = DAQ_STATE[AIR_DRIVE_ISO_2_OUT] == 1
                gas_booster_fill_open = DAQ_STATE[GAS_BOOSTER_FILL_OUT] == 1
                press_fill_open = DAQ_STATE[PRESS_FILL_OUT] == 1
                press_vent_open = DAQ_STATE[PRESS_VENT_OUT] == 0
                fuel_press_iso_open = DAQ_STATE[FUEL_PRESS_ISO_OUT] == 1
                ox_press_open = DAQ_STATE[OX_PRESS_OUT] == 1
                ox_low_vent_open = DAQ_STATE[OX_LOW_VENT_OUT] == 0
                ox_fill_valve_open = DAQ_STATE[OX_FILL_VALVE_OUT] == 1
                ox_high_flow_vent_open = DAQ_STATE[OX_HIGH_FLOW_VENT_OUT] == 1
                ox_mpv_open = DAQ_STATE[OX_MPV_OUT] == 1

                if ox_mpv_open and OX_MPV_LAST_OPEN is None:
                    OX_MPV_LAST_OPEN = sy.TimeStamp.now()
                elif not ox_mpv_open:
                    MPV_LAST_OPEN = None

                if fuel_mpv_open and FUEL_MPV_LAST_OPEN is None:
                    FUEL_MPV_LAST_OPEN = sy.TimeStamp.now()
                elif not fuel_mpv_open:
                    FUEL_MPV_LAST_OPEN = None

                fuel_tank_1_delta = 0
                fuel_tank_2_delta = 0
                trailer_pneumatics_delta = 0
                press_tank_delta = 0
                ox_tank_delta =0

                if ox_press_open:
                    ox_tank_delta += 2.5
    
                if fuel_press_iso_open:
                    fuel_tank_1_pressure += 2.5
                    fuel_tank_2_pressure += 2.5
                
                if ox_low_vent_open:
                    ox_tank_delta -= 1.5

                if ox_high_flow_vent_open:
                    ox_tank_delta -= 2.5

                if engine_pneumatics_iso_open:
                    trailer_pneumatics_delta += 2.5

                if engine_pneumatics_vent_open:
                    trailer_pneumatics_delta -= 1.5

                if press_fill_open:
                    press_tank_delta += 2.5

                if press_vent_open:
                    press_tank_delta -= 1.5

                if (ox_press_open and press_tank_pressure > 0
                        and not ox_tank_1_pressure > press_tank_pressure):
                    ox_tank_delta -= 1
                    press_tank_delta += 1

                if (fuel_press_iso_open and press_tank_pressure > 0
                        and not fuel_tank_1_pressure > press_tank_pressure):
                    fuel_tank_1_delta -= 1
                    press_tank_delta += 1

                #updates when vent and one valve is open
                # if vent_open and tpc_1_open:
                #     scuba_delta -= 1

                if ox_mpv_open:
                    ox_tank_delta -= 0.1 * sy.TimeSpan(sy.TimeStamp.now() - OX_MPV_LAST_OPEN).seconds
                
                if fuel_mpv_open:
                    fuel_tank_1_delta -= 0.1 * sy.TimeSpan(sy.TimeStamp.now() - FUEL_MPV_LAST_OPEN).seconds

                ox_tank_1_pressure += ox_tank_delta
                ox_tank_2_pressure += ox_tank_delta
                ox_tank_3_pressure += ox_tank_delta
                fuel_tank_1_pressure += fuel_tank_1_delta
                fuel_tank_2_pressure += fuel_tank_2_delta
                trailer_pneumatics_pressure += trailer_pneumatics_delta
                press_tank_pressure += press_tank_delta

                if ox_tank_1_pressure < 0:
                    ox_tank_1_pressure = 0
                if ox_tank_2_pressure < 0:
                    ox_tank_2_pressure = 0
                if ox_tank_3_pressure < 0:
                    ox_tank_3_pressure = 0
                if fuel_tank_1_pressure < 0:
                    fuel_tank_1_pressure = 0
                if fuel_tank_2_pressure < 0:
                    fuel_tank_2_pressure = 0
                if trailer_pneumatics_pressure < 0:
                    trailer_pneumatics_pressure = 0
                if press_tank_pressure < 0:
                    press_tank_pressure = 0

                now = sy.TimeStamp.now()

                ok = w.write({
                    DAQ_TIME: now,
                    FUEL_VENT_IN: int(fuel_vent_open),
                    FUEL_PREVALVE_IN: int(fuel_prevalve_open),
                    FUEL_MPV_IN: int(fuel_mpv_open),
                    FUEL_FEEDLINE_PURGE_IN: int(fuel_feedline_purge_open),
                    OX_FILL_PURGE_IN: int(ox_fill_purge_open),
                    FUEL_PRE_PRESS_IN: int(fuel_pre_press_open),
                    OX_PRE_PRESS_IN: int(ox_pre_press_open),
                    OX_FEEDLINE_PURGE_IN: int(ox_feedline_purge_open),
                    ENGINE_PNEUMATICS_ISO_IN: int(engine_pneumatics_iso_open),
                    ENGINE_PNEUMATICS_VENT_IN: int(engine_pneumatics_vent_open),
                    SOLENOID_MANIFOLD_IN: int(solenoid_manifold_open),
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
                    OX_MPV_IN: int(ox_mpv_open),
                    FUEL_TANK_1_PRESSURE: fuel_tank_1_pressure,
                    FUEL_TANK_2_PRESSURE: fuel_tank_2_pressure,
                    TRAILER_PNEUMATICS_PRESSURE: trailer_pneumatics_pressure,
                    PRESS_TANK_PRESSURE: press_tank_pressure,
                    OX_TANK_1_PRESSURE: ox_tank_1_pressure,
                    OX_TANK_2_PRESSURE: ox_tank_2_pressure,
                    OX_TANK_3_PRESSURE: ox_tank_3_pressure
                })

                i += 1
                if (i % 40) == 0:
                    print(f"Committing {i} samples")
                    ok = w.commit()

            except Exception as e:
                print(e)
                raise e
