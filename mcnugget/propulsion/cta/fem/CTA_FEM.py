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
        self.model = tfem.Model()
        # calculate other geometry values
        self.calc_geometry()
        # setup the model
        self.setup()
        # convergence tolerance
        self.tol = 0.1 # K
        # convection to ambient air from outside of jacket
        # TODO: find a source for these values
        self.h_amb = 1 # W/m^2-K
        self.T_amb = 300 # K
            
    def setup(self):
        self.generate_mesh()
        self.build_contacts()
        
    def solve(self):
        # set initial coolant temperatures
        self.init_cooling()
        # set the convection boundaries
        self.set_boundaries()
        # solve the wall temepratures
        self.model.solve()
        
        max_Tc = self.get_max_Tc()
        is_converged = False
        while not is_converged:
            prev_max_Tc = max_Tc
            # calculate the coolant temepratures
            self.update_cooling()
            max_Tc = self.get_max_Tc()
            
            # update the convection based on the new coolant temepratures
            self.set_boundaries()
            # resolve the wall temperatures
            self.model.solve()
            # determine convergence based on how much the maximum fuel 
            # temperature changed in the iteration
            is_converged = abs(max_Tc-prev_max_Tc) < self.tol
                
        # TODO: check that the model is converged, ideally based on the heat 
    
    def generate_mesh(self):
        '''Builds the mesh.'''
        # call make_solid to make the bodies

        # set the number of divisions in each solid
        self.model.set_r_numel(3)
        self.model.set_theta_numel(3)
        self.model.set_x_numel(20)
        
        # the liner and jacket are broken up into separate solids for the 
        # sections between and below each fin to help with applying convections
        # the fins are named finN for N from 0 to self.n_fin-1 
        # the liner and jacket solids above and below finN are linerN/jacketN
        # the liner and jacket solids to the +theta side of N are N.5
                
        # iterate over each fin
        for n in range(self.n_fin):
            # fin
            self.model.make_solid('revolve',r1=lambda x: self.r_liner_out(x),
                                  r2=lambda x: self.r_jacket_in(x),
                                  x1=0,x2=self.L_c+self.L_n,
                                  theta1=n*2*np.pi/self.n_fin,
                                  theta2=n*2*np.pi/self.n_fin+self.dtheta_fin,
                                  material='C18150',name='fin{}'.format(n))
            # liner below fin
            self.model.make_solid('revolve',r1=lambda x: self.r_liner_in(x),
                                  r2=lambda x: self.r_liner_out(x),
                                  x1=0,x2=self.L_c+self.L_n,
                                  theta1=n*2*np.pi/self.n_fin,
                                  theta2=n*2*np.pi/self.n_fin+self.dtheta_fin,
                                  material='C18150',name='liner{}'.format(n))
            # liner between fins
            self.model.make_solid('revolve',r1=lambda x: self.r_liner_in(x),
                              r2=lambda x: self.r_liner_out(x),
                              x1=0,x2=self.L_c+self.L_n,
                              theta1=n*2*np.pi/self.n_fin+self.dtheta_fin,
                              theta2=np.mod(n+1,self.n_fin)*2*np.pi/self.n_fin,
                              material='C18150',name='liner{}'.format(n+0.5))
            # jacket above fin
            self.model.make_solid('revolve',r1=lambda x: self.r_jacket_in(x),
                                  r2=lambda x: self.r_jacket_out(x),
                                  x1=0,x2=self.L_c+self.L_n,
                                  theta1=n*2*np.pi/self.n_fin,
                                  theta2=n*2*np.pi/self.n_fin+self.dtheta_fin,
                                  material='C18150',name='jacket{}'.format(n))
            # jacket between fins
            self.model.make_solid('revolve',r1=lambda x: self.r_jacket_in(x),
                              r2=lambda x: self.r_jacket_out(x),
                              x1=0,x2=self.L_c+self.L_n,
                              theta1=n*2*np.pi/self.n_fin+self.dtheta_fin,
                              theta2=np.mod(n+1,self.n_fin)*2*np.pi/self.n_fin,
                              material='C18150',name='jacket{}'.format(n+0.5))
            
        # now the mesh should be complete

    def build_contacts(self):
        # contacts
        for n in range(self.n_fin):
            # bottom of fins
            self.model.make_contact('liner{}'.format(n),'fin{}'.format(n))
            # top of fins
            # contact conductance from A Heat Transfer Textbook p76
            self.model.make_contact('fin{}'.format(n),'jacket{}'.format(n),
                                    h=10e3)
            # between liner sections
            self.model.make_contact('liner{}'.format(n),
                                    'liner{}'.format(n+0.5))
            self.model.make_contact('liner{}'.format(n+0.5),
                                    'liner{}'.format(np.mod(n+1,self.n_fin)))
            # between jacket sections
            self.model.make_contact('jacket{}'.format(n),
                                    'jacket{}'.format(n+0.5))
            self.model.make_contact('jacket{}'.format(n+0.5),
                                    'jacket{}'.format(np.mod(n+1,self.n_fin)))
            
    def set_boundaries(self):
        # convective boundaries
        for n in range(self.n_fin):
            # outer liner to fuel
            self.model.make_convection('liner{}'.format(n+0.5),'+r',
                                       h_of_x=lambda x: self.get_hc_liner(x),
                                       T_of_x=lambda x: self.get_Tc(x))
            # -theta side of fins
            self.model.make_convection('fin{}'.format(n),'-theta',
                                       h_of_x=lambda x: self.get_hc_liner(x),
                                       T_of_x=lambda x: self.get_Tc(x))
            # +theta side of fins
            self.model.make_convection('fin{}'.format(n),'+theta',
                                       h_of_x=lambda x: self.get_hc_liner(x),
                                       T_of_x=lambda x: self.get_Tc(x))
            # inner jacket to fuel
            self.model.make_convection('jacket{}'.format(n+0.5),'-r',
                                       h_of_x=lambda x: self.get_hc_jacket(x),
                                       T_of_x=lambda x: self.get_Tc(x))
            # hot gas to inner liner
            self.model.make_convection('liner{}'.format(n+0.5),'-r',
                                       h_of_x=lambda x: self.get_hg(x),
                                       T_of_x=lambda x: self.get_Taw(x))
            # outer jacket to ambient
            self.model.make_convection('jacket{}'.format(n),'+r',
                                       h_of_x=lambda x: self.h_amb,
                                       T_of_x=lambda x: self.T_amb)
        
        pass
    
    def calc_geometry(self):
        '''Sets geometry parameters derived from the primary inputs.'''
        # length of the chamber cylinder
        # TODO
        self.L_cyl = np.nan
        # location of start of nozzle bell
        # TODO
        self.x_bell_start = np.nan
        # angular width of fin
        # TODO
        self.dtheta_fin = np.nan
        
    def r_liner_in(self,x):
        '''Returns the radius of the inner liner wall at the given location'''
        # TODO
        pass
    
    def r_liner_out(self,x):
        '''Returns the radius of the liner outer wall at the given location'''
        # TODO
        pass
    
    def r_jacket_in(self,x):
        '''Returns the radius of the inner jacket wall at the given location'''
        # TODO
        pass
    
    def r_jacket_out(self,x):
        '''Returns the radius of the outer jacket wall at the given location'''
        # TODO
        pass
    
    def get_hc_liner(self,x):
        '''Returns the htc between the coolant liquid and liner at the given 
        location.'''
        # TODO
        pass
    
    def get_hc_jacket(self,x):
        '''Returns the htc between the coolant liquid and jacket at the given 
        location.'''
        # TODO
        pass
    
    def get_hg(self,x):
        '''Returns the hot gas htc at the given location.'''
        # TODO
        pass
    
    def get_Tc(self,x):
        '''Returns the temeprature of the coolant liquid at the given location.
        '''
        # TODO
        pass
    
    def get_Taw(self,x):
        '''Returns the adiabatic wall temperature of the hot gas at the 
        given location.'''
        # TODO
        pass
    
    def init_cooling(self):
        '''Sets initial temepratures in the coolant liquid.'''
        # TODO
        pass
    
    def update_cooling(self):
        '''Updates the coolant temepratures based on the current wall 
        temepratures.'''
        # TODO
        pass
    
    def get_max_Tc(self):
        '''Returns the coolant temperature at the end of the passsage.'''
        # TODO
        pass
    
    
    
    
    
    
    
    
            
            
        
        
    
    

