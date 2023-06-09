import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
from class_init import Regen_Channel
from class_init import Liner
import numpy as np
import pint
import pandas as pd

fuel = pd.read_csv('rp1.csv', sep=',')


