# DataTracker class to hold and plot data as needed

import numpy as np
import matplotlib.pyplot as plt
import constants as consts
from system_helpers import mdot_to_scfm


class DataTracker():
    def __init__(self):
        self._impulse = 0.0
        self._time = list()
        # Engine parameters
        self._mdot_liq_o = list()
        self._mdot_liq_f = list()
        self._c_star = list()
        self._isp = list()
        self._F_t = list()
        self._P_c = list()
        self._of_ratio = list()
        # Feed system parameters
        self._copv_P = list()
        self._ox_P = list()
        self._ox_T = list()
        self._ox_liq_v = list()
        self._ox_ullage_scfm = list()
        self._fuel_P = list()
        self._fuel_T = list()
        self._fuel_liq_v = list()
        self._fuel_ullage_scfm = list()
        
    def update_engine_data(self, mdot_o, mdot_f, c_star, F_t, P_c, C_F):
        self._mdot_liq_o.append(mdot_o)
        self._mdot_liq_f.append(mdot_f)
        self._c_star.append(c_star)
        self._isp.append(c_star*C_F/consts.g_0)
        self._F_t.append(F_t/1000)
        self._P_c.append(P_c/consts.PSI_TO_PA)
        self._of_ratio.append(mdot_o/mdot_f)
        
    def update_feed_data(self, copv_P: float, ox_params, fuel_params):
        self._copv_P.append(copv_P/consts.PSI_TO_PA/1000)
        # [ullage_P, ullage_T, prop_V] = params
        self._ox_P.append(ox_params[0]/consts.PSI_TO_PA)
        self._ox_T.append(ox_params[1])
        self._ox_liq_v.append(ox_params[2]/consts.L_TO_M3)
        self._ox_ullage_scfm.append(mdot_to_scfm(ox_params[3]))
        self._fuel_P.append(fuel_params[0]/consts.PSI_TO_PA)
        self._fuel_T.append(fuel_params[1])
        self._fuel_liq_v.append(fuel_params[2]/consts.L_TO_M3)
        self._fuel_ullage_scfm.append(mdot_to_scfm(fuel_params[3]))
        
    def update_counters(self, dt: float, step: float):
        self._time.append(dt*step)
        self._impulse += (self._F_t[-1]*1e3) * dt
        
    def get_end_string(self):
        output = f"Total impulse: {self._impulse/1e3:.2f} kN-s | "
        output += f"Residual LOX: {self._ox_liq_v[-1]*consts.L_TO_M3*consts.LOX_RHO:2f} kg | " 
        output += f"Residual fuel: {self._fuel_liq_v[-1]*consts.L_TO_M3*consts.RP1_RHO:.2f} kg"
        return output
        
    def plot_data(self):
        # Plot thrust with chamber pressure 
        fig1, axs1 = plt.subplots(3)
        fig1.suptitle("Engine Parameters")
        axs1[0].plot(self._time[1:], self._F_t[1:])
        axs1[1].plot(self._time[1:], self._P_c[1:])
        axs1[2].plot(self._time[1:], self._of_ratio[1:])
        axs1.flat[0].set(ylabel = "Thrust [kN]")
        axs1.flat[1].set(ylabel = "P_chamber [psia]")
        axs1.flat[2].set(ylabel = "O/F Ratio")
        axs1.flat[0].grid()
        axs1.flat[1].grid()
        axs1.flat[2].grid()
        axs1.flat[0].ticklabel_format(useOffset=False)
        plt.xlabel("Time [s]")
        
        fig2, axs2 = plt.subplots(3)
        fig2.suptitle("Ox Tank Parameters")
        axs2[0].plot(self._time, self._ox_P)
        axs2[1].plot(self._time, self._ox_T)
        axs2[2].plot(self._time, self._ox_liq_v)
        axs2.flat[0].set(ylabel = "P_ullage [psia]")
        axs2.flat[1].set(ylabel = "T_ullage [K]")
        axs2.flat[2].set(ylabel = "Propellant [L]")
        axs2.flat[0].grid()
        axs2.flat[1].grid()
        axs2.flat[2].grid()
        plt.xlabel("Time [s]")
        
        fig3, axs3 = plt.subplots(3)
        fig3.suptitle("Fuel Tank Parameters")
        axs3[0].plot(self._time, self._fuel_P)
        axs3[1].plot(self._time, self._fuel_T)
        axs3[2].plot(self._time, self._fuel_liq_v)
        axs3.flat[0].set(ylabel = "P_ullage [psia]")
        axs3.flat[1].set(ylabel = "T_ullage [K]")
        axs3.flat[2].set(ylabel = "Propellant [L]")
        axs3.flat[0].grid()
        axs3.flat[1].grid()
        axs3.flat[2].grid()
        plt.xlabel("Time [s]")
        
        fig4, axs4 = plt.subplots(3)
        fig4.suptitle("Other Parameters")
        axs4[0].plot(self._time, self._copv_P)
        axs4[1].plot(self._time, self._ox_ullage_scfm)
        axs4[2].plot(self._time, self._fuel_ullage_scfm)
        axs4.flat[0].set(ylabel = "P_COPV [ksia]")
        axs4.flat[1].set(ylabel = "vdot_ox [SCFM]")
        axs4.flat[2].set(ylabel = "vdot_fuel [SCFM]")
        axs4.flat[0].grid()
        axs4.flat[1].grid()
        axs4.flat[2].grid()
        plt.xlabel("Time [s]")
        
        fig5, axs5 = plt.subplots(2)
        fig5.suptitle("Performance")
        axs5[0].plot(self._time, self._c_star)
        axs5[1].plot(self._time, self._isp)
        axs5.flat[0].set(ylabel = "C* [m/s]")
        axs5.flat[1].set(ylabel = "Isp [s]")
        axs5.flat[0].grid()
        axs5.flat[1].grid()
        plt.xlabel("Time [s]")
