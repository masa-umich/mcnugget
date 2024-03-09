# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 15:11:05 2024

@author: Nate Campbell
"""

import thermal_fem as tfem
import numpy as np
import matplotlib.pyplot as plt

!CLS

model = tfem.Model()

model.set_r_numel(3)
model.set_theta_numel(6)
model.set_x_numel(2)

model.make_revolve(
    r1=lambda x: np.zeros(x.shape)+1,
    r2=lambda x: np.zeros(x.shape)+2,
    x1=1,x2=2,
    theta1=0,theta2=np.pi/2,
    material='C18150',name='rev0'
    )

print(model.bodies['rev0'].faces)
print(model.node_connect)
print('areas:\n',model.bodies['rev0'].areas)

plt.close('all')
model.plot_mesh()
model.make_convection('rev0','r-',h=lambda x: 100,T=lambda x: 400)
model.make_convection('rev0','r+',h=lambda x: 10, T=lambda x: 300)
model.solve()

print('T', model.T)








