import numpy as np
from synnax.hardware.ni.types import AIVoltageChan, TableScale

def computeTemperature(mv):
    if -6.3 <= mv < -4.648:
        constants = [-192.43000, -5.4798963, 59.572141, 1.9675733, -78.176011, -10.963280, 0.27498092, -1.3768944, -0.45209805]
    elif -4.648 <= mv < 0.0:
        constants = [-60.0, -2.1528350, 30.449332, -1.2946560, -3.0500735, -0.19226856, 0.0069877863, -0.10596207, -0.010774995]
    elif 0.0 <= mv < 9.288:
        constants = [135.0, 5.9588600, 20.325591, 3.3013079, 0.12638462, -0.00082883695, 0.17595577, 0.0079740521, 0.0]
    elif 9.288 <= mv < 20.872:
        constants = [300.0, 14.861780, 17.214707, -0.93862713, -0.073509066, 0.0002957614, -0.048095795, -0.0047352054, 0.0]
    else:
        return -1

    T0, V0, p1, p2, p3, p4, q1, q2, q3 = constants

    numerator = (mv - V0) * (p1 + (mv - V0) * (p2 + (mv - V0) * (p3 + p4 * (mv - V0))))
    denominator = 1 + (mv - V0) * (q1 + (mv - V0) * (q2 + q3 * (mv - V0)))
    return T0 + (numerator / denominator)

def process_tc_poly():
    voltage_range = (-6.3, 20.872)
    num_points = 100
    voltages = np.linspace(voltage_range[0], voltage_range[1], num_points)
    volt_lst = list(voltages)

    temp_lst = []
    for mv in voltages:
        temp_lst.append(computeTemperature(mv))

    return volt_lst, temp_lst

def configure_tc_channel(analog_task, row, analog_card):
    volt_lst, temp_lst = process_tc_poly()

    tc_channel = AIVoltageChan(port=row["Port"], channel=row["Channel"], device=analog_card.key)
    tc_channel.units = "Volts"
    tc_channel.custom_scale = TableScale(pre_scaled_vals=volt_lst, scaled_vals=temp_lst, pre_scaled_units="Volts")
    analog_task.config.channels.append(tc_channel)
    print("Added TC channel")