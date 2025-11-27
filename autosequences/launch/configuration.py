# configuration.py
from typing import List
import yaml
from dataclasses import dataclass, fields

@dataclass
class Settings:
    press_rate_1: float
    press_rate_1_ittrs: int
    press_rate_2: float
    copv_upper_bound_temp: float
    copv_lower_bound_temp: float
    copv_minimum_temp: float
    copv_pressure_target: float
    copv_pressure_margin: float
    copv_pressure_max: float
    bottle_equalization_threshold: float

@dataclass
class ChannelMap:
    # EBox / Launch GSE
    # PTs
    Ox_Fill_PT: str
    Pneumatics_2k_Bottle_PT: str
    Engine_Pneumatics_PT: str
    Trailer_Pneumatics_PT: str
    Purge_2k_Bottle_PT: str
    Purge_Post_Reg_PT: str
    Trickle_Purge_PT: str
    Bottle_1_PT: str
    Bottle_2_PT: str
    Bottle_3_PT: str
    Post_Press_Fill_PT: str
    Reg_Set_PT: str
    Fuel_Level_Sensing_PT: str
    # Valves
    Ox_Fill_Valve: str
    Ox_Drain_Valve: str
    Press_Iso_1: str
    Press_Iso_2: str
    Press_Iso_3: str
    Press_Fill_Iso: str
    Press_Fill_Vent: str
    Ox_Pre_Press: str
    Fuel_Fill_Purge: str
    Ox_MPV_Purge: str
    Fuel_MPV_Purge: str
    Ox_Fill_QD_Pilot: str
    Ox_Pre_Press_QD_Pilot: str
    COPV_Fill_QD_Pilot: str
    # TCs
    Bottle_1_Skin_TC: str
    Bottle_2_Skin_TC: str
    Bottle_3_Skin_TC: str

    # Flight Computer
    # PTs
    Recovery_Bottle_PT: str
    # Valves
    Recovery_Piston_Pilot: str
    Drogue_Parachute_TD: str
    Main_Parachute_TD: str
    # TCs (N/A)

    # Press Bay Board
    # PTs
    COPV_PT_1: str
    COPV_PT_2: str
    Fuel_TPC_Inlet_PT: str
    Fuel_TPC_Outlet_PT: str
    Fuel_Pilot_Outlet_PT: str
    Fuel_Dome_PT: str
    Fuel_Tank_PT_1: str
    Fuel_Tank_PT_2: str
    # Valves
    COPV_Vent: str
    Fuel_Dome_Iso: str
    Fuel_Vent: str
    # TCs
    COPV_TC_1: str
    COPV_TC_2: str

    # Intertank Bay Board
    # PTs
    Ox_TPC_Inlet_PT: str
    Ox_Pilot_Outlet_PT: str
    Ox_Dome_PT: str
    Ox_TPC_Outlet_PT: str
    Ox_Tank_PT_1: str
    Ox_Tank_PT_2: str
    Fuel_Manifold_PT_2: str
    Regen_Manifold_PT_2: str
    # Valves
    Ox_Dome_Iso: str
    Ox_Vent: str
    # TCs
    Ox_Ullage_TC: str

    # Engine Bay Board
    # PTs
    Ox_MPV_Inlet_PT: str
    Ox_MPV_Throat_PT: str
    Ox_Level_Sensor: str
    Fuel_Flowmeter_Inlet_PT: str
    Fuel_Flowmeter_Throat_PT: str
    Chamber_PT_1: str
    Chamber_PT_2: str
    Chamber_PT_3: str
    Fuel_Manifold_PT_1: str
    Regen_Manifold_PT_1: str
    # Valves
    Ox_MPV: str
    Fuel_MPV: str
    # TCs
    Ox_Level_Sensor_TC: str
    Fuel_Manifold_TC_1: str
    Fuel_Manifold_TC_2: str
    Regen_Manifold_TC_1: str
    Regen_Manifold_TC_2: str

class Configuration:
    variables: Settings
    mappings: ChannelMap
    channels: dict

    def get_valves(self) -> list:
        valves: list = []
        for channel in self.channels.values():
            if "vlv" in channel: 
                valves.append(channel)
        return valves

    def get_states(self) -> list:
        states: list = []
        for channel in self.channels.values():
            if "vlv" in channel:
                state_channel_name = channel.replace("vlv", "state")
                states.append(state_channel_name)
        return states

    def get_pts(self) -> list:
        pts: list = []
        for channel in self.channels.values():
            if "pt" in channel: 
                pts.append(channel)
        return pts

    def get_tcs(self) -> list:
        tcs: list = []
        for channel in self.channels.values():
            if "tc" in channel: 
                tcs.append(channel)
        return tcs

    def __init__(self, filepath: str):
        self.channels = {} # initialize the channels flat map

        with open(filepath, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        # Populate Settings class from "variables"
        vars_data = yaml_data.get("variables", {})
        valid_var_keys = {f.name for f in fields(Settings)}
        filtered_vars = {k: v for k, v in vars_data.items() if k in valid_var_keys}
        self.variables = Settings(**filtered_vars)

        # Populate ChannelMap from "channel_mappings"
        mappings_data = yaml_data.get("channel_mappings", {})
        # Add the handoff channel manually
        if "handoff" in mappings_data:
            self.channels["handoff"] = mappings_data["handoff"]
        
        prefix_map = {
            "ebox": "gse",
            "flight_computer": "fc",
            "bay_board_1": "bb1",
            "bay_board_2": "bb2",
            "bay_board_3": "bb3"
        }

        type_suffix_map = {
            "pts": "pt",
            "valves": "vlv",
            "tcs": "tc"
        }

        for controller_key, prefix in prefix_map.items():
            controller_data = mappings_data.get(controller_key)
            if not controller_data:
                continue

            for type_key, suffix in type_suffix_map.items():
                items = controller_data.get(type_key)
                if not items:
                    continue # Skip if this controller doesn't have TCs (e.g. Flight Computer)

                for real_name, index in items.items():
                    # Construct Synnax Name: prefix_suffix_index (e.g., gse_pt_1)
                    synnax_name = f"{prefix}_{suffix}_{index}"
                    self.channels[real_name] = synnax_name

        # 3. Instantiate ChannelMap
        # We iterate over the fields in ChannelMap to find the matching name in our flat_map
        channel_args = {}
        for field in fields(ChannelMap):
            # We match strictly by name (YAML key must match Dataclass field name)
            if field.name in self.channels:
                channel_args[field.name] = self.channels[field.name]
            else:
                print(f"Warning: Channel '{field.name}' defined in Python but not found in YAML config.")
                channel_args[field.name] = "MISSING_CONFIG"
        
        self.mappings = ChannelMap(**channel_args)