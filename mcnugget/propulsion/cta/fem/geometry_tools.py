# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 14:45:25 2024

@author: Nate Campbell
"""

import math
import numpy as np

def test_array_midpoints():
    x = np.array(range(4))[np.newaxis,:]+np.zeros((3,4))
    y = np.linspace(0,0.2,3)[:,np.newaxis]+np.zeros((3,4))
    print('x:\n',x)
    print('y:\n',y)
    z = x + y
    print('z:\n',z)
    (z_mid,y_mid) = array_midpoints(z, y)
    # print('x_mid:\n',x_mid)
    # print('y_mid:\n',y_mid)
    print('z_mid:\n',z_mid)

def cyl_dist(r1,th1,z1,r2,th2,z2):
    '''Returns the distance between two points in cylindrical coordinates'''
    
    x1 = r1*math.cos(th1)
    y1 = r1*math.sin(th1)
    x2 = r2*math.cos(th2)
    y2 = r2*math.sin(th2)

    return math.dist((x1,y1,z1),(x2,y2,z2))
   
def array_midpoints(x,y):
    '''Returns x,y matrices representing the midpoints and edges of the grid.
    
    y is the first dimension, and x is the second
    '''
    # take the midpoints in the primary direction
    x_mid = (x[:,0:-1]+x[:,1:])/2
    y_mid = (y[0:-1,:]+y[1:,:])/2 
    
    x_mid_top = x_mid[0,:].copy()
    x_mid_bot = x_mid[-1,:].copy()
    y_mid_left = y_mid[:,0].copy()
    y_mid_right = y_mid[:,-1].copy()
    
    # take averages to account for changes in the secondary direction
    x_mid = (x_mid[0:-1,:]+x_mid[1:,:])/2
    y_mid = (y_mid[:,0:-1]+y_mid[:,1:])/2
    
    # extend in the constant dimension 
    x_mid = np.concatenate((
        x_mid_top[np.newaxis,:],x_mid,x_mid_bot[np.newaxis,:]),axis=0)
    y_mid = np.concatenate((
        y_mid_left[:,np.newaxis],y_mid,y_mid_right[:,np.newaxis]),axis=1)
    
    # pad with edge values
    x_left_mid = np.array((x[0:-1,0]+x[1:,0])/2)[:,np.newaxis]
    x_right_mid = np.array((x[0:-1,-1]+x[1:,-1])/2)[:,np.newaxis]
    x_left = np.concatenate(([[x[0,0]]],x_left_mid,[[x[-1,0]]]),axis=0)
    x_right = np.concatenate(([[x[0,-1]]],x_right_mid,[[x[-1,-1]]]),axis=0)
    x_mid = np.concatenate((x_left,x_mid,x_right),axis=1)
    
    y_top_mid = np.array((y[0,0:-1]+y[0,1:])/2)[np.newaxis,:]
    y_bot_mid = np.array((y[-1,0:-1]+y[-1,1:])/2)[np.newaxis,:]
    y_top = np.concatenate(([[y[0,0]]],y_top_mid,[[y[0,-1]]]),axis=1)
    y_bot = np.concatenate(([[y[-1,0]]],y_bot_mid,[[y[-1,-1]]]),axis=1)
    y_mid = np.concatenate((y_top,y_mid,y_bot),axis=0)
    
    return (x_mid,y_mid)    
    
def cyl_tri_area(p1,p2,p3):
    '''Returns the area of the triangle formed by the three cylindrical points.
    
    p1,p2,p3: tuples of (r,theta,z) coordinates
    
    Uses Heron's formula: A = sqrt(s(s-a)(s-b)(s-c)); s = 1/2(a+b+c)
    '''
    
    # first convert the coordinates from cylindrical to cartesian
    p1 = cyl_to_cart(p1)
    p2 = cyl_to_cart(p2)
    p3 = cyl_to_cart(p3)
    
    # find the side lengths
    a = math.dist(p1,p2)
    b = math.dist(p2,p3)
    c = math.dist(p3,p1)
    
    # find the semi-perimeter
    s = 1/2*(a+b+c)
    
    # find the area
    A = math.sqrt(s*(s-a)*(s-b)*(s-c))
    
    return A
    
    
def cyl_to_cart(p):
    '''Converts a tuple of 3d cylindrical (r,th,z) coordinates to cartesian (x,y,z).'''
    r = p[0]
    theta = p[1]
    z = p[2]
    return (r*math.cos(theta),r*math.sin(theta),z)
    
if __name__ == '__main__':
    test_array_midpoints()
    
    
    
    
    
    
    
