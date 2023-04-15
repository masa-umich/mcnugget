import numpy as np
import scipy.stats as st
import math as m

class st_ops:
    def t_interval(data, sig_level):  
        df = len(data) - 1
        # sig_level = 
        mean = np.mean(data)
        c_interval = st.t.interval(sig_level, df, np.mean(data), st.sem(data))
        return np.array(c_interval)

    def delta_t(data, sig_level):
        df = len(data) - 1
        tCV = st.t.ppf(sig_level, df) # t critical value 
        s = st.sem(data) # standard deviation of the mean 
        tDelta = tCV * (s/(m.sqrt(len(data))))
        return tDelta
        
##calling upon t interval function 
#create a function called valve_delay that calls t_interval twice, one for lox and one for fuel

def valve_delay(lox_data, fuel_data, sig_level):
    lox_delay = st_ops.t_interval(lox_data, sig_level)
    fuel_delay = st_ops.t_interval(fuel_data, sig_level)
    
    #two intervals to get the delta inside your valve_delay function
    lox_m = np.mean(lox_data)
    fuel_m = np.mean(fuel_data)

    lox_d = st_ops.delta_t(lox_data, sig_level)
    fuel_d = st_ops.delta_t(fuel_data, sig_level)

    cian_mtd = fuel_m - lox_m - fuel_d - lox_d
    return cian_mtd

    #or you can just subtract the lower bound of fuel by the upper bound of lox 
    other_mtd = fuel_delay[0] - lox_delay[1]
    return other_mtd





