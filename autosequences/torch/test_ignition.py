# quick checks for the ignition detection logic 
# uv run python test_ignition.py
from torch_auto import check_overpressure, evaluate_ignition
  
LOWER, UPPER, VOTE = 165, 242, 20

assert evaluate_ignition([200, 201, 199], VOTE, LOWER, UPPER)[0] is True    # good ignition
assert evaluate_ignition([200, 201, 900], VOTE, LOWER, UPPER)[0] is True    # one bad PT gets voted out
assert evaluate_ignition([150, 151, 149], VOTE, LOWER, UPPER)[0] is False   # cold flow / no ignition
assert evaluate_ignition([250, 251, 249], VOTE, LOWER, UPPER)[0] is False   # over the upper bound
assert evaluate_ignition([], VOTE, LOWER, UPPER) == (False, None)           # no data = not ignited
assert evaluate_ignition([165, 165, 165], VOTE, LOWER, UPPER)[0] is True    # bounds are inclusive

assert check_overpressure([193, 194, 192], VOTE, 333)[0] is False           # nominal
assert check_overpressure([350, 351, 349], VOTE, 333)[0] is True            # overpressure
assert check_overpressure([193, 194, 900], VOTE, 333)[0] is False           # one bad PT voted out
assert check_overpressure([333, 333, 333], VOTE, 333)[0] is False           # threshold is strict
assert check_overpressure([400], VOTE, 333)[0] is True                      # one available PT trips
assert check_overpressure([], VOTE, 333) == (False, None)                    # no data
print("All ignition tests passed")
