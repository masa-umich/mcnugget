# Heat Exchanger Starter Project
import numpy as np
import matplotlib.pyplot as plt
# import CoolProp.CoolProp as CP
# from pyfluids import Fluid, FluidsList, Input

IN_TO_M = 1/39.37
def f_to_kelvin(temp): return (temp-32)*(5/9)+273.15

# Inputs
class Tube:
    def __init__(self, od: float, id: float, T_wall_max: float):
        self.od = od*IN_TO_M
        self.id = id*IN_TO_M
        self.T_wall_max = f_to_kelvin(T_wall_max)


def get_steady_T_profile(tube: Tube, do_plot: bool = True):
    # Given inputs
    h_g = 0.7035*1000   # Convective heat transfer coefficient, [W/m^2K]
    T_c = 3327.96       # Combustion temperature, [K]
    k = 16.2            # Assuming a constant thermal conductivity for 304 SS, [W/m-K]
    L = 12*IN_TO_M      # Assuming 1-foot length of tube
    
    A_inner = 2*np.pi*(tube.id/2)*L
    Q_g = h_g*(T_c-tube.T_wall_max)*A_inner  # Overall heat from hot gas convection
    # Heat flux must be conserved throughout the tube radially
    radii = np.linspace(tube.id, tube.od, num=50)
    T_profile = tube.T_wall_max - Q_g*(np.log(radii/tube.id)/(2*np.pi*L*k))
    plt.plot(radii, T_profile)
    plt.xlabel("Radial distance [m]")
    plt.ylabel("Temperature [K]")
    Twc = np.min(T_profile)
    print("Temperature at inner wall: {} K".format(tube.T_wall_max))
    print("Temperature at outer wall: {} K".format(Twc))
    
    # Part 2: Getting h_cold (convective heat transfer coefficient at outer wall)
    A_outer = 2*np.pi*(tube.od/2)*L
    h_cold = (Q_g/A_outer)/(Twc - f_to_kelvin(70))
    print("Cold wall convective coefficient must be at least {} W/m^2K".format(h_cold))
    if do_plot: plt.show()
    
if __name__ == "__main__":
    tube = Tube(0.5, .46, 1500)
    get_steady_T_profile(tube, True)

