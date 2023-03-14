import os

from pathlib import Path
from synnax import Synnax

import toml

TOML = toml.load(Path(os.path.dirname(__file__)).parent.parent / "pyproject.toml")['tool']['synnax']

print(TOML)

try:
    CLIENT = Synnax(
        host=TOML["host"],
        port=TOML["port"],
        username=TOML["username"],
        password=TOML["password"],
        secure=TOML["secure"],
    )
except Exception as e:
    raise Exception(
        f"""
        Failed to connect to Synnax data processing sever. Screenshot
        this error and send it in the #avionics slack channel.
    """
    ) from e
