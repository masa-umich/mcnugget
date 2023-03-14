from synnax import TimeRange
from mcnugget.query.client import CLIENT
from enum import Enum
from pandas import DataFrame


class ECStates(Enum):
    MANUAL = 0
    ARMED = 1
    AUTO_PRESS = 2
    STARTUP = 3
    IGNITION = 4
    HOTFIRE = 5
    ABORT = 6
    POST = 7
    SAFE = 8
    IGNITION_FAIL = 9
    CONTINUE = 255


class FCStates(Enum):
    MANUAL = 0
    ARMED = 1
    ASCENT = 2
    DROGUE = 3
    MAIN = 4
    TOUCHDOWN = 5
    ABORT = 6


def read_during_state(
    tr: TimeRange, *channels: str, state: ECStates | FCStates = ECStates.HOTFIRE
) -> DataFrame:
    """
    Read data from the specified channels during the specified state.

    Args:
        tr: The time range to read data from.
        channels: The channels to read data from.
        state: The state to read data during.

    Returns:
        A DataFrame containing the data.
    """
    state_ch = "ec.STATE" if isinstance(state, ECStates) else "fc.STATE"
    df = read(tr, *channels, state_ch)
    ec_data = df[state_ch].to_numpy()
    return df[ec_data == state.value]

def read(
    tr: TimeRange, *channels: str
) -> DataFrame:
    """
    Read data from the specified channels during the specified state.

    Args:
        tr: The time range to read data from.
        channels: The channels to read data from.

    Returns:
        A DataFrame containing the data.
    """
    df = DataFrame()
    for chan in [*channels]:
        print(chan)
        df[chan] = CLIENT.read(tr.start.datetime(), tr.end.datetime(), chan)[0]

    return df
