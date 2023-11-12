import click
import pandas as pd
from dataclasses import dataclass
import gspread
from rich import print
import synnax as sy
from mcnugget.client import client

ALIAS_COL = "Name"
DEVICE_COL = "Device"
PORT_COL = "Port"
TYPE_COL = "Type"
PT_MAX_PRESSURE_COL = "Max Pressure (PSI)"
TC_TYPE_COL = "TC Type"
TC_OFFSET_COL = "TC Offset (K)"
GSE_DEVICE = "gse"

Device = GSE_DEVICE

VALID_DEVICES = [GSE_DEVICE]

PT_TYPE = "PT"
TC_TYPE = "TC"
VLV_TYPE = "VLV"
LC_TYPE = "LC"

VALID_TYPES = [PT_TYPE, TC_TYPE, VLV_TYPE, LC_TYPE]

GSE_AI_TIME = sy.Channel(
    name="gse_ai_time", is_index=True, data_type=sy.DataType.TIMESTAMP
)

GSE_DI_TIME = sy.Channel(
    name="gse_di_time",
    is_index=True,
    data_type=sy.DataType.TIMESTAMP,
)

GSE_DOA_TIME = sy.Channel(
    name="gse_doa_time", is_index=True, data_type=sy.DataType.TIMESTAMP
)


@dataclass
class Context:
    client: sy.Synnax
    active_range: sy.Range
    indexes: dict[str, sy.Channel]


@click.command()
@click.argument("sheet", type=click.Path(exists=False), required=True)
@click.option("--gcreds", type=click.Path(exists=False), required=False)
def instrument(sheet: str | None, gcreds: str | None):
    pure_instrument(sheet, client=client, gcreds=gcreds)


def pure_instrument(sheet: str | None, client: sy.Synnax, gcreds: str | None = None):
    print(sheet)
    if ".xlsx" in sheet:
        data = process_excel(sheet)
    elif "docs.google.com" in sheet:
        data = process_url(sheet, gcreds)
    else:
        data = process_name(sheet, gcreds)

    ctx = Context(
        client=client, active_range=client.ranges.retrieve_active(), indexes={}
    )

    create_device_channels(ctx)
    existing_ports = {int, bool}
    for index, row in data.iterrows():
        process_row(ctx, index, row, existing_ports)


def process_excel(source) -> pd.DataFrame:
    try:
        workbook = pd.read_excel(source)
    except pd.errors.EmptyDataError:
        raise "failed while trying to extract excel sheet from " + source
    return workbook


def process_url(source, creds) -> pd.DataFrame:
    try:
        gspread_client = gspread.service_account(creds)
    except FileNotFoundError:
        raise "to authenticate to the gcloud server, you must add a valid credentials.json file in this directory"
    sheet = gspread_client.open_by_url(source)
    if not sheet:
        raise "Unable to process url as google sheet"
    return extract_google_sheet(sheet)


def extract_google_sheet(sheet: gspread.Spreadsheet) -> pd.DataFrame:
    vals = sheet.sheet1.get_all_values()
    return pd.DataFrame(vals[1:], columns=vals[0])


def process_name(source, creds) -> pd.DataFrame:
    try:
        gspread_client = gspread.service_account(creds)
    except FileNotFoundError:
        raise "to authenticate to the gcloud server, you must add a valid credentials.json file in this directory"
    sheet = gspread_client.open(source)
    if not sheet:
        raise "Unable to process name as google sheet"
    return extract_google_sheet(sheet)


def process_row(ctx: Context, index: int, row: dict, ports: {int, str}):
    if ports.get(row[PORT_COL]):
        print(
            f"""[purple]Row {index} - [/purple]Port {row[PORT_COL]} is already in use by channel {ports.get(row[PORT_COL])} and was not updated."""
        )
    else:
        ports[row[PORT_COL]] = row[ALIAS_COL]
    type_ = row[TYPE_COL]
    if type_ == VLV_TYPE:
        return process_valve(ctx, index, row)
    if type_ == PT_TYPE:
        return process_pt(ctx, index, row)
    if type_ == TC_TYPE:
        return process_tc(ctx, index, row)
    if type_ == LC_TYPE:
        return

    print(
        f"""[purple]Row {index} - [/purple][red]Invalid sensor or actuator type '{type}' in row {index}[/red]\n[blue]Valid types are: {VLV_TYPE}, {PT_TYPE}, {TC_TYPE}[/blue]"""
    )


def get_device(index: int, row: dict) -> (str, bool):
    device = row[DEVICE_COL]
    if device not in VALID_DEVICES:
        print(
            f"""[red]Invalid device name '{device}' in row {index}[/red]\n[blue]Valid devices are: {VALID_DEVICES}[/blue]"""
        )
        return "", False

    return device, True


GSE_VALID_PORTS = range(0, 80)


def get_port(index: int, row: dict, device: Device) -> (int, bool):
    port = row[PORT_COL]
    try:
        port = int(port)
    except ValueError:
        print(
            f"""[red]Invalid port number '{port}' in row {index}[/red]\n[blue]Value must be a positive integer[/blue]"""
        )
        return -1, False
    if device == GSE_DEVICE and port not in GSE_VALID_PORTS:
        print(
            f"""[red]Invalid port number for {device} '{port}' in row {index}[/red]\n[blue]Valid ports are: {GSE_VALID_PORTS}[/blue]"""
        )
        return -1, False
    return port, True


def create_device_channels(ctx: Context) -> (dict, bool):
    res = ctx.client.channels.create(
        [GSE_AI_TIME, GSE_DI_TIME], retrieve_if_name_exists=True
    )
    ctx.indexes["gse_ai"] = res[0]
    ctx.indexes["gse_di"] = res[1]


# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# |||||||||||||||||||||||||||||||||||||||||||||||||||| VALVES ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

VALVE_AI_PORT_OFFSET = 36
VALID_VALVE_PORTS = range(0, 24)


def process_valve(ctx: Context, index: int, row: dict):
    # get the device name
    device, ok = get_device(index, row)
    if not ok:
        return

    # get the port number
    port, ok = get_port(index, row, device)
    if not ok:
        return

    print(
        f"[purple]Row {index} - [/purple][blue]Configuring valve {port} on {device} port {VALVE_AI_PORT_OFFSET + port}[/blue]"
    )

    if port not in VALID_VALVE_PORTS:
        print(
            f"""[red]Valves can only be connected to ports {VALID_VALVE_PORTS.start} through {VALID_VALVE_PORTS.stop}[/red]"""
        )
        return

    ack_channel = sy.Channel(
        name=f"gse_doa_{port}",
        data_type=sy.DataType.UINT8,
        index=ctx.indexes["gse_ai"].key,
    )
    i_channel = sy.Channel(
        name=f"gse_ai_{port + VALVE_AI_PORT_OFFSET}",
        data_type=sy.DataType.FLOAT32,
        index=ctx.indexes["gse_ai"].key,
    )
    v_channel = sy.Channel(
        name=f"gse_di_{port}",
        data_type=sy.DataType.FLOAT32,
        index=ctx.indexes["gse_di"].key,
    )
    input_channels = [ack_channel, i_channel, v_channel]

    try:
        input_channels = ctx.client.channels.create(
            input_channels, retrieve_if_name_exists=True
        )
    except Exception as e:
        print(
            f"[orange]Failed to retrieve channels for {device} valve {port}[/orange]\n[blue]Error: {e}[/blue]"
        )
        return

    cmd_time_channel = sy.Channel(
        name=f"gse_doc_{port}_time", data_type=sy.DataType.TIMESTAMP, is_index=True
    )

    try:
        cmd_time_channel = ctx.client.channels.create(
            cmd_time_channel, retrieve_if_name_exists=True
        )
    except Exception as e:
        print(
            f"[orange]Failed to retrieve channels for {device} valve {port}[/orange]\n[blue]Error: {e}[/blue]"
            ""
        )
        return

    cmd_channel = sy.Channel(
        name=f"gse_doc_{port}", data_type=sy.DataType.UINT8, index=cmd_time_channel.key
    )

    try:
        cmd_channel = ctx.client.channels.create(
            cmd_channel, retrieve_if_name_exists=True
        )
    except Exception as e:
        print(
            f"[orange]Failed to retrieve channels for {device} valve {port}[/orange]\n[blue]Error: {e}[/blue]"
            ""
        )
        return

    name = str(row[ALIAS_COL])
    if len(name) == 0:
        print(
            f"[orange]Alias for {device} valve {port} is empty. We won't set any aliases for this channel.[/orange]"
        )

    name = name + "_"
    aliases = {
        ack_channel.name: name + "ack",
        i_channel.name: name + "i",
        v_channel.name: name + "v",
        cmd_channel.name: name + "cmd",
        cmd_time_channel.name: name + "cmd_time",
    }
    try:
        ctx.active_range.set_alias(aliases)
    except Exception as e:
        print(
            f"""[red]Failed to set aliases for {device} valve {port}[/red]\n[blue]Error: {e}[/blue]"""
        )
        return


# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# ||||||||||||||||||||||||||||||||||||||||||||| PRESSURE TRANSDUCERS |||||||||||||||||||||||||||||||||||||||||||||||||||
# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

PT_VALID_PORTS = range(0, 37)
PT_MAX_OUTPUT_VOLTAGE = 4500
PT_OFFSET = 500


def pt_analog_port(port: int) -> int:
    if port == 36:
        return 60
    return port


def process_pt(ctx: Context, index: int, row: dict):
    # get the device name
    device, ok = get_device(index, row)
    if not ok:
        return False

    # get the port number
    port, ok = get_port(index, row, device)
    if not ok:
        return False
    if port not in PT_VALID_PORTS:
        print(
            f"[red]Pressure transducers can only be connected to ports {PT_VALID_PORTS}[/red]"
        )
        return False

    print(
        f"[purple]Row {index} - [/purple][blue]Configuring PT {port} on {device} port {port}[/blue]"
    )

    name = f"{device}_ai_{pt_analog_port(port)}"

    try:
        ctx.client.channels.create(
            name=name,
            data_type=sy.DataType.FLOAT32,
            index=ctx.indexes["gse_ai"].key,
            retrieve_if_name_exists=True,
        )
    except sy.NoResultsError:
        print(
            f"""[orange]Channel {name} does not exist. We can continue, but this is likely an error.[/orange]"""
        )
        return False
    except Exception as e:
        print(
            f"""[red]Failed to retrieve channel for {device} pressure transducer {port}[/red]\n[blue]Error: {e}[/blue]"""
        )
        return False

    max_pressure = row[PT_MAX_PRESSURE_COL]
    # try to convert max_pressure to a float
    try:
        max_pressure = float(max_pressure)
    except ValueError:
        print(
            f"""[red]Invalid value for PT max pressure '{max_pressure}' in row {index}[/red]\n[blue]Value must be a positive number[/blue]"""
        )
        return False

    slope = (PT_MAX_OUTPUT_VOLTAGE - PT_OFFSET) / max_pressure
    try:
        ctx.active_range.meta_data.set({f"{name}_pt_slope": slope})
    except Exception as e:
        print(
            f"""[red]Failed to set slope for {device} pressure transducer {port}[/red]\n[blue]Error: {e}[/blue]"""
        )
        return False

    alias = str(row[ALIAS_COL]).rstrip()
    if len(alias) == 0:
        print(
            f"""[orange]Alias for {device} pressure transducer {port} is empty. We won't set any aliases for this channel.[/orange]"""
        )
        return True

    try:
        ctx.active_range.set_alias({name: alias})
    except Exception as e:
        print(
            f"""[red]Failed to set alias for {device} pressure transducer {port}[/red]\n[blue]Error: {e}[/blue]"""
        )
        return False

    return True


# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# ||||||||||||||||||||||||||||||||||||||||||||| THERMOCOUPLES ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

TC_PORT_OFFSET = 64
TC_VALID_PORTS = range(0, 16)


def process_tc(ctx: Context, index: int, row: dict):
    # get the device name
    device, ok = get_device(index, row)
    if not ok:
        return False

    # get the port number
    port, ok = get_port(index, row, device)
    if not ok:
        return False

    if port not in TC_VALID_PORTS:
        print(
            f"""[red]Thermocouples can only be connected to ports {TC_VALID_PORTS}[/red]"""
        )
        return False

    print(
        f"[purple]Row {index} - [/purple][blue]Configuring TC {port} on {device} port {TC_PORT_OFFSET + port}[/blue]"
    )

    port += TC_PORT_OFFSET

    name = f"{device}_ai_{port}"

    ch = sy.Channel(
        name=name,
        data_type=sy.DataType.FLOAT32,
        index=ctx.indexes["gse_ai"].key,
    )

    try:
        ch = ctx.client.channels.create(ch, retrieve_if_name_exists=True)
    except Exception as e:
        print(
            f"""[red]Failed to retrieve channel for {device} thermocouple {port}[/red]\n Error: {e}"""
        )
        return False

    if ch.data_type != sy.DataType.FLOAT32:
        print(
            f"""[orange]Invalid data type for {device} thermocouple {port} - should be FLOAT32.[/orange]"""
        )

    tc_type = str(row[TC_TYPE_COL]).rstrip()
    if len(tc_type) == 0:
        print(
            f"[red]Invalid value for TC type '{tc_type}' in row {index}[/red]\n[blue]Value must be a valid thermocouple type[/blue]"
        )
        return True

    tc_offset = str(row[TC_OFFSET_COL]).rstrip()
    if len(tc_offset) == 0:
        print(
            f"[orange]Invalid value for TC offset '{tc_offset}' in row {index}[/orange]\n[blue]We'll use the default value of 0[/blue]"
        )
        return True

    try:
        ctx.active_range.meta_data.set(
            {f"{name}_tc_type": tc_type, f"{name}_tc_offset": tc_offset}
        )
    except Exception as e:
        print(
            f"""
        [red]Failed to set thermocouple type and offset for {device} thermocouple {port}[/red]
        [blue]Error: {e}[/blue]
        """
        )
        return False

    alias = str(row[ALIAS_COL]).rstrip()
    if len(alias) == 0:
        print(
            f"""
        [orange]Alias for {device} thermocouple {port} is empty. We won't set any aliases for this channel.[/orange]
        """
        )
        return True

    try:
        ctx.active_range.set_alias({name: alias})
    except Exception as e:
        print(
            f"""
        [red]Failed to set alias for {device} thermocouple {port}[/red]
        [blue]Error: {e}[/blue]
        """
        )
        return False
