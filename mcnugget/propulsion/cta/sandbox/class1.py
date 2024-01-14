# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 15:27:13 2024

@author: Nate Campbell
"""

import class2

class Class1:
    def __init__(self):
        self.class2 = class2.Class2()
        
    def func1(self):
        print('calling class2.func3')
        self.class2.func3(lambda x: self.func2(x))
        
    def func2(self,x):
        return x**2
        
