import pytest
import synnax as sy
from mcnugget.cli.instrument import (
    pure_instrument,
    process_valve,
    Context,
    create_device_channels,
    process_pt,
    process_tc,
    ALIAS_COL,
    DEVICE_COL,
    PORT_COL,
    PT_MAX_PRESSURE_COL,
    TC_TYPE_COL,
    TC_OFFSET_COL,
)

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False,
)
rng = client.ranges.create(
    name="Test Active Range",
    time_range=sy.TimeRange(
        start=sy.TimeStamp.now(),
        end=sy.TimeStamp.now() + 5 * sy.TimeSpan.SECOND,
    )
)
client.ranges.set_active(rng.key)
ctx = Context(client=client, active_range=rng, indexes=dict())

create_device_channels(ctx)


@pytest.mark.instrument
class TestInstrument:
    def test_valve(self):
        process_valve(ctx, 1, {
            DEVICE_COL: "gse",
            ALIAS_COL: "My Valve",
            PORT_COL: 40,
        })

    def test_pt(self):
        process_pt(ctx, 2, {
            DEVICE_COL: "gse",
            ALIAS_COL: "My PT",
            PORT_COL: 12,
            PT_MAX_PRESSURE_COL: 4000,
        })

    def test_tc(self):
        process_tc(ctx, 3, {
            DEVICE_COL: "gse",
            ALIAS_COL: "My TC",
            PORT_COL: 70,
            TC_TYPE_COL: "K",
            TC_OFFSET_COL: 0,
        })

    def test_it_all(self):
        pure_instrument("Auto Instrumentation Sheet.xlsx", client)
