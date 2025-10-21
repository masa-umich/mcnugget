import matplotlib.pyplot as plt
from mcnugget.client import client
import synnax as sy
from datetime import datetime

# Start is March 16 at 4pm

tr =sy.TimeRange(1710611641818236700, 1710635502843300600)
print(tr)

data = client.read(tr, ["gse_ai_3", "gse_ai_time"])

start = None
end = None
ai_1 = []
time = []
for i, v in enumerate(data.columns):
    if v == "gse_ai_3":
        s = data.series[i]
        ai_1.append(s)
        if start is None:
            start = s.time_range.start
        end = s.time_range.end
    else:
        s = data.series[i]
        time.append(s)

        # print(s.time_range, len(s))

for i, v in enumerate(ai_1):
    plt.plot(time[i].to_datetime(), v)

plt.show()