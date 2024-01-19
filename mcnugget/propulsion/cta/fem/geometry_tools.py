# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 14:45:25 2024

@author: Nate Campbell
"""

import math
import numpy as np

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
    x_mid = (x[:,0:-1]+x[:,1:])/2
    y_mid = (y[0:-1,:]+y[1:,:])/2 
    
    # extend in the constant dimension 
    x_mid = np.concatenate((x_mid,x_mid[0,np.newaxis,:]),axis=0)
    y_mid = np.concatenate((y_mid,y_mid[:,0,np.newaxis]),axis=1)
    
    # pad with edge values
    x_left = np.concatenate(([[x[0,0]]],x[:,0,np.newaxis]),axis=0)
    x_right = np.concatenate(([[x[0,-1]]],x[:,-1,np.newaxis]),axis=0)
    x_mid = np.concatenate((x_left,x_mid,x_right),axis=1)
    
    y_top = np.concatenate(([[y[0,0]]],y[0,np.newaxis,:]),axis=1)
    y_bot = np.concatenate(([[y[-1,0]]],y[-1,np.newaxis,:]),axis=1)
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
    
    
    
    
    
    
    
    
