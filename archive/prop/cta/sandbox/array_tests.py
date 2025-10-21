# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 12:41:33 2024

@author: Nate Campbell
"""

import numpy as np

r_vals = np.array(['r{},'.format(x) for x in range(4)],dtype=object)
th_vals = np.array(['th{},'.format(x) for x in range(4)],dtype=object)
x_vals = np.array(['x{}'.format(x) for x in range(4)],dtype=object)

print(r_vals)
print(th_vals)
print(x_vals)

a = r_vals[:,np.newaxis,np.newaxis] + th_vals[np.newaxis,:,np.newaxis] \
    + x_vals[np.newaxis,np.newaxis,:]
    
x_mat = x_vals[np.newaxis,np.newaxis,:]
    
print('a:\n',a)

print('r0:\n',a[0])

print('th0:\n', a[:,0])

print('x:\n', x_mat)



