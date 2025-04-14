import synnax

client = synnax.Synnax()
SAMPLES = 5

frames = []
with client.open_streamer(["gse_thermistor_signal", "gse_ai_time"]) as streamer:
    for i in range(SAMPLES):
        frames.append(streamer.read())

pt_samples = {}
total_samples = 0
for frame in frames:
    if frame is None:
        print('empty frame')
        continue
    for i in range(5):
        pt = frame["gse_thermistor_signal"][i]
        time = frame["gse_ai_time"][i]
        if pt_samples.get(pt) is None:
            pt_samples[pt] = []
        pt_samples[pt].append(time)
        total_samples += 1

# for pt_reading, timestamp in pt_samples.items():
#     if len(timestamp) > 1:
#         print(f"read value {pt_reading} at {timestamp}")

# print()
probability_of_duplicate = 1 - len(list(pt_samples.keys())) / total_samples
print(f"testing over {SAMPLES} samples")
print(f"probability of reading value multiple times: {probability_of_duplicate}")