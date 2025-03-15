# things to check before running hotfire_new.py

* prevalves or MPVs before fire?
* prepress target pressures
* when Iso valves open
* fuel/ox only?
* any recent adjustments to channel assignments?
* fire duration

# are your scripts running?

* average_all.py in /autosequences/scripts
* thermo_magic.py in /daq
* flowmeter.py in /autosequences/scripts

# have you been a responsible SRE?

* communicated status of autosequence to TC?
* tested each abort contingency of the autosequence yourself?
* done a dry run of the autosequence (nominal, prepress abort, hotfire abort)?
* eaten at least one glazed donut?

One time I pressed a button and it caused a massive explosion that cost the team months of work, not to mention tens of thousands of dollars. While it wasn't my fault, there were things I could have done to reduce the chances of an off-nominal outcome.

If you have concerns, speak up.