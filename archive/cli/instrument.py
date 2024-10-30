import click
import math
import pandas as pd
from dataclasses import dataclass
import gspread
from rich import print
import synnax as sy
from mcnugget.client import client
from rich.prompt import Prompt, Confirm

ALIAS_COL = "Name"
DEVICE_COL = "Device"
PORT_COL = "Port"
TYPE_COL = "Type"
PT_MAX_PRESSURE_COL = "Max Pressure (PSI)"
OPT_PT_OFFSET_COL = "PT Offset (V - Optional)"
OPT_PT_SLOPE_COL = "PT Slope (PSI/V - Optional)"
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


def main():
    print(
        """[purple]Commencing instrumentation update procedure[/purple]"""
    )
    sheet, gcreds = create_popup()
    # print(f"would run instrumentation on {sheet}")
    pure_instrument(sheet, client, gcreds=None)


global selected_value
selected_value = None  # this is necessary; trust
global confirm_button
confirm_button = None  # this is also necessary; trust
global gcreds_value
gcreds_value = None
global gcreds_button
gcreds_button = None


def create_popup():
    def set_selected_value(x):
        global selected_value
        if x is not None and x != '':
            selected_value = x
        confirm_button.config(text=f"Confirm\n{selected_value}")

    def get_selected_value():
        global selected_value
        return selected_value

    def get_gcreds():
        global gcreds_value
        return gcreds_value

    def clear_popup():
        if get_selected_value() is None:
            messagebox.showinfo(title="Warning", message="Please choose a source")
        elif ".xlsx" not in get_selected_value() and get_gcreds() is None:
            messagebox.showinfo(title="Warning", message="Please provide valid gcreds if retrieving from a google sheet.")
        else:
            popup.destroy()

    def choose_gcreds():
        global gcreds_value
        foo = filedialog.askopenfilename(filetypes=[("Excel files", "*.json")])
        if foo is not None and foo != '':
            gcreds_value = foo
        gcreds_button.config(text=f"Retrieving gcreds from:\n{get_gcreds()}")

    popup = tk.Tk()
    popup.title("Instrumentation Update")
    # Get the screen width and height
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    # popup.config(background='navy')

    # Set the window dimensions to be half of the screen size
    window_width = screen_width // 2
    window_height = screen_height // 2

    # Calculate the position of the window to be centered on the screen
    window_x = (screen_width - window_width) // 2
    window_y = (screen_height - window_height) // 2

    # Set the window dimensions and position
    popup.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")

    file_button = tk.Button(popup, text="Select File", height=2, width=30, font=("Helvetica", 24), command=lambda: set_selected_value(
        filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])))
    file_button.pack(padx=10, pady=10)

    url_button = tk.Button(popup, text="Google Sheet URL", height=2, width=30, font=("Helvetica", 24), command=lambda: set_selected_value(
        simpledialog.askstring("Input", "Enter the URL of the Google Sheet")))
    url_button.pack(padx=10, pady=10)

    name_button = tk.Button(popup, text="Google Sheet by Name", height=2, width=30, font=("Helvetica", 24), command=lambda: set_selected_value(
        simpledialog.askstring("Input", "Enter the name of the Google Sheet")))
    name_button.pack(padx=10, pady=10)

    global confirm_button
    confirm_button = tk.Button(popup, text=f"Click to confirm source:\n{get_selected_value()}", height=3, width=60, font=("Helvetica", 18), command=lambda: clear_popup())
    confirm_button.configure(highlightbackground='green2')
    confirm_button.pack(padx=20, pady=20)

    global gcreds_button
    gcreds_button = tk.Button(popup, text=f"Retrieving gcreds from:\n{get_gcreds()}", height=2, width=60, font=("Helvetica", 18), command=lambda: choose_gcreds())
    gcreds_button.pack(padx=20, pady=10)

    popup.mainloop()

    print(f"Running instrumentation updates from [yellow]{get_selected_value()}[/yellow]")
    if get_gcreds():
        print(f"Using gcreds from [yellow]{get_gcreds()}[/yellow]")
    return get_selected_value(), get_gcreds()


def pure_instrument(sheet: str | None, client: sy.Synnax, gcreds: str | None = None):
    if ".xlsx" in sheet:
        data = process_excel(sheet)
    elif "docs.google.com" in sheet:
        data = process_url(sheet, gcreds)
    else:
        data = process_name(sheet)

    active = client.ranges.retrieve_active()
    if active is None:
        active = prompt_active_range(client)
        if active is None:
            print(f"""[red] Cannot proceed without a configured active range. [/red]""")
            return

    ctx = Context(
        client=client, active_range=active, indexes={}
    )

    if ctx.active_range is None:
        print(
            """[red]Active Range not found - aborting[/red]"""
        )
        raise "ActiveRangeNotFound"

    create_device_channels(ctx)
    existing_ports = {}
    for index, row in data.iterrows():
        process_row(ctx, index, row)
    client.ranges.set_active(active.key)


def prompt_active_range(client: sy.Synnax) -> sy.Range | None:
    print(f"""[orange]No active active range found in the Synnax cluster.""")
    if not Confirm.ask(f"""[blue]Would you like to create a new active range?[/blue]"""):
        return None
    name = Prompt.ask(f"""[blue]What would you like to name the new active range?[/blue]""")
    rng = client.ranges.create(
        name=name,
        time_range=sy.TimeRange(
            start=sy.TimeStamp.now(),
            end=sy.TimeStamp.now() + 1 * sy.TimeSpan.HOUR,
        ),
    )
    client.ranges.set_active(rng.key)
    return rng


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


def process_row(ctx: Context, index: int, row: dict, ports: dict):
    type_ = row[TYPE_COL]
    port, ok = get_port(index, row, Device, type_)
    if not ok:
        return
    if ports.get(port) is not None:
        print(
            f"""[purple]Row {index} - [/purple][red]Port {port} is already in use by channel {ports.get(port)} and was not updated.[/red]"""
        )
        return
    else:
        ports[port] = row[ALIAS_COL]
    if type_ == VLV_TYPE:
        return process_valve(ctx, index, row, port)
    if type_ == PT_TYPE:
        return process_pt(ctx, index, row, port)
    if type_ == TC_TYPE:
        return process_tc(ctx, index, row, port)
    if type_ == LC_TYPE:
        return process_lc(ctx, index, row)

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


def get_port(index: int, row: dict, device: Device, type_: str) -> (int, bool):
    port = row[PORT_COL]
    try:
        port = int(port)
    except ValueError:
        print(
            f"""[red]Invalid port number '{port}' in row {index}[/red]\n[blue]Value must be a positive integer[/blue]"""
        )
        return -1, False
    if type_ == VLV_TYPE:
        port += VALVE_AI_PORT_OFFSET
        if port not in VALID_VALVE_PORTS:
            print(
                f"""[red]Invalid port number for {device} '{port}' in row {index}[/red]\n[blue]Valid ports are {VALID_VALVE_PORTS}[/blue]"""
            )
        return port, True
    elif type_ == PT_TYPE:
        if port + PT_PORT_OFFSET not in PT_VALID_PORTS:
            print(
                f"""[red]Invalid port number for {device} '{port}' in row {index}[/red]\n[blue]Valid ports are {PT_VALID_PORTS}[/blue]"""
            )
        # had to hard-code in port 36 because it is mapped to 60, idk why
        if port == 36:
            return 60 + PT_PORT_OFFSET, True
        return port + PT_PORT_OFFSET, True
    elif type_ == TC_TYPE:
        port += TC_PORT_OFFSET
        if port not in TC_VALID_PORTS:
            print(
                f"""[red]Invalid port number for {device} '{port}' in row {index}[/red]\n[blue]Valid ports are {TC_VALID_PORTS}[/blue]"""
            )
        return port, True
    elif type_ == LC_TYPE:
        print(
            f"""[yellow]LC types not implemented yet[/yellow]"""
        )
        return -1, False
    else:
        print(
            f"""[red]Unable to retrieve port - invalid sensor type in row {index}[/red]"""
        )
        return -1, False


def create_device_channels(ctx: Context) -> (dict, bool):
    res = ctx.client.channels.create(
        [GSE_AI_TIME, GSE_DI_TIME, GSE_DOA_TIME], retrieve_if_name_exists=True
    )
    ctx.indexes["gse_ai"] = res[0]
    ctx.indexes["gse_di"] = res[1]
    ctx.indexes["gse_doa"] = res[2]

    analog_inputs = [
        sy.Channel(
            name=f"gse_ai_{i}",
            data_type=sy.DataType.FLOAT32,
            index=ctx.indexes["gse_ai"].key,
        ) for i in range(1, 81)
    ]
    digital_inputs = [
        sy.Channel(
            name=f"gse_di_{i}",
            data_type=sy.DataType.FLOAT32,
            index=ctx.indexes["gse_di"].key,
        ) for i in range(1, 33)
    ]
    client.channels.create(analog_inputs, retrieve_if_name_exists=True)
    client.channels.create(digital_inputs, retrieve_if_name_exists=True)
    digital_command_times = [
        sy.Channel(
            name=f"gse_doc_{i}_time",
            data_type=sy.DataType.TIMESTAMP,
            is_index=True,
        ) for i in range(1, 33)
    ]
    digital_command_times = client.channels.create(digital_command_times, retrieve_if_name_exists=True)
    digital_commands = [
        sy.Channel(
            name=f"gse_doc_{i}",
            data_type=sy.DataType.UINT8,
            index=digital_command_times[i - 1].key,
        ) for i in range(1, 33)
    ]
    client.channels.create(digital_commands, retrieve_if_name_exists=True)
    digital_output_acks = [
        sy.Channel(
            name=f"gse_doa_{i}",
            data_type=sy.DataType.UINT8,
            index=ctx.indexes["gse_doa"].key,
        ) for i in range(1, 33)
    ]
    client.channels.create(digital_output_acks, retrieve_if_name_exists=True)


# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# |||||||||||||||||||||||||||||||||||||||||||||||||||| VALVES ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

VALVE_AI_PORT_OFFSET = 36
VALID_VALVE_PORTS = range(1, 33) # cringe


def process_valve(ctx: Context, index: int, row: dict, port: int):
    # get the device name
    device, ok = get_device(index, row)
    if not ok:
        return

    print(
        f"[purple]Row {index} - [/purple][blue]Configuring valve {port - VALVE_AI_PORT_OFFSET} on {device} port {port}[/blue]"
    )

    ack_channel = sy.Channel(
        name=f"gse_doa_{port - VALVE_AI_PORT_OFFSET}",
        data_type=sy.DataType.UINT8,
        index=ctx.indexes["gse_doa"].key,
    )
    i_channel = sy.Channel(
        name=f"gse_ai_{port}",
        data_type=sy.DataType.FLOAT32,
        index=ctx.indexes["gse_ai"].key
    )
    v_channel = sy.Channel(
        name=f"gse_di_{port - VALVE_AI_PORT_OFFSET}",
        data_type=sy.DataType.FLOAT32,
        index=ctx.indexes["gse_di"].key,
    )
    input_channels = [ack_channel, i_channel, v_channel]
    retrieved_channels = []
    for channel in input_channels:
        try:
            retrieved_channel = ctx.client.channels.create(channel, retrieve_if_name_exists=True)
            retrieved_channels.append(retrieved_channel)
            if retrieved_channel.data_type != channel.data_type:
                print(
                    f"""[purple]Row {index} - [/purple][red]Was expecting data_type {channel.data_type}, but found a channel with data_type {retrieved_channel.data_type}[/red]"""
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

    ctx.active_range.meta_data.set({
        f"{i_channel.name}_type": "VLV",
    })


# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# ||||||||||||||||||||||||||||||||||||||||||||| PRESSURE TRANSDUCERS |||||||||||||||||||||||||||||||||||||||||||||||||||
# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

PT_VALID_PORTS = range(1, 38)
PT_MAX_OUTPUT_VOLTAGE = 4.5
PT_OFFSET = 0.5


def pt_analog_port(port: int) -> int:
    if port == 37:
        return 61
    return port


def process_pt(ctx: Context, index: int, row: dict):
    # get the device name
    device, ok = get_device(index, row)
    if not ok:
        return False

    print(
        f"[purple]Row {index} - [/purple][blue]Configuring PT {port - PT_PORT_OFFSET} on {device} port {port}[/blue]"
    )

    name = f"{device}_ai_{port}"

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
    opt_offset = row[OPT_PT_OFFSET_COL]
    opt_slope = row[OPT_PT_SLOPE_COL]
    # check if its non nan, NOT an empty stringja
    if opt_slope != "" and not math.isnan(opt_slope):
        try:
            print(f"""[blue]Using optional PT slope '{opt_slope}' for {device} pressure transducer {port}[/blue]""")
            slope = float(opt_slope)
        except ValueError:
            print(
                f"""[red]Invalid value for PT slope '{opt_slope}' for {device} pressure transducer {port}[/red]\n[blue]Value must be a positive number[/blue]"""
            )
            return False
    else:
        try:
            max_pressure = float(max_pressure)
            slope = max_pressure / (PT_MAX_OUTPUT_VOLTAGE - PT_OFFSET)
        except ValueError:
            print(
                f"""[red]Invalid value for PT max pressure '{max_pressure}' for {device} pressure transducer {port}[/red]\n[blue]Value must be a positive number[/blue]"""
            )
            return False

    if opt_offset != "" and not math.isnan(opt_offset):
        try:
            print(f"""[blue]Using optional PT offset '{opt_offset}' for {device} pressure transducer {port}[/blue]""")
            offset = float(opt_offset)
        except ValueError:
            print(
                f"""[red]Invalid value for PT offset '{opt_offset}' for {device} pressure transducer {port}[/red]\n[blue]Value must be a positive number[/blue]"""
            )
            return False
    else:
        offset = PT_OFFSET

    try:
        ctx.active_range.meta_data.set({
            f"{name}_type": "PT",
            f"{name}_pt_slope": slope,
            f"{name}_pt_offset": offset,
        })
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
TC_VALID_PORTS = range(1, 17)


def process_tc(ctx: Context, index: int, row: dict, port: int):
    # get the device name
    device, ok = get_device(index, row)
    if not ok:
        return False

    print(
        f"[purple]Row {index} - [/purple][blue]Configuring TC {port} on {device} port {port + TC_PORT_OFFSET}[/blue]"
    )

    name = f"{device}_ai_{port}"

    ch = sy.Channel(
        name=name,
        data_type=sy.DataType.FLOAT32,
        index=ctx.indexes["gse_ai"].key,
    )

    try:
        ctx.client.channels.create(ch, retrieve_if_name_exists=True)
    except Exception as e:
        print(
            f"""[red]Failed to retrieve channel for {device} thermocouple {port}[/red]\n Error: {e}"""
        )
        return False

    if ch.data_type != sy.DataType.FLOAT32:
        print(
            f"""[orange]Invalid data type for {device} thermocouple {port} - should be FLOAT32.[/orange]"""
        )

    tc_type = TC_DEFAULT_VAL
    tc_offset = str(row[TC_OFFSET_COL]).rstrip()
    if len(tc_offset) == 0:
        print(
            f"[orange]Invalid value for TC offset '{tc_offset}' in row {index}[/orange]"
            f"\n[blue]We'll use the default value of 0[/blue]"
        )
        tc_offset = 0

    try:
        ctx.active_range.meta_data.set(

            {
                f"{name}_type": "TC",
                f"{name}_tc_type": tc_type,
                f"{name}_tc_offset": tc_offset,
            }
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
        return False

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


LC_PORT_OFFSET = 60


def process_lc(ctx: Context, index: int, row: dict):
    # get the device name
    device, ok = get_device(index, row)
    if not ok:
        return False

    # get the port number
    port, ok = get_port(index, row, device)
    if not ok:
        return False

    # if port not in TC_VALID_PORTS:
    #     print(
    #         f"""[red]Load cells can only be connected to ports {TC_VALID_PORTS}[/red]"""
    #     )
    #     return False

    print(
        f"[purple]Row {index} - [/purple][blue]Configuring LC {port} on {device} port {LC_PORT_OFFSET + port}[/blue]"
    )

    port += LC_PORT_OFFSET

    name = f"{device}_ai_{port}"

    sy.Channel(
        name=name,
        data_type=sy.DataType.FLOAT32,
        index=ctx.indexes["gse_ai"].key,
    )

    try:
        ctx.active_range.meta_data.set(
            {
                f"{name}_type": "LC",
            }
        )
    except Exception as e:
        print(
            f"""
        [red]Failed to set load cell type and offset for {device} load cell {port}[/red]
        [blue]Error: {e}[/blue
        """)
