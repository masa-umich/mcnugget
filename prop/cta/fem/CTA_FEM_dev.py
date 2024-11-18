# -*- coding: utf-8 -*-
"""
Created on Sat Jan 13 14:18:49 2024

@author: natecamp
"""

import numpy as np
import pandas as pd

input_fname = "input_sheets/cta_fem_input_0.xlsx"

input_tbl = pd.read_excel(input_fname,sheet_name='inputs',
                          usecols=['variable','value'])

inputs = {}

for v in range(input_tbl.shape[0]):
   inputs[input_tbl.loc[v,'variable']] = input_tbl.loc[v,'value']
   


