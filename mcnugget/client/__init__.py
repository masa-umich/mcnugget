import os

from pathlib import Path
from synnax import Synnax

import toml

TOML = toml.load(Path(os.path.dirname(__file__)).parent.parent / "pyproject.toml")[
    "tool"
]["synnax"]

try:
    client = Synnax(
        host=TOML["host"],
        port=TOML["port"],
        username=TOML["username"],
        password=TOML["password"],
        secure=TOML["secure"],
    )
except Exception as e:
    raise Exception(
        f"""
        Failed to connect to Synnax data processing sever. 
        Check your connection credentials and other options. 
        Screenshot this error and send it in the #sw_eng slack channel.
    """
    ) from e
