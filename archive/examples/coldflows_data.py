import synnax as sy
from mcnugget.client import client
import pandas
from datetime import datetime
import time

rng = client.ranges.retrieve("March 16-17 Coldflows")
#start = datetime.datetime("2024-3-17 19:00:00")
start = datetime(2024, 3, 17, 19, 20)
end = datetime(2024, 3, 17, 19, 50)
#end = datetime.datetime("2024-3-17 20:00:00")

channels = client.channels.retrieve(["gse_ai_time", "gse_ai_3", "gse_ai_4", "gse_ai_35", "gse_ai_22", "gse_ai_24", "gse_ai_26", "gse_ai_12", "gse_ai_13"])

data = channels.read(start, end)
pd_data = pandas.DataFrame(data)
filename = "csvtest.csv"
pd_data.to_csv(filename, sep="\t")

time.sleep(10)
pt3 = rng.gse_ai_3
pt4 = rng.gse_ai_4
pt35 = rng.gse_ai_35
pt22 = rng.gse_ai_22
pt24 = rng.gse_ai_24
pt26 = rng.gse_ai_26
doc25 = rng.gse_doc_25
doc26 = rng.gse_doc_26
pt12 = rng.gse_ai_12
pt13 = rng.gse_ai_13
time = rng.gse_ai_time
pt35df = pandas.DataFrame(pt35)
pt3df = pandas.DataFrame(pt3)
pt4df = pandas.DataFrame(pt4)
pt22df = pandas.DataFrame(pt22)
pt24df = pandas.DataFrame(pt24)
pt26df = pandas.DataFrame(pt26)
#doc25df = pandas.DataFrame(doc25)
#doc26df = pandas.DataFrame(doc26)
pt12df = pandas.DataFrame(pt12)
pt13df = pandas.DataFrame(pt13)
timedf = pandas.DataFrame(time)
filename = "coldflows_march_17.csv"
df = pandas.concat([timedf, pt3df, pt4df, pt35df, pt22df, pt24df, pt26df, pt12df, pt13df], axis=1)
column_names = ["time", "pt3", "pt4", "pt35", "pt22", "pt24", "pt26", "pt12", "pt13"]
df.columns = column_names
df.to_csv(filename, sep="\t")

