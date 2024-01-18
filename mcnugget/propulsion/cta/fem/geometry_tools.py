# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 14:45:25 2024

@author: Nate Campbell
"""

import math

def cyl_dist(r1,th1,z1,r2,th2,z2):
    '''Returns the distance between two points in cylindrical coordinates'''
    
    x1 = r1*math.cos(th1)
    y1 = r1*math.sin(th1)
    x2 = r2*math.cos(th2)
    y2 = r2*math.sin(th2)

    return math.dist((x1,y1,z1),(x2,y2,z2))
   

