"""
Calculates the Steinhardt-Hart coefficients for thermistor conversions.
See `https://github.com/masa-umich/gse-driver/blob/main/gse-driver/daq/thermistor.cpp`
Evan Eidt our savior <o~o>
"""

import math

inversion_0 = 1 / (0 + 273.15)
inverstion_25 = 1 / (25 + 273.15)
inversion_50 = 1 / (50 + 273.15)

ln_0 = math.log(32650)
ln_25 = math.log(10000)
ln_50 = math.log(3603)

sh_0 = ln_0**3 - ln_25**3
sh_2 = ln_25**3 - ln_50**3
sh_1 = (inversion_0 - inverstion_25) / sh_0
sh_1 = sh_1 - (inverstion_25 - inversion_50) / sh_2
sh_1 = sh_1 / ((ln_0 - ln_25) / sh_0 - (ln_25 - ln_50) / sh_2)

sh_0 = ln_0**3 - ln_50**3
sh_2 = (inversion_0 - inversion_50) / sh_0 - sh_1 * (ln_0 - ln_50) / sh_0

sh_0 = inverstion_25 - sh_1 * ln_25 - sh_2 * ln_25**3

print(sh_0, sh_1, sh_2)
