import synnax as sy

PRESSURE_TRANSDUCERS = []

client = sy.Synnax()

with client.control.acquire(
    name=""
)