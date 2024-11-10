# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 22:26:06 2024

@author: Nate Campbell
"""

import numpy as np

a = np.array([[1,2,3],[4,5,6],[7,8,9]])

print(a)

b = a**2

print(b)

a[a<5] = b[a<5]/2

print(a)

print(a/b)



