# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 15:11:05 2024

@author: Nate Campbell
"""

import thermal_fem as tfem
import numpy as np
import matplotlib.pyplot as plt

def main():
    plt.close('all')
    single_cyl_test()
    # multi_cyl_test()

def single_cyl_test():
    model = tfem.Model()
    
    model.set_r_numel(3)
    model.set_theta_numel(3)
    model.set_x_numel(20)
    
    model.make_revolve(
        r1=lambda x: np.zeros(x.shape)+1,
        r2=lambda x: np.zeros(x.shape)+2,
        x1=1,x2=2,
        theta1=lambda x: np.zeros(x.shape),
        theta2=lambda x: np.zeros(x.shape)+np.pi/2,
        material='C18150',name='rev0'
        )
    
    # print(model.bodies['rev0'].faces)
    # print(model.node_connect)
    # print('areas:\n',model.bodies['rev0'].areas)
    
    fig,ax = model.plot_mesh()
    model.make_convection('rev0','r-',h=lambda x: 100,T=lambda x: 400)
    model.make_convection('rev0','r+',h=lambda x: 10, T=lambda x: 300)
    model.solve()
    model.export_to_xlsx('results/test.xlsx')
    
    q_rp = model.get_heat_flux('rev0','r+',1,1.5)
    q_rn = model.get_heat_flux('rev0','r-',1,2)
    q_thp = model.get_heat_flux('rev0','theta+',1,2)
    print('average r+ heat flux: q: {:.4f} W/m^2'.format(q_rp))
    print('average r- heat flux: q: {:.4f} W/m^2'.format(q_rn))
    print('average th+ heat flux: Q: {:.4f} W/m^2'.format(q_thp))
    
    
    # print('T', model.T)

def multi_cyl_test():
    model = tfem.Model()
    
    model.set_r_numel(2)
    model.set_theta_numel(2)
    model.set_x_numel(2)
    
    model.make_revolve(
        r1=lambda x: np.zeros(x.shape)+1,
        r2=lambda x: np.zeros(x.shape)+1.5,
        x1=1,x2=2,
        theta1=lambda x: np.zeros(x.shape),
        theta2=lambda x: np.zeros(x.shape)+np.pi/2,
        material='C18150',name='rev0'
        )
    model.make_revolve(
        r1=lambda x: np.zeros(x.shape)+1.5,
        r2=lambda x: np.zeros(x.shape)+2,
        x1=1,x2=2,
        theta1=lambda x: np.zeros(x.shape),
        theta2=lambda x: np.zeros(x.shape)+np.pi/2,
        material='C18150',name='rev1'
        )
    
    model.make_contact('rev0','rev1')
    
    fig,ax = model.plot_mesh()
    model.make_convection('rev0','r-',h=lambda x: 100,T=lambda x: 400)
    model.make_convection('rev1','r+',h=lambda x: 10, T=lambda x: 300)
    model.solve()
    model.export_to_xlsx('results/test.xlsx')
    
    q_rp = model.get_heat_flux('rev1','r+',1,2)
    q_rn = model.get_heat_flux('rev0','r-',1,2)
    q_thp = model.get_heat_flux('rev0','theta+',1,2)
    print('average r+ heat flux: q: {:.4f} W/m^2'.format(q_rp))
    print('average r- heat flux: q: {:.4f} W/m^2'.format(q_rn))
    print('average th+ heat flux: Q: {:.4f} W/m^2'.format(q_thp))
    
    # print('T', model.T)


if __name__ == '__main__':
    main()





