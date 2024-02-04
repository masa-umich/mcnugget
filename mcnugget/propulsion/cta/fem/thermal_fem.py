# -*- coding: utf-8 -*-
"""
Created on Sat Jan 13 16:38:32 2024

@author: natecamp
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geometry_tools
import math
import matplotlib as mpl

class Model:
    '''Represents a three-dimensional thermal finite element model.'''
    
    def __init__(self):
        # default numbers of elements through solid dimensions
        self.r_numel = 2
        self.theta_numel = 3
        self.x_numel = 4
        # maximum node number created
        self.max_noden = -1
        # table with node information
        # r, theta, and z coordinates 
        # sol_id is the index for the node in the solution matrix
        # indexed by the node number 
        self.node_tbl = pd.DataFrame({'r':[],'theta':[],'x':[],'sol_id':[]})
        # dict with node connections
        self.node_connect = dict()
        # dict of Body objects with the names as the keys
        self.bodies = dict()
        # the solution matrix (A of Ax=b)
        self.sol_mat = []
        # the solution vector (b of Ax=b)
        self.sol_vec = []
        # the temperature results
        # this should be a pd.Series indexed by the sol_ids
        self.T = None
        
    def solve(self):
        '''Solve for all temperatures.
        
        http://masa.eecs.umich.edu/wiki/index.php/Thrust_Chamber_Thermal_Modeling
        '''
        # extract the list of unique solution ids
        sol_id = list(dict.fromkeys(self.node_tbl['sol_id']))
        num_T = len(sol_id)

        # need to make sure there aren't gaps in the sol_ids
        # the sol_idx will be a new index that doesn't have gaps
        # use this Series to get the sol_idx from the sol_id, and use the 
        # sol_idx to index the solution matrix
        sol_idx = pd.Series(data=list(range(num_T)),index=sol_id)
        
        # initialize solution system
        self.sol_mat = np.zeros((num_T,num_T))
        self.sol_vec = np.zeros((num_T,1))
                
        # add the solid conduction resistances
        # R = t/kA
        
        # TODO: make sure body is a reference, not a copy
        for body in self.bodies:
            for node0 in body.nodes:
                # node0 corresponds to the i index, or the row of the matrix
                
                # solution id for node0
                sol_id0 = self.node_tbl.loc[node0,'sol_id']
                # solution index for node0
                sol_idx0 = sol_idx.loc[sol_id0]
                                
                for (face,node1) in self.node_connect[node0]:
                    # node1 corresponds to the j index, or the column of the 
                    # matrix
                    
                    # solution id
                    sol_id1 = self.node_tbl.loc[node1,'sol_id']
                    # solution index
                    sol_idx1 = sol_idx.loc[sol_id0]
                    
                    # distance between the nodes
                    L = self.node_dist(node0,node1)
                    # node areas normal to heat flow
                    A0 = body.areas[face].loc[node0]
                    A1 = body.areas[face].loc[node1]
                    # just take the average ig
                    A = (A0+A1)/2
                    # get thermal conductivity from the Body's Material
                    k = body.material.get('k')
                    # thermal resistance
                    Rij = L/(k*A)
                    
                    # now put this thermal resistance in the solution matrix
                    # add -1/Rij in i row, i col
                    self.sol_mat[sol_idx0,sol_idx0] += -1/Rij
                    # add 1/Rij in i row, j col
                    self.sol_mat[sol_idx0,sol_idx1] += 1/Rij
                    
        # now iterate over the convection objects 
        # add the -Gai Ti and Gai Ta
        for convect in self.convects:
            body = self.bodies[convect.body_name]
            for node0 in body.faces[convect.face_name]:
                sol_id0 = self.node_tbl.loc[node0,'sol_id']
                sol_idx0 = sol_idx.loc[sol_id0]
                
                # get the area of this node
                # the face_name has a +/- on the end, so yeet to index the 
                # areas dict
                # index value of the areas dict with the r/x/theta direction
                # inex the area in the Series with the node number
                A = body.areas[convect.face_name[:-1]].loc[node0]
                
                # get the x coordinate of nodei
                xi = self.node_tbl.loc[node0,'x']
                # add -Gai to row i, col i
                self.sol_mat[sol_idx0,sol_idx0] += convect.h(xi)*A
                # add -Gai Ta to b row i
                self.sol_vec.loc[sol_idx0] += -convect.h(xi)*A * convect.T_inf
        
        # now just solve the system
        T_vec = np.linalg.solve(self.sol_mat,self.sol_vec)
        # put into a series indexed by the sol_id
        self.T = pd.Series(data=T_vec,index=sol_id)
            

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
            r1 (function) 
             - returns the inner radius of the body as a function of x location
            r2 (function) 
             - returns the outer radius of the body as a function of x location
            x1 (float) - the minimum x dimension of the body
            
            x2 (float) - the maximum x dimension of the body
            
            theta1 (float) - the minimum theta dimension of the body
            
            theta2 (float) - the maximum theta dimension of the body
            
            material (string) 
             - the material used for the capacitance of nodes and thermal 
               resistance between nodes
             - currently supports C18150, Al6061
             - data from ./input_sheets/materials.xlsx
                              
            name (string) - a label used for applying contacts and boundaries
            
        Calculations
         - coordinates of each node
         - area of each face element (stored in Body object)
         - the connections between nodes
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
                
        # https://stackoverflow.com/questions/22981845/3-dimensional-array-in-numpy 
        node_theta = np.linspace(args['theta1'],args['theta2'],
            self.theta_numel)[np.newaxis,:,np.newaxis]+np.zeros((
            self.r_numel,self.theta_numel,self.x_numel))
        node_x = np.linspace(args['x1'],args['x2'],self.x_numel)[
            np.newaxis,np.newaxis,:]+np.zeros((
            self.r_numel,self.theta_numel,self.x_numel))
        
        # node_x[0] and node_x[self.r_numel] should be the same
        node_r1 = args['r1'](node_x[0])
        node_r2 = args['r2'](node_x[-1])
        # linear interpolation
        node_r = node_r1 + (node_r2-node_r1)*np.linspace(
            0,1,self.r_numel)[:,np.newaxis,np.newaxis]
        
        # reshape these 3d arrays into one dimensional lists and put into table
        # all of these arrays should have the same shape, and corresponding
        # locations, so they just need to be reshaped in the same order
        # the sol_id is initially the node number for all nodes, and can be 
        # changed if it becomes part of a contact
        
        body_node_tbl = pd.DataFrame(
            data={
                'r':node_r.reshape(-1),
                'theta':node_theta.reshape(-1),
                'x':node_x.reshape(-1),
                'sol_id':body_nodes.reshape(-1)
            },
            index=body_nodes.reshape(-1)
            )
        self.node_tbl = pd.concat((self.node_tbl,body_node_tbl))
        self.nodes = body_nodes.reshape(-1)
        
        # make the Body object for this body
        self.bodies[name] = Body(name,args['material'])
        # sort the nodes into faces
        self.bodies[name].faces['r+']     = body_nodes[-1,:,:].copy()
        self.bodies[name].faces['r-']     = body_nodes[0,:,:].copy()
        self.bodies[name].faces['theta+'] = body_nodes[:,-1,:].copy()
        self.bodies[name].faces['theta-'] = body_nodes[:,0,:].copy()
        self.bodies[name].faces['x+']     = body_nodes[:,:,-1].copy()
        self.bodies[name].faces['x-']     = body_nodes[:,:,0].copy()
        
        # get the surface areas for the nodes
        self.calc_body_areas(args,name,body_nodes,node_r,node_theta,node_x,
                             body_node_tbl)
        
        # node connections
        for r_idx in range(self.r_numel):
            for th_idx in range(self.theta_numel):
                for x_idx in range(self.x_numel):
                    # node number
                    node = body_nodes[r_idx,th_idx,x_idx]
                    # initialize the list of nodes that connect to this one
                    self.node_connect[node] = set()
                    # add r- node
                    if r_idx > 0:
                        node_rn = body_nodes[r_idx-1,th_idx,x_idx]
                        self.node_connect[node].add(('r',node_rn))
                    # add r+ node
                    if r_idx < self.r_numel-1:
                        node_rp = body_nodes[r_idx+1,th_idx,x_idx]
                        self.node_connect[node].add(('r',node_rp))
                    # add th- node
                    if th_idx > 0:
                        node_thn = body_nodes[r_idx,th_idx-1,x_idx]
                        self.node_connect[node].add(('theta',node_thn))
                    # add th+ node
                    if th_idx < self.theta_numel-1:
                        node_thp = body_nodes[r_idx,th_idx+1,x_idx]
                        self.node_connect[node].add(('theta',node_thp))
                    # add x- node
                    if x_idx > 0:
                        node_xn = body_nodes[r_idx,th_idx,x_idx-1]
                        self.node_connect[node].add(('x',node_xn))
                    # add x+ node
                    if x_idx < self.x_numel-1:
                        node_xp = body_nodes[r_idx,th_idx,x_idx+1]
                        self.node_connect[node].add(('x',node_xp))
        
        
    def calc_body_areas(self,args,name,body_nodes,node_r,node_theta,node_x,
                        body_node_tbl):
        '''Calculate all external and internal node surface areas in the
        three planes and store to self.bodies[name].areas'''
        
        # TODO: should store the current numel values in the body objects
        
        # r+ face - [-1,:,:], r- face - [0,:,:]
        face = 'r'
        for r_idx in range(self.r_numel):
            
            # calculate the midpoints
            # midpoint arrays on the r face, x and theta coordintes
            (mid_r_x,mid_r_th) = geometry_tools.array_midpoints(
                node_x[r_idx],node_theta[r_idx])
            # midpoint arrary of r coordinates for the r face
            mid_r_r1 = args['r1'](mid_r_x)
            mid_r_r2 = args['r2'](mid_r_x)
            mid_r_r = mid_r_r1 + (mid_r_r2-mid_r_r1)*(r_idx/(self.r_numel-1))
            
            # calculate areas by splitting each face into two triangles
            for th_idx in range(self.theta_numel):
                for x_idx in range(self.x_numel):
                    # node numbers
                    node0 = body_nodes[r_idx,th_idx,x_idx]
                    # node1 = body_nodes[r_idx,th_idx+1,x_idx]
                    # node2 = body_nodes[r_idx,th_idx,x_idx+1]
                    # node3 = body_nodes[r_idx,th_idx+1,x_idx+1]
                    
                    # area of triangles 1 and 2
                    # triangle 1 is points 0,1,2
                    # triangle 2 is points 3,1,2
                    tr1 = geometry_tools.cyl_tri_area(
                        (
                        mid_r_r[th_idx,x_idx],
                        mid_r_th[th_idx,x_idx],
                        mid_r_x[th_idx,x_idx]
                        ),(
                        mid_r_r[th_idx+1,x_idx],
                        mid_r_th[th_idx+1,x_idx],
                        mid_r_x[th_idx+1,x_idx]
                        ),(
                        mid_r_r[th_idx,x_idx+1],
                        mid_r_th[th_idx,x_idx+1],
                        mid_r_x[th_idx,x_idx+1]
                        ))
                    tr2 = geometry_tools.cyl_tri_area(
                        (
                        mid_r_r[th_idx+1,x_idx+1],
                        mid_r_th[th_idx+1,x_idx+1],
                        mid_r_x[th_idx+1,x_idx+1]
                        ),(
                        mid_r_r[th_idx+1,x_idx],
                        mid_r_th[th_idx+1,x_idx],
                        mid_r_x[th_idx+1,x_idx]
                        ),(
                        mid_r_r[th_idx,x_idx+1],
                        mid_r_th[th_idx,x_idx+1],
                        mid_r_x[th_idx,x_idx+1]
                        ))
                    # add areas of triangles to make area of 4-sided element
                    self.bodies[name].areas[face][node0] = tr1+tr2
    
        # th+ face - [:,-1,:], th- face - [:,0,:]
        face = 'theta'
        for th_idx in range(self.theta_numel):
            
            # calculate the midpoints
            # midpoint arrays on the theta face, x and r coordintes
            (mid_th_x,mid_th_r) = geometry_tools.array_midpoints(
                node_x[:,th_idx],node_r[:,th_idx])
            # midpoint arrary of theta coordinates for the theta face
            # TODO: update this when implementing theta profiles
            # assumes that the theta values are constant over the face
            mid_th_th = node_theta[0,th_idx,0]+np.zeros((
                self.r_numel+1,self.x_numel+1))
            assert(
                math.isclose(node_theta[-1,th_idx,-1],node_theta[0,th_idx,0]))
            
            # calculate areas by splitting each face into two triangles
            for r_idx in range(self.r_numel):
                for x_idx in range(self.x_numel):
                    # node numbers
                    node0 = body_nodes[r_idx,th_idx,x_idx]
                    
                    # area of triangles 1 and 2
                    # triangle 1 is points 0,1,2
                    # triangle 2 is points 3,1,2
                    tr1 = geometry_tools.cyl_tri_area(
                        (
                        mid_th_r[r_idx,x_idx],
                        mid_th_th[r_idx,x_idx],
                        mid_th_x[r_idx,x_idx]
                        ),(
                        mid_th_r[r_idx+1,x_idx],
                        mid_th_th[r_idx+1,x_idx],
                        mid_th_x[r_idx+1,x_idx]
                        ),(
                        mid_th_r[r_idx,x_idx+1],
                        mid_th_th[r_idx,x_idx+1],
                        mid_th_x[r_idx,x_idx+1]
                        ))
                    tr2 = geometry_tools.cyl_tri_area(
                        (
                        mid_th_r[r_idx+1,x_idx+1],
                        mid_th_th[r_idx+1,x_idx+1],
                        mid_th_x[r_idx+1,x_idx+1]
                        ),(
                        mid_th_r[r_idx+1,x_idx],
                        mid_th_th[r_idx+1,x_idx],
                        mid_th_x[r_idx+1,x_idx]
                        ),(
                        mid_th_r[r_idx,x_idx+1],
                        mid_th_th[r_idx,x_idx+1],
                        mid_th_x[r_idx,x_idx+1]
                        ))
                    # add areas of triangles to make area of 4-sided element
                    self.bodies[name].areas[face][node0] = tr1+tr2

        # x+ face - [:,:,-1], x- face - [:,:,0]
        face = 'x'
        for x_idx in range(self.x_numel):
            
            # calculate the midpoints
            # midpoint arrays on the x face, theta and r coordintes
            (mid_x_th,mid_x_r) = geometry_tools.array_midpoints(
                node_theta[:,:,x_idx],node_r[:,:,x_idx])
            # midpoint arrary of theta coordinates for the x face
            # assumes that the theta values are constant over the face
            mid_x_x = node_x[0,0,x_idx]+np.zeros((
                self.r_numel+1,self.theta_numel+1))
            assert(math.isclose(node_x[-1,-1,x_idx],node_x[0,0,x_idx]))
            
            # calculate areas by splitting each face into two triangles
            for r_idx in range(self.r_numel):
                for th_idx in range(self.theta_numel):
                    # node numbers
                    node0 = body_nodes[r_idx,th_idx,x_idx]
                    
                    # area of triangles 1 and 2
                    # triangle 1 is points 0,1,2
                    # triangle 2 is points 3,1,2
                    tr1 = geometry_tools.cyl_tri_area(
                        (
                        mid_x_r[r_idx,th_idx],
                        mid_x_th[r_idx,th_idx],
                        mid_x_x[r_idx,th_idx]
                        ),(
                        mid_x_r[r_idx+1,th_idx],
                        mid_x_th[r_idx+1,th_idx],
                        mid_x_x[r_idx+1,th_idx]
                        ),(
                        mid_x_r[r_idx,th_idx+1],
                        mid_x_th[r_idx,th_idx+1],
                        mid_x_x[r_idx,th_idx+1]
                        ))
                    tr2 = geometry_tools.cyl_tri_area(
                        (
                        mid_x_r[r_idx+1,th_idx+1],
                        mid_x_th[r_idx+1,th_idx+1],
                        mid_x_x[r_idx+1,th_idx+1]
                        ),(
                        mid_x_r[r_idx+1,th_idx],
                        mid_x_th[r_idx+1,th_idx],
                        mid_x_x[r_idx+1,th_idx]
                        ),(
                        mid_x_r[r_idx,th_idx+1],
                        mid_x_th[r_idx,th_idx+1],
                        mid_x_x[r_idx,th_idx+1]
                        ))
                    # add areas of triangles to make area of 4-sided element
                    self.bodies[name].areas[face][node0] = tr1+tr2
        
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
        
    def plot_mesh(self):
        '''Plots the mesh nodes and returns the Axes object.'''
        fig = plt.figure(figsize=(10,10))
        ax = fig.add_subplot(projection='3d')
        
        # plot a line from each node to each of its connections
        for start_node in self.node_connect.keys():
            # get the coordinates of start_node
            r0,th0,x0 = self.node_tbl.loc[start_node,['r','theta','x']]
            # make cartesian point
            p0 = geometry_tools.cyl_to_cart((r0,th0,x0))
            # loop over the nodes that connect
            for face,end_node in self.node_connect[start_node]:
                r1,th1,x1 = self.node_tbl.loc[end_node,['r','theta','x']]
                p1 = geometry_tools.cyl_to_cart((r1,th1,x1))
                # plot the line from start_node to end_node
                ax.plot([p0[0],p1[0]],[p0[1],p1[1]],[p0[2],p1[2]])
        
        plt.show()
        return ax
    
    def node_dist(self,node0,node1):
        '''Returns the distance between the two nodes.'''
        
        r0,th0,x0 = self.node_tbl.loc[node0,['r','theta','x']]
        r1,th1,x1 = self.node_tbl.loc[node1,['r','theta','x']]
        return geometry_tools.cyl_dist(r0,th0,x0,r1,th1,x1)
        
            
class Body:
    '''Represents a solid body in the model.'''
    def __init__(self,name,material):
        # the name and material of this body
        self.name = name
        self.material = Material(material)
        # stores nodes numbers that belong on each of the six faces
        self.faces = {
            'r+':[],'r-':[],'theta+':[],'theta-':[],'x+':[],'x-':[]
            }
        # stores the surface area that nodes have on this body, organized by 
        # normal direction
        # each value is a pd.Series indexed by node numbers
        self.areas = {
            'r':pd.Series(),
            'theta':pd.Series(),
            'x':pd.Series()
            }
        # list of node numbers in this Body
        self.nodes = []
        
class Material:
    '''Represents a material with temperature dependent properties.
    
    Available properties: k [W/(m*K)]
    
    Uses default data sheet at ./input_sheets/materials.xlsx
    '''
    
    def __init__(self,name):
        
        fname = 'input_sheets/materials.xlsx'
        self.data = pd.read_excel(fname,sheet_name=name)
        
    def get(self,prop,T=None):
        '''Returns the value of prop at temperature T [K].'''
        if T is None:
            return self.data.loc[0,prop]
        else:
            return np.interp(self.data['T'],T,self.data['prop'])
        
        
class Convect:
    '''Represents a convection boundary condition applied to the face of 
    a boday with a heat transfer coefficient, h(x) [W/m^2*K] and 
    freestream T [K].
    
    '''
    
    def __init__(self,body_name,face_name,h,T):
        '''    
        Inputs:
        body_name: string
         - the name used to create the body this is applied to
         
        face_name: 'r+', 'r-', 'theta+', 'theta-', 'x+', or 'x-'
         - the face this is applied to
         
        h: function of axial location x
         - returns the desired heat transfer coefficient in W/m^2*K
         
        T: freestream temperature in K
         '''
         
        self.body_name = body_name
        self.face_name = face_name
        self.h = h
        self.T = T
        
        
    