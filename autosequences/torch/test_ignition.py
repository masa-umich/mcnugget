# quick checks for the ignition detection logic 
# uv run python test_ignition.py
from torch_auto import evaluate_ignition
  
LOWER, UPPER, VOTE = 165, 242, 20

assert evaluate_ignition([200, 201, 199], VOTE, LOWER, UPPER)[0] is True    # good ignition
assert evaluate_ignition([200, 201, 900], VOTE, LOWER, UPPER)[0] is True    # one bad PT gets voted out
assert evaluate_ignition([150, 151, 149], VOTE, LOWER, UPPER)[0] is False   # cold flow / no ignition
assert evaluate_ignition([250, 251, 249], VOTE, LOWER, UPPER)[0] is False   # over the upper bound
assert evaluate_ignition([], VOTE, LOWER, UPPER) == (False, None)           # no data = not ignited
assert evaluate_ignition([165, 165, 165], VOTE, LOWER, UPPER)[0] is True    # bounds are inclusive
print("All ignition tests passed")