import synnax as sy
import numpy as np
import matplotlib.pyplot as plt
from mcnugget.client import client


# unit conversions
m = 1/39.37 #1 m = 39.071 inches
Pa = 6894.7572931783 #1 psi = 6894.7572931783 Pa

# fuel flowmeter dimensions
inlet_d_in = 0.6202 #in
throat_d_in = 0.4005 #in

inlet_d = inlet_d_in * m #m
throat_d = throat_d_in * m #m

# l stand dimensions
level_height_in = 7.75 #in
l_stand_id_in = 7.5 #in
l_stand_height_in = 46.446 #in

level_height = level_height_in * m #m
l_stand_id = 7.5 * m #m
l_stand_height = l_stand_height_in * m #m

# fluid properties - water
rho = 1000 #kg/m^3
dyn_visc = 0.001 #Pa * s

#mass flow rate function
# def flow_rate(inlet_diameter,throat_diameter,density,dP):
    # mdot = (inlet_diameter*np.pi())*np.sqrt((2/density)*dP)/((inlet_diameter/throat_diameter)^2-1)*density

# TR = sy.TimeRange(1678042983002521300, 1678042991250027500) ## update this

# Feb 4th Test #s and Times
# TR1 = sy.TimeRange(1707070834781453800, 1707070847346782000) #real test #1

# data = client.ranges.retrieve("Feb 4 Flowmeter Test")


data = client.ranges.create(
    name="BB TPC Feb 11 Test #1",
    time_range = sy.TimeRange(1707673090101871400, 1707673098882826800),
    retrieve_if_name_exists=True
)




def mass_flow_rate(
    dP: np.array,
    inlet_diameter: float,
    throat_diameter: float,
    density: float,
):
    inlet_area = (np.pi)*(inlet_diameter/2)**2
    throat_area = (np.pi)*(throat_diameter/2)**2
    square_root = (2/density)*dP*(1/(((inlet_area/throat_area)**2)-1))
    return (inlet_area*np.sqrt(square_root)*density)
    
# test = mass_flow_rate(40*Pa, 0.6202*m, 0.4005*m, 1000)
# print(40*Pa, 0.6202*m, test)

TIME = "gse_ai_time"
INLET = "gse_ai_9"
THROAT = "gse_ai_10"

data_2 = client.read(sy.TimeRange(1707070831313725200, 1707070831313725200), [TIME, INLET, THROAT])

print(sy.TimeStamp(data_2[TIME][0]), sy.TimeStamp(data_2[TIME][-1]))

plt.plot(sy.elapsed_seconds(data_2[TIME]), data_2[INLET])
plt.show()

INLET = data[INLET].to_numpy()
#INLET = np.convolve(INLET, np.ones(100)/100, mode="same")

Time = sy.elapsed_seconds(data[TIME])

plt.plot(Time, INLET)
plt.show()


'''if __name__ == "__main__":
    Time = sy.elapsed_seconds(data[TIME])
    # DP_raw = DATA["gse.pressure[15]"]  # psi * 10
    dP_Pa = (data[INLET]-data[THROAT] )*Pa #delta p in Pa

    mdot_1 = mass_flow_rate(dP_Pa, inlet_d, throat_d, rho)
    plt.plot(Time, mdot_1)
    plt.show()

'''