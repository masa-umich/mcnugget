from mcnugget.client import client
import synnax as sy

tr = sy.TimeRange(1707070832631803000, 1707070845348109600)
print(tr.start)

data = client.read(tr, "gse_ai_time")
print(tr.span)
print(data.time_range.span, sy.TimeSpan(len(data)/200 * sy.TimeSpan.SECOND))