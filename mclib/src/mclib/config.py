import yaml
from typing import Any


class Config:
    """
    Parses a config.yaml file for channel mappings and autosequence variables.
    Use get_var(name) or get_vlv(name) to get objects from the config file
    Also checks that the requested field exists, throws an error if it doesn't
    """

    _yaml_data: dict

    vars: dict[str, Any]
    vlvs: dict[str, str]
    pts: dict[str, str]
    tcs: dict[str, str]

    def __init__(self, filepath: str):
        self.vlvs: dict[str, str] = {}
        self.normally_open_vlvs: dict[str, bool] = {}
        self.pts: dict[str, str] = {}
        self.tcs: dict[str, str] = {}
        self.vars: dict[str, Any] = {}

        prefix_map: dict[str, str] = {
            "ebox": "gse",
            "flight_computer": "fc",
            "bay_board_1": "bb1",
            "bay_board_2": "bb2",
            "bay_board_3": "bb3",
        }

        type_suffix_map: dict[str, str] = {"pts": "pt", "valves": "vlv", "tcs": "tc"}

        with open(filepath, "r") as f:
            self._yaml_data: dict = yaml.safe_load(f)

        self.vars: dict[str, Any] = self._yaml_data.get("variables", {})
        mappings_data: dict[Any, Any] = self._yaml_data.get("channel_mappings", {})

        for controller_key, prefix in prefix_map.items():
            controller_data = mappings_data.get(controller_key)
            if not controller_data:
                continue

            for type_key, suffix in type_suffix_map.items():
                items = controller_data.get(type_key)
                if not items:
                    continue  # Skip if this controller doesn't have TCs (e.g. Flight Computer)

                for config_ch_name, value in items.items():
                    # Construct Synnax Name: prefix_suffix_index (e.g., gse_pt_1)
                    ch_index = value
                    is_normally_open = False  # Default assumption

                    # If the entry has extra information
                    if isinstance(value, dict):
                        ch_index = value.get("id")
                        # We use .get(key, default) so it still works if 'normally_open' is omitted
                        is_normally_open = value.get("normally_open", False)

                    # Construct Synnax Name
                    synnax_name = f"{prefix}_{suffix}_{ch_index}"
                    real_name: str = config_ch_name.lower()

                    if suffix == "pt" or real_name == "ox_level_sensor":
                        self.pts[real_name] = synnax_name
                    elif suffix == "tc":
                        self.tcs[real_name] = synnax_name
                    elif suffix == "vlv":
                        self.vlvs[real_name] = synnax_name
                        self.normally_open_vlvs[real_name] = is_normally_open
                        self.normally_open_vlvs[synnax_name] = (
                            is_normally_open  # add both name styles
                        )
                    else:
                        raise Exception("Bad entry in mappings part of config")

    def get_var(self, name: str) -> Any:
        var: Any | None = self.vars.get(name.lower())
        if var is not None:
            return var
        else:
            raise Exception(f"Could not find variable with name: '{name}' in config")

    def get_vlv(self, name: str) -> str:
        vlv: str | None = self.vlvs.get(name.lower())
        if vlv is not None:
            return vlv
        else:
            raise Exception(f"Could not find valve with name: '{name}' in config")

    def is_vlv_nc(self, name: str) -> bool:
        nc: bool | None = self.normally_open_vlvs.get(name.lower())
        if nc is not None:
            return not nc
        else:
            raise Exception(f"Could not find valve with name: '{name}' in config")

    def get_state(self, name: str) -> str:
        vlv: str | None = self.vlvs.get(name.lower())
        if vlv is not None:
            return vlv.replace("vlv", "state")
        else:
            raise Exception(f"Could not find valve with name: '{name}' in config")

    def get_pt(self, name: str) -> str:
        pt: str | None = self.pts.get(name.lower())
        if pt is not None:
            return pt
        else:
            raise Exception(f"Could not find pt with name: '{name}' in config")

    def get_tc(self, name: str) -> str:
        tc: str | None = self.tcs.get(name.lower())
        if tc is not None:
            return tc
        else:
            raise Exception(f"Could not find tc with name: '{name}' in config")

    def get_vlvs(self) -> list[str]:
        all_vlvs: list[str] = []
        for vlv in self.vlvs.values():
            all_vlvs.append(vlv)
        return all_vlvs

    def get_states(self) -> list[str]:
        all_states: list[str] = []
        for vlv in self.vlvs.values():
            all_states.append(vlv.replace("vlv", "state"))
        return all_states

    def get_pts(self) -> list[str]:
        all_pts: list[str] = []
        for pt in self.pts.values():
            all_pts.append(pt)
        return all_pts

    def get_tcs(self) -> list[str]:
        all_tcs: list[str] = []
        for tc in self.tcs.values():
            all_tcs.append(tc)
        return all_tcs

    def get_sensors(self) -> list[str]:
        all_sensors: list[str] = []
        for pt in self.pts.values():
            all_sensors.append(pt)
        for tc in self.tcs.values():
            all_sensors.append(tc)
        return all_sensors
