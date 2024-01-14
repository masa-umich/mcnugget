# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 19:30:13 2024

@author: natecamp
"""

import numpy as np
import pandas as pd
import thermal_fem as tfem

class Model:
    '''A class representing a finite element thermal model of a thrust chamber.
    
    '''
    
    def __init__(self, input_fname):
        # read in the input sheet
        input_tbl = pd.read_excel(input_fname,sheet_name='inputs',
                                  usecols=['variable','value'])
        # assign the variables of the input table to the object
        for v in range(input_tbl.shape[0]):
            setattr(self, input_tbl.loc[v,'variable'], input_tbl.loc[v,'value'])
        # initialize the finite element model    
        self.model = tfem.Model
        # calculate other geometry values
        self.calc_geometry
        
            
    def setup(self):
        self.model.generate_mesh
        self.model.build_system
        
    def solve(self):
        self.model.solve
        # update coolant temperatures
        # update heat transfer coefficients
    
    def generate_mesh(self):
        '''Builds the mesh.'''
        # call make_solid to make the bodies
        # the meshing algorithm should already have default size controls, 
        # so won't specify number of divisions in each call
        
        # set the mesh divisions
        # TODO: set list of angular divisions to line up the liner/jacket with 
        # the fins
        divs_fin_start = np.linspace(0,2*np.pi-1/self.n_fin,self.n_fin)
        divs_fin_end = divs_fin_start+self.dtheta_fin
        self.model.set_theta_divs(sorted(np.concatenate(
            divs_fin_start,divs_fin_end
            )))
        
        # liner
        self.model.make_solid('revolve',r1=lambda x: self.r_liner_in(x),
                              r2=lambda x: self.r_liner_out(x),
                              x1=0,x2=self.L_c+self.L_n,
                              material='C18150')
        # jacket
        self.model.make_solid('revolve',r1=lambda x: self.r_jacket_in(x),
                              r2=lambda x: self.r_jacket_out(x),
                              x1=0,x2=self.L_c+self.L_n,
                              material='Al6061')
        # fins
        # iterate over each fin
        for n in range(self.n_fin):
            self.model.make_solid('revolve',r1=lambda x: self.r_liner_out(x),
                                  r2=lambda x: self.r_jacket_in(x),
                                  x1=0,x2=self.L_c+self.L_n,
                                  theta1=n*2*np.pi/self.n_fin,
                                  theta2=n*2*np.pi/self.n_fin+self.dtheta_fin,
                                  material='C18150')
        # now the mesh should be complete


        
                
    
    def build_system(self):
        # contacts
        
        # 
        pass
    
    def calc_geometry(self):
        '''Sets geometry parameters derived from the primary inputs.'''
        # length of the chamber cylinder
        self.L_cyl = np.nan
        # location of start of nozzle bell
        self.x_bell_start = np.nan
        # angular width of fin
        self.dtheta_fin = np.nan
        
    def r_liner_in(self,x):
        '''Returns the radius of the inner liner wall at the given location'''
        pass
    
    def r_liner_out(self,x):
        '''Returns the radius of the liner outer wall at the given location'''
        pass
    
    def r_jacket_in(self,x):
        '''Returns the radius of the inner jacket wall at the given location'''
        pass
    
    def r_jacket_out(self,x):
        '''Returns the radius of the outer jacket wall at the given location'''
        pass
    
    
    
            
            
        
        
    
    

