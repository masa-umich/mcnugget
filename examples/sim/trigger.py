import uuid

import synnax as sy
from typing import Callable
import json
import matplotlib.pyplot as plt

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False,
)


# creata generic decorator
def range_create(f: [Callable, [sy.Range], None]):
    with client.new_streamer(["sy_range_set"]) as s:
        for r in s:
            rng = json.loads(r["sy_range_set"].data)
            f(client.ranges.retrieve(uuid.UUID(rng["key"])))


@range_create
def process(s: sy.Range):
    print(s.gse_ai_0.__array__())
    # plt.plot(sy.lapsed_seconds(s.gse_ai_time), s.gse_ai_0)
    # plt.savefig("test.png")



