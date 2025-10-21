import synnax
import time
import random

client = synnax.Synnax()

tc_channel = client.channels.retrieve("gse_tc_1_raw")
tc_write_channel = client.channels.retrieve("gse_tc_1")
ai_time_channel = client.channels.retrieve("gse_ai_time")
# tc_index = client.channels.retrieve(tc_channel.index.key)

# print(tc_channel.key)

print(f"tc_channel key {tc_channel.index} == ai_time_channel key {ai_time_channel.key}")
