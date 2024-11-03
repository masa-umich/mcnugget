import pandas as pd
import sys
import matplotlib.pyplot as plt
import synnax as sy
import time
import dask.dataframe as dd
from dask.diagnostics import ProgressBar

times = []
start = time.time()
ProgressBar().register()
times.append(time.time())
print("setup completed")

df = pd.read_csv('/Users/evanhekman/masa/ai_data_filtered_backup.csv', header=None, engine="python")
times.append(time.time())
print("read completed")

# print(df)

headers = df[0]
del df[0]
times.append(time.time())
print("column extraction completed")

filter_rows = df.iloc[-1, :]
# filter_condition = df.iloc[-1, :] > 1715754150000000000 < 1715757880000000000
filter_condition = filter_rows.between(1715754150000000000, 1715757880000000000)
times.append(time.time())
print("filter setup completed")

filtered_df = df.loc[:, filter_condition]
times.append(time.time())
print("filtering completed")

filtered_df.insert(0, 0, headers)
times.append(time.time())
print("header reinsertion completed")

times.append(time.time())
filtered_df.to_csv("~/masa/ai_data_filtered.csv", index=False)
print("save completed")

# print(filtered_df)

times.append(time.time())
print("thank god")
for t in times:
    print(t - start)
