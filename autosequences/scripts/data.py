import synnax
import datetime

client = synnax.Synnax()

start = input("starting time: M D H M S: ")
start = start.split()
start = datetime.datetime(
    2024, int(start[0]), int(start[1]), int(start[2]), int(start[3]), int(start[4])
)
synnax_start = synnax.TimeStamp(start)

end = input("ending time: M D H M S: ")
end = end.split()
end = datetime.datetime(
    2024, int(end[0]), int(end[1]), int(end[2]), int(end[3]), int(end[4])
)
synnax_end = synnax.TimeStamp(end)
time_range = synnax.TimeRange(
    start=synnax_start,
    end=synnax_end,
)

channel_to_retrieve = input("channel: ")

channel = client.channels.retrieve(channel_to_retrieve)

file = input("file to write to: ")

# frame = client.read(time_range, [channel_to_retrieve])
# print(frame)
# print(frame.series)
# print(frame.__class__)
# print(frame.__dict__)

# with open(file, "w") as f:
#     data = channel.read(time_range)
#     for i in range(len(data)):
#         f.write(f"{data[i]}\n")
#     print(f"wrote {len(data)} samples to {file}")

with client.open_iterator(
    time_range, [channel], 500 * 60,
) as iterator:
    print(iterator.value)
    