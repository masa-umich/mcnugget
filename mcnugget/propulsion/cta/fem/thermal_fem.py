# -*- coding: utf-8 -*-
"""
Created on Sat Jan 13 16:38:32 2024

@author: natecamp
"""

import numpy as np

class Model:
    '''Represents a three-dimensional thermal finite element model.'''
    
    def __Model__():
        pass
    
    def solve(self):
        '''Solve for all temperatures.'''
        pass
    
    def set_theta_divs(self,theta_divs):
        pass
    
    def make_solid(self,shape,**args):
        '''Adds a solid body to the model.
        
        Inputs:
            shape (string) - the type of solid to create
                           - currently supports 'revolve'
        '''
        
        if shape == 'revolve':
            self.make_revolve(**args)
        else:
            raise ValueError('invalid shape given to Model.make_solid')
        pass
    
    def make_contact(self,body_name_1,body_name_2,h=None):
        pass
    
    def make_convection(self,body_name,direction,**args):
        pass
    
    def make_revolve(self,**args):
        '''Adds a solid revolved body to the model.
                
        Keyword Inputs:
            r1 (function) - returns the inner radius of the body as a function 
                            of x location
            r2 (function) - returns the outer radius of the body as a function 
                            of x location
            x1 (float) - the minimum x dimension of the body
            x2 (float) - the maximum x dimension of the body
            theta1 (float) - the minimum theta dimension of the body
            theta2 (float) - the maximum theta dimension of the body
            material (string) - the material used for the capacitance of nodes 
                                and thermal resistance between nodes
                              - currently supports C18150, Al6061
                              - data from ./input_sheets/materials.xlsx
            name (string) - a label used for applying contacts and boundaries
            
        '''
        
        # make a matrix with node numbers
        shape_nodes = np.array()
        
        
    
    
    
    