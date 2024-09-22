# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
#-----------------------------------------------------------------------------

import math

def get_mass_flow(dp,cda,rho):
    mdot = cda*math.sqrt(2*dp*rho)
    return mdot


mdot = get_mass_flow(1,1,1)

print(mdot)

#----------------------------Variables----------------------------------------

#Radius in inches
radius = 0.1875 

#Conversion from inches to meters
MeterRadi = radius * 0.0254

#print('Radius is', MeterRadi)
#^^^ this is a tester to check the conversion 

MeterDiam = MeterRadi * 2

#print('Diameter is', MeterDiam)
#^^^ this is a tester to check the conversion 

math.pi
# ^^^ gives pi from import math 

AreaM = math.pi * MeterRadi**2
#^^^ units in meters squared

#print('Area is', AreaM)
#^^^ this is a test for the area

Gamma = 1.4

Cv = .1

R = 297
#^^^ Gas Constant

T = 300
#^^^ Temp in Kelvin 

P2 = 14
# Pressure 2 in PSI

DarcyFactor = 0.05

PressureRatio = (2 / 2.4)**3.5

#print('PRatio is', PressureRatio)
#^^^ this is a tester to check the ratio

#-----------------------------Cd Values---------------------------------------

ChamCd = 1 / (math.sqrt(.57))

SPipeIVCd = 1 / (math.sqrt(6.4))

Bendk = ((.42 * math.sin(math.pi / 4)) + 2.56 * math.sin(math.pi / 4)**3)

EBendCd = 1 / math.sqrt(Bendk)

SPipeIIICd = 1 / (math.sqrt(4.8))

ValveCv = .1
 
OutletCd = 1 / (math.sqrt(1))

#----------------------------CdA Vslues---------------------------------------

ChamCdA = ChamCd * AreaM
#continue adding CdA values and begin massflowcalcs

#----------------------Unchoked Formula Shortcuts-----------------------------

RxT = R * T
#RT constant

#print('RTconstant is', RxT)

GamFormula = ((2 * Gamma) / (Gamma - 1))

#print('Gam is', GamFormula)
#^^^ this is a test for gam 

Bracket5000 = (((4000 / 5000)**(2 / Gamma)) - ((4000 / 5000)**((Gamma + 1) / Gamma)))
#5000 PSI short cut

Bracket4000 = (((3000 / 4000)**(2 / Gamma)) - ((3000 / 4000)**((Gamma + 1) / Gamma)))
#4000 PSI short cut

Bracket5000 = (((2000 / 3000)**(2 / Gamma)) - ((2000 / 3000)**((Gamma + 1) / Gamma)))
#3000 PSI short cut

Bracket5000 = (((1000 / 2000)**(2 / Gamma)) - ((1000 / 2000)**((Gamma + 1) / Gamma)))
#2000 PSI short cut

Bracket5000 = (((100 / 1000)**(2 / Gamma)) - ((100 / 1000)**((Gamma + 1) / Gamma)))
#1000 PSI short cut

Bracket5000 = (((14 / 100)**(2 / Gamma)) - ((14 / 100)**((Gamma + 1) / Gamma)))
#100 PSI short cut

rho5000 = 5000 / RxT
#units in psi

rho4000 = 4000 / RxT
#units in psi

rho3000 = 3000 / RxT
#units in psi

rho2000 = 2000 / RxT
#units in psi

rho1000 = 1000 / RxT
#units in psi

rho100 = 100 / RxT
#units in psi

Pascals5000 = rho5000 * 6894.76
#converts psi -> pascals

Pascals4000 = rho4000 * 6894.76
#converts psi -> pascals

Pascals3000 = rho3000 * 6894.76
#converts psi -> pascals

Pascals2000 = rho2000 * 6894.76
#converts psi -> pascals

Pascals1000 = rho1000 * 6894.76
#converts psi -> pascals

Pascals100 = rho100 * 6894.76
#converts psi -> pascals


#---------------------Choked Formula Shortcuts--------------------------------

SqrtSC = math.sqrt(Gamma / RxT)
#short cut for the square root piece

#print('Square Root is', SqrtSC)
#^^^ this is a test for the sqrt function inside the formula

ParenthesisSC = (2 / (Gamma + 1))
# shortcut

ExponentSC = ((Gamma + 1) / (2 * (Gamma - 1)))
# shortcut

ParentExpo = ParenthesisSC**ExponentSC
# shortcut

#print('ParenthesisCubed', ParentExpo)
# this is a test for ParentExpo

#-----------------------------------------------------------------------------