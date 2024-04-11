# Enumerates known constants

# Unit conversions
IN_TO_M = 1/39.37
PSI_TO_PA = 6894.757
L_TO_M3 = 0.001
FT_TO_M = 1/3.281
LBM_TO_KG = 1/2.20462
KGM3_TO_LBCF = 0.062428
# Converting SCFM is tricky: "standard" is actually at 68 F and 1 atm
GN2_RHO_STD = 1.1648342                 # [kg/m^3]
GN2_RHO_IMP = GN2_RHO_STD*KGM3_TO_LBCF  # [lbm/ft^3]

# Known values
RP1_RHO = 790   # Typically 810 to 1020 [kg/m^3]
LOX_RHO = 1140  # At boiling point [kg/m^3]
GN2_R = 296.80  # Specific gas constant [J/kg K]
g_0 = 9.80665   # Gravitational acceleration [m/s^2]
