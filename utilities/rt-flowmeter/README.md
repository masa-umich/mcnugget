# Real-time Venturi Flowmeter Calculations
This script reads in flowmeter inlet and outlet pressures and temperatures, then with the data provided in `config.json` calculates the flowrate in kg/s and writes that data into Synanx. An example configuration can be found in `example_config.json`. This script assumes a Venturi flowmeter and a known geometry & fluid. This is a work-in-progress.

This is different than the script found in `autosequences/scripts/flowmeter.py`, sorry for the confusing names lol

## Development
- Use the program refprop as a look-up table for fluid densities
- Find out how to calculate flowrates by asking in #nostupidquestions
- Reference old flowmeter calculation code in `mcnugget/autosequences/scripts/flowmeter.py`