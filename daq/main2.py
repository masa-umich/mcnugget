import synnax as sy
from synnax.hardware import ni

client = sy.Synnax(
    host="masasynnax.ddns.net",
    port=9090,
    username="synnax",
    password="seldon"
)

analog_card = client.hardware.devices.retrieve(name="PCI-6225")
digital_card = client.hardware.devices.retrieve(name="PCI-6514")

# Timestamp channel
gse_ai_time = client.channels.create(
    name="gse_ai_time",
    is_index=True,
    data_type=sy.DataType.TIMESTAMP,
    retrieve_if_name_exists=True,
)

# create analog read task
analog_task = ni.AnalogReadTask(
    name="Analog Read Task",
    sample_rate=sy.Rate.HZ * 50,
    stream_rate=sy.Rate.HZ * 10,
    data_saving=True,
    channels=[]
)

# create digital read task
digital_read_task = ni.DigitalReadTask(
    name="Digital Read Task",
    device=digital_card.key,
    sample_rate=sy.Rate.HZ * 50,
    stream_rate=sy.Rate.HZ * 10,
    data_saving=True,
    channels=[]
)

# Create digital write task
digital_write_task = ni.DigitalWriteTask(
    name="Digital Write Task",
    device=digital_card.key,
    state_rate=sy.Rate.HZ * 50,
    data_saving=True,
    channels=[]
)

client.hardware.tasks.configure(analog_task)
client.hardware.tasks.configure(digital_read_task)
client.hardware.tasks.configure(digital_write_task)


