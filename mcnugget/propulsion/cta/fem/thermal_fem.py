# -*- coding: utf-8 -*-
"""
Created on Sat Jan 13 16:38:32 2024

@author: natecamp
"""

import numpy as np
import pandas as pd

class Model:
    '''Represents a three-dimensional thermal finite element model.'''
    
    def __Model__(self):
        # default numbers of elements through solid dimensions
        self.r_numel = 2
        self.theta_numel = 3
        self.x_numel = 4
        # maximum node number created
        self.max_noden = -1
        # table with node information
        self.node_tbl = pd.DataFrame({'r':[],'theta':[],'z':[]})
        # dict with node connections
        self.node_connect = dict()
        # dict of Body objects with the names as the keys
        self.bodies = dict()
        
        
    
    def solve(self):
        '''Solve for all temperatures.'''
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
        
        # the name of this solid
        name = args['name']
        
        # do all calculations in this function and store the body-specific
        # results in the body objects instead of doing calculations in the 
        # Bodies
                
        # number of nodes in this body
        num_bnodes = self.r_numel*self.theta_numel*self.x_numel
        # make a matrix with node numbers
        # dimensions: (r,th,x)
        body_nodes = np.reshape(np.linspace(
            self.max_noden+1,self.max_noden+1+num_bnodes-1,num_bnodes
            ),(self.r_numel,self.theta_numel,self.x_numel))
                
        # np.linspace puts the vector in the third dimension
        # https://stackoverflow.com/questions/22981845/3-dimensional-array-in-numpy 
        node_theta = (np.linspace(args['theta1'],args['theta2'],
                                 self.theta_numel)+np.zeros((
             self.x_numel,self.r_numel,self.theta_numel))).transpose((1,2,0))
        node_x = (np.linspace(args['x1'],args['x2'],self.x_numel)+np.zeros((
            self.r_numel,self.theta_numel,self.x_numel))).transpose((0,1,2))
        
        # node_x[0] and node_x[self.numel_r] should be the same
        node_r1 = args['r1'](node_x[0])
        node_r2 = args['r2'](node_x[self.numel_r])
        # linear interpolation
        node_r = node_r1 + (node_r2-node_r1)*np.linspace(
            0,1,self.numel_r)[:,np.newaxis,np.newaxis]
        
        # reshape these 3d arrays into one dimensional lists and put into table
        # all of these arrays should have the same shape, and corresponding
        # locations, so they just need to be reshaped in the same order
        
        body_node_tbl = pd.DataFrame(
            data={
                'r':node_r.reshape(-1),
                'theta':node_theta.reshape(-1),
                'x':node_x.reshape(-1)
            },
            index=body_nodes.reshape(-1)
            )
        
        # make the Body object for this body
        self.bodies[name] = Body(name,args['material'])
        # sort the nodes into faces
        self.bodes[name].faces['r+'] = body_nodes[-1,:,:]
        self.bodies[name].faces['r-'] = body_nodes[0,:,:]
        self.bodies[name].faces['theta+'] = body_nodes[:,-1,:]
        self.bodies[name].faces['theta-'] = body_nodes[:,0,:]
        self.bodies[name].faces['z+'] = body_nodes[:,:,-1]
        self.bodies[name].faces['z-'] = body_nodes[:,:,0]
        
        # get the surface areas for the nodes
        # r+ face
        el_areas = None  
        
        
        
        
        
        

           

        
        
    def set_r_numel(self,numel):
        '''Sets the number of elements that will be made through the radial 
        dimension of new solids created.'''
        
        self.r_numel = numel
        
    def set_theta_numel(self,numel):
        '''Sets the number of elements that will be made through the tangential
        dimension of new solids created.'''

        self.theta_numel = numel
        
    def set_x_numel(self,numel):
        '''Sets the number of elements that will be made through the axial 
        dimension of new solids created.'''
        
        self.x_numel = numel
        
            
class Body:
    '''Represents a solid body in the model.'''
    def __init__(self,name,material):
        # the name and material of this body
        self.name = name
        self.material = material
        # stores nodes numbers that belong on each of the six faces
        self.faces = {
            'r+':[],'r-':[],'theta+':[],'theta-':[],'x+':[],'x-':[]
            }
        # stores the surface area that nodes have on this body
        self.node_area = pd.Series(name='area')
        
        
    
    
    
    