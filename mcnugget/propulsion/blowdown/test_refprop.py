# This example code is derived from:
# https://github.com/usnistgov/REFPROP-wrappers/blob/master/wrappers/python/notebooks/Tutorial.ipynb
# 19 October, 2023

import os, numpy as np
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary


def NBP():
    RP = REFPROPFunctionLibrary(os.environ["RPPREFIX"])
    RP.SETPATHdll(os.environ["RPPREFIX"])
    print("REFPROP Version {}".format(RP.RPVersion()))
    MASS_BASE_SI = RP.GETENUMdll(0, "MASS BASE SI").iEnum
    PA_TO_PSI = 0.0001450377

    p1 = 500 / PA_TO_PSI  # 500 [psi]
    T1 = 298  # Room temperature [K]
    vol = RP.REFPROPdll(
        "Nitrogen", "PT", "V", MASS_BASE_SI, 0, 0, p1, T1, [1.0]
    ).Output[0]
    energy = RP.REFPROPdll(
        "Nitrogen", "PT", "E", MASS_BASE_SI, 0, 0, p1, T1, [1.0]
    ).Output[0]
    print("--- Initial State ---")
    print("Density: {} kg/m^3".format(1 / vol))
    print("Energy: {} J/kg".format(energy))
    print(f"Pressure: {p1*PA_TO_PSI} psi | Temperature: {T1} K")

    print("Now, increasing the volume by 1 liter and getting the new internal energy:")
    dV = 0.001
    new_vol = vol + dV
    energy2 = energy - p1 * dV  # dE = Q-W, work done = p1*dV for small dV
    p2 = RP.REFPROPdll(
        "Nitrogen", "ED", "P", MASS_BASE_SI, 0, 0, energy2, (1 / new_vol), [1.0]
    ).Output[0]
    T2 = RP.REFPROPdll(
        "Nitrogen", "ED", "T", MASS_BASE_SI, 0, 0, energy2, (1 / new_vol), [1.0]
    ).Output[0]
    print(f"(New) Density: {1/new_vol} kg/m^3")
    print(f"(New) Energy: {energy2} J/kg")
    print(f"(New) Pressure: {p2*PA_TO_PSI} psi | (New) Temperature: {T2} K")


if __name__ == "__main__":
    os.environ["RPPREFIX"] = r"/home/jasonyc/masa/REFPROP-cmake/build"
    NBP()
