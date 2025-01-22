"""
This script creates ALL of the channels that will (ever?) be needed on GSE for the W25 testing campaign.
"""

import synnax as sy
import os.path as path
import datetime
import json

client = sy.Synnax()

channel_creation_info = path.join(
    path.dirname(__file__),
    "config",
    f"channel_creation_info_{datetime.datetime.now()}.json",
)

FILE_DICT = {}

gse_state_time = client.channels.create(
    name="gse_state_time",
    data_type=sy.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)
FILE_DICT["gse_state_time"] = {
    "key": gse_state_time.key,
    "name": gse_state_time.name,
    "data_type": gse_state_time.data_type,
    "index": "is_index=True",
}

gse_ai_time = client.channels.create(
    name="gse_ai_time",
    data_type=sy.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)
FILE_DICT["gse_ai_time"] = {
    "key": gse_ai_time.key,
    "name": gse_ai_time.name,
    "data_type": gse_ai_time.data_type,
    "index": "is_index=True",
}

for i in range(42):
    c = client.channels.create(
        name=f"gse_pt_{i+1}",
        data_type=sy.DataType.FLOAT32,
        index=gse_state_time.key,
        retrieve_if_name_exists=True,
    )
    FILE_DICT[f"gse_pt_{i+1}"] = {
        "key": c.key,
        "name": f"gse_pt_{i+1}",
        "data_type": "FLOAT32",
        "index": gse_state_time.key,
    }

# thermistor signal + supply
c = client.channels.create(
    name="gse_thermistor_supply",
    data_type=sy.DataType.FLOAT32,
    index=gse_ai_time.key,
    retrieve_if_name_exists=True,
)
FILE_DICT["gse_thermistor_supply"] = {
    "key": c.key,
    "name": f"gse_thermistor_supply",
    "data_type": "FLOAT32",
    "index": gse_ai_time.key,
}

c = client.channels.create(
    name="gse_thermistor_signal",
    data_type=sy.DataType.FLOAT32,
    index=gse_ai_time.key,
    retrieve_if_name_exists=True,
)
FILE_DICT["gse_thermistor_signal"] = {
    "key": c.key,
    "name": f"gse_thermistor_signal",
    "data_type": "FLOAT32",
    "index": gse_ai_time.key,
}

for i in range(12):
    c = client.channels.create(
        name=f"gse_tc_{i+1}",
        data_type=sy.DataType.FLOAT32,
        index=gse_ai_time.key,
        retrieve_if_name_exists=True,
    )
    FILE_DICT[f"gse_tc_{i+1}"] = {
        "key": c.key,
        "name": f"gse_tc_{i+1}",
        "data_type": "FLOAT32",
        "index": gse_ai_time.key,
    }

    c = client.channels.create(
        name=f"gse_tc_{i+1}_raw",
        data_type=sy.DataType.FLOAT32,
        index=gse_ai_time.key,
        retrieve_if_name_exists=True,
    )
    FILE_DICT[f"gse_tc_{i+1}_raw"] = {
        "key": c.key,
        "name": f"gse_tc_{i+1}_raw",
        "data_type": "FLOAT32",
        "index": gse_ai_time.key,
    }

for i in range(24):
    c = client.channels.create(
        name=f"gse_state_{i+1}",
        data_type=sy.DataType.UINT8,
        index=gse_state_time.key,
        retrieve_if_name_exists=True,
    )
    FILE_DICT[f"gse_state_{i+1}"] = {
        "key": c.key,
        "name": f"gse_state_{i+1}",
        "data_type": "UINT8",
        "index": gse_state_time.key,
    }

    c = client.channels.create(
        name=f"gse_vlv_{i+1}",
        data_type=sy.DataType.UINT8,
        virtual=True,
        retrieve_if_name_exists=True,
    )
    FILE_DICT[f"gse_vlv_{i+1}"] = {
        "key": c.key,
        "name": f"gse_vlv_{i+1}",
        "data_type": "UINT8",
        "index": "virtual channel",
    }

with open(channel_creation_info, "w") as f:
    json.dump(FILE_DICT, f, indent=4)

print("yay :)")
