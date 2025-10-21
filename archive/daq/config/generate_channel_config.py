"""
Generates a config file that contains
    - 80 ai channels
        - 14 TC
        - 60 AI
    - 32 valve channels
"""

import json

CONFIG_FILE = "daq/channels.json"
DATA = {}

for i in range(60):
    DATA[f"gse_pt_{i}"] = f"gse_ai_{i}"

for i in range(32):
    DATA[f"gse_vlv_{i}_cmd"] = f"gse_di_{i % 8}_{i // 8}"
    DATA[f"gse_vlv_{i}_state"] = f"gse_do_{i % 8}_{i // 8}"

for i in range(14):
    DATA[f"gse_tc_{i}"] = f"gse_ai_{i + 60}"

with open(CONFIG_FILE, "w") as f:
    json.dump(DATA, f, indent=4)