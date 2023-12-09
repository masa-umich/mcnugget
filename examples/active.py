import synnax as sy

client = sy.Synnax(
    host="synnax.masa.engin.umich.edu",
    port=80,
    username="synnax",
    password="seldon",
    secure=True,
)
rng = client.ranges.create(
    name="Dec 9 Level Sensing Cryoflow",
    time_range=sy.TimeRange(
        start=sy.TimeStamp.now(),
        end=sy.TimeStamp.now() + 5 * sy.TimeSpan.SECOND,
    ),
)
rng = client.ranges.retrieve("Dec 9 Level Sensing Cryoflow")
client.ranges.set_active(rng.key)
