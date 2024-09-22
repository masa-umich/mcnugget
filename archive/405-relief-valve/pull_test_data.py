import synnax as sy
from mcnugget.client import client
import csv
import pandas as pd
import matplotlib.pyplot as plt

# Create named ranges for previous tests
test1 = client.ranges.create(
    name="405-test1-4-18-2024",
    time_range=sy.TimeRange(1713485601895225856, 1713485728059025664)
)


test2 = client.ranges.create(
    name="405-test2-4-18-2024",
    time_range=sy.TimeRange(1713489661570824192, 1713489678802247936)
)

test3 = client.ranges.create(
    name="405-test3-4-18-2024",
    time_range=sy.TimeRange(1713490222562735872, 1713490239599087104)
)

# Extract data
data1 = {
    "time": pd.DataFrame(test1.gse_ai_time),
    "pt1": pd.DataFrame(test1.gse_ai_1),
    "pt2": pd.DataFrame(test1.gse_ai_2),
    "pt3": pd.DataFrame(test1.gse_ai_3)
}

data2 = {
    "time": pd.DataFrame(test2.gse_ai_time),
    "pt1": pd.DataFrame(test2.gse_ai_1),
    "pt2": pd.DataFrame(test2.gse_ai_2),
    "pt3": pd.DataFrame(test2.gse_ai_3)
}

data3 = {
    "time": pd.DataFrame(test3.gse_ai_time),
    "pt1": pd.DataFrame(test3.gse_ai_1),
    "pt2": pd.DataFrame(test3.gse_ai_2),
    "pt3": pd.DataFrame(test3.gse_ai_3)
}


df1 = pd.concat([data1["time"], data1["pt1"], data1["pt2"], data1["pt3"]],axis=1)
df2 = pd.concat([data2["time"], data2["pt1"], data2["pt2"], data2["pt3"]],axis=1)
df3 = pd.concat([data3["time"], data3["pt1"], data3["pt2"], data3["pt3"]],axis=1)

column_names = ["time", "pt1", "pt2", "pt3"]
df1.columns = column_names
df2.columns = column_names
df3.columns = column_names

# Save to CSV
filename1 = "405-relief-valve-4-18-2024-test1.csv"
filename2 = "405-relief-valve-4-18-2024-test2.csv"
filename3 = "405-relief-valve-4-18-2024-test3.csv"

df1.to_csv(filename1, sep=",", index=False)
df2.to_csv(filename2, sep=",", index=False)
df3.to_csv(filename3, sep=",", index=False)
