# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 21:19:29 2024

@author: Nate Campbell
"""

import numpy as np

# make a 2x3x4 matrix

d1 = (np.linspace(0,1,2)+np.zeros((3,4,2))).transpose((2,0,1))
d2 = (np.linspace(0,0.2,3)+np.zeros((4,2,3))).transpose((1,2,0))
d3 = (np.linspace(0,0.03,4)+np.zeros((2,3,4))).transpose((0,1,2))

print(d1+d2+d3)
