import synnax
import time
import random

client = synnax.Synnax()

# READ = ["gse_pt_1", "gse_ai_time"]

# WRITE = ["gse_pt_1_avg", "gse_average_time"]

# with client.open_streamer(READ) as streamer:
#     with client.open_writer(synnax.TimeStamp.now(), WRITE, 20, enable_auto_commit=True) as writer:
#         time.sleep(0.1)
#         while True:
#             frame = streamer.read(0.01)
#             if frame is None:
#                 continue
#             pt = frame["gse_pt_1"][-1]
#             pt_time = frame["gse_ai_time"][-1]
#             print(pt)
#             print(pt_time)
#             print(writer.write(
#                 {
#                     "gse_pt_1_avg": pt + 10,
#                     1049396: pt_time,
#                 }
#             ))

# with client.open_writer(synnax.TimeStamp.now(), ["gse_pt_1_a", "true_average_time"], 20, enable_auto_commit=True) as writer:

print(client.channels.retrieve("gse_pt_1"), client.channels.retrieve("gse_pt_1").index)
print(client.channels.retrieve("gse_ai_time"), client.channels.retrieve("gse_ai_time").index)
print(client.channels.retrieve("gse_pt_1_a"), client.channels.retrieve("gse_pt_1_a").index)
print(client.channels.retrieve("true_average_time"), client.channels.retrieve("true_average_time").index)

# with client.open_streamer(["gse_pt_1_a", "true_average_time"]) as streamer:
# with client.open_streamer(["gse_pt_1", "gse_ai_time"]) as streamer:
with client.control.acquire(
    "testing", ["gse_pt_1_a", "true_average_time"], [], 5
) as auto:
    time.sleep(0.1)
    while True:
        print(auto["gse_pt_1_a"])
        print(auto["true_average_time"])
        # if frame is None:
        #     continue
        # pt = frame["gse_pt_1_a"][-1]
        # pt_time = frame["true_average_time"][-1]
        # print(pt)
        # print(pt_time)
        # writer.write(
        #     {
        #         "gse_pt_1_a": random.uniform(0, 100),
        #         "true_average_time": synnax.TimeStamp.now(),
        #     }
        # )
        # time.sleep(0.1)