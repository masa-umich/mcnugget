import numpy as np #computations
import pandas as pd #data cleaning
import matplotlib.pyplot as plt #matlab plots
import pyfluids as cp #cool prop

def gasBooster(supplyP_1, supplyV, copvV, temp): 
    # GOOSTER plots copv pressure and temperature vs cycle # and outputs a table
    # with cycle #, inlet pressure, copv pressure, copv mass, and temperature
    # for every 30 cycles.
    # Pressure inputs in psi and volume in L, temp in celsius
    # The booster has a maximum speed of 60 cpm
   
# setting constants and variables and conversions (psi -> atm, C -> K)
    inletPressure = supplyP_1 * 0.06804 
    outletPressure = supplyP_1 * 0.68046 #init copv pressure (eq to 4k)
    Vs = supplyV 
    Vo = copvV
    Tcopv = temp + 273.15  #assuming conversion from c to k in copv
    Ts = temp + 273.15
    R = 0.0820574 #ideal gas constant 
    molar_m = 28.0134
    cycleV = 0.02031996
    v2 = cycleV / 20
    i = 1 
    cp = 1.04 
    pa = 140 * 0.068046

# find initial mass of n2 in copv and 2k bottle after equalized 
# change to real gas (cool prop)
    ms = (inletPressure * Vs * molar_m) / (R * Ts)
    copvMass = (outletPressure * Vo * molar_m)/(R * Tcopv)

# table and graph 
    gasBooster = pd.DataFrame(columns=['cycleNumber', 'inletPressure', 'copvPressure', 'copvMass', 'temperature'])
    
    booster = plt.figure()

    fig, ax1 = plt.subplots()
    ax1.set_xlabel('cycle #')
    ax1.set_ylabel('copv P (psi)')
    ax2 = ax1.twinx()
    ax2.set_ylabel('copv Temperature (C)')
    ax1.set_title('COPV Pressure (psi) and Temperature (C) vs Cycle #')
    
    # Gooster cycling
    while i <= 30:
        cycleNumber = i
        
        # Mass is removed from supply bottle
        m = (inletPressure * cycleV * molar_m) / (R * Ts)
        
        # Reassign Ts after loss of mass
        Ts = Ts - (m * cp) / (molar_m * pa * (v2 - cycleV)) + 273.15
        
        # Compression
        Tcompressed = ((-m * cp) / (molar_m * pa * (v2 - cycleV))) + 273.15 + Ts
        
        # Copv calculations
        Tcopv = ((copvMass * Tcopv) + (m * Tcompressed)) / (copvMass + m)
        outletPressure = ((copvMass + m) * R * Tcopv) / (molar_m * Vo)
        
        # Reassign values
        copvMass = copvMass + m  # Mass in copv
        Ms = Ms - m  # Supply mass
        
        # Converting back to psi/C
        inletP = inletPressure * 14.6959
        outletP = outletPressure * 14.6959
        copvTemp = Tcopv - 273.15
        
        # Plot copv P (psi)
        ax1.plot(cycleNumber, outletP, '.b', markersize=12)
        
        # Plot copv Temperature (C)
        ax2.plot(cycleNumber, copvTemp, '.r', markersize=12)
        
        # Add data to the table
        if i % 5 == 0:
            A = i // 5
            gasBooster.loc[A] = [cycleNumber, inletP, outletP, copvMass, copvTemp]
        
        i += 1
    
    plt.show()
    return gasBooster

# Example usage
supplyP_1 = 100
supplyV = 10
copvV = 5
temp = 25

result = gasBooster(supplyP_1, supplyV, copvV, temp)
print(result)



#emiliano questions:
#does it tell how fast to cycle pump (ultimate question trying to answer)

#2 phases: 0->2k phase (just what is in the 2k bottle) faster pressure climb
#2nd phase is pressing, using the pump 

#max operating pressure, max operating temp as parameter 
#write something for the first and second phase 

#how fast the cycles should be, time in between each open and close 
#first phase: time will be different because pressing faster 
# every time press COPV start out at 0 
#in some cases you are never going to go to phase 2 because you don't have to turn the pump on 
#current operating pressure might never reach 2k 
#machine learning (eventually lmao) get data, retune, do it again
#computation to improve automation 


