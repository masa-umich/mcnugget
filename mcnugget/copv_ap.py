import numpy as np #computations
import pandas as pd #data cleaning
import matplotlib.pyplot as plt #matlab plots
import CoolProp as cp #cool prop


#max continuous operating temperature, various specification parameters 
#for your COPV (volume, surface area, thermodynamic properties, etc),  
#the press rate of your pump, and the specifications of your gas bottle
def copvAP(supplyP_1, cycleNum, vSupply, maxTemp):
    #parameters need a bit of workshopping 
    
    # does it tell how fast to cycle pump (ultimate question trying to answer)
    # with cycle #, inlet pressure, copv pressure, copv mass, and temperature
    # Pressure inputs in psi and volume in L, temp in celsius
    # The booster has a maximum speed of 60 cpm

#constants and variables (psi -> pa and atm -> pa and c -> k)
    copvVolume = 26.6  # in liters
    copvPressure = 1 * 101325  # atm -> pascal
    meop = 6000 * 6894.76  # psi -> pascal
    maxCycleNum = 60 #60 cycles per minute max, which means 1 cycle/second 
    copvTemp = cp.PropsSI('T', 'P', copvPressure, 'Q', 1, 'Nitrogen')
    
    while copvPressure > meop or copvTemp > maxTemp:
        # Phase 1: 0->2k phase (fast pressure climb)
        #if copvPresure > 2k:
        #add more 
        #else copv pressure being over 2k 
#time between cycles? 
        

#2 phases: 0->2k phase (just what is in the 2k bottle) faster pressure climb
#2nd phase is pressing, using the pump 

#max operating pressure, max operating temp as parameter 
#write something for the first and second phase 

#how fast the cycles should be, time in between each open and close 
#first phase: time will be different because pressing faster 
# every time press COPV start out at 0 
#in some cases you are never going to go to phase 2 because you don't have to turn the pump on 
#current operating pressure might never reach 2k