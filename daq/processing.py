import synnax as sy
from synnax.hardware import ni
import pandas as pd

client = sy.Synnax(
    host="masasynnax.ddns.net",
    port=9090,
    username="synnax",
    password="seldon",
)


def process_vlv(row: pd.Series, digital_task):
    channel = int(row["Channel"])

    gse_state_time = client.channels.create(
        name="gse_state_time",
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )

    state_chan = client.channels.create(
        name=f"gse_state_{channel}",
        data_type=sy.DataType.UINT8,
        retrieve_if_name_exists=True,
        index=gse_state_time.key,
    )

    cmd_chan = client.channels.create(
        name=f"gse_vlv_{channel}",
        data_type=sy.DataType.UINT8,
        retrieve_if_name_exists=True,
        virtual=True,
    )

    do_chan = ni.DOChan(
        cmd_channel=cmd_chan.key,
        state_channel=state_chan.key,
        port=(channel / 8) + 4,
        line=(channel - 1) % 8,
    )

    digital_task.config.channels.append(do_chan)
    print("Valve channel created.")


def process_pt(row: pd.Series, analog_task: ni.AnalogReadTask, analog_card: sy.Device):
    synnax_channel_time = client.channels.create(
        name="gse_ai_time",
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
        is_index=True,
    )
    synnax_channel = client.channels.create(
        name=f"gse_pt_{row['Channel']}",
        data_type=sy.DataType.FLOAT32,
        index=synnax_channel_time.key,
        retrieve_if_name_exists=True,
    )
    pt_channel = ni.AIVoltageChan(
        channel=synnax_channel.key,
        device=analog_card.key,
        port=row["Channel"] - 1,
        custom_scale=ni.LinScale(
            slope= ((row["Max Pressure"]) / (row["Max Output Voltage"] - row["Calibration Offset (V)"])),
            y_intercept= (-(row["Max Pressure"]) / (row["Max Output Voltage"] - row["Calibration Offset (V)"])) * row["Calibration Offset (V)"],
            pre_scaled_units="Volts",
            scaled_units="PoundsPerSquareInch",
        ),
        terminal_config="RSE",
        max_val=row["Max Pressure"],
    )
    analog_task.config.channels.append(pt_channel)
    print("PT channel created.")


def process_tc(row: pd.Series, analog_task: ni.AnalogReadTask, analog_card: sy.Device):
    port = row["Channel"] - 1 + 65

    synnax_channel_time = client.channels.create(
        name="gse_ai_time",
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
        is_index=True,
    )

    synnax_channel = client.channels.create(
        name=f"gse_tc_{row['Channel']}",
        data_type=sy.DataType.FLOAT32,
        index=synnax_channel_time.key,
        retrieve_if_name_exists=True,
    )

    tc_channel = ni.AIVoltageChan(
        channel=synnax_channel.key,
        device=analog_card.key,
        port=port,
        custom_scale=ni.LinScale(
            slope=row["Calibration Slope (mV/psig)"],
            y_intercept=row["Calibration Offset (V)"],
            pre_scaled_units="Volts",
            scaled_units="Volts",
        ),
    )

    analog_task.config.channels.append(tc_channel)

    print("I am a thermocouple")


def process_lc(row: pd.Series, analog_task: ni.AnalogReadTask, analog_card: sy.Device):
    print("I am a load cell")
