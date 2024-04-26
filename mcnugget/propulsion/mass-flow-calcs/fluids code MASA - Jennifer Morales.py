# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
# calculations for choked mass flow 
import math

# Cd for chamber 
cd = 1/math.sqrt(0.57)

pi = math.pi
radius = 0.1875 * 0.0254 
print(radius)
area = pi*((radius)**2)
print(area)
cda = cd * area
print(cda)

#pressure in psi
psi1 = 5000
psi2 = 4000
psi3 = 3000
psi4 = 2000
psi5 = 1000
psi6 = 100
psi7 = 14

#pressure in pascals 
p1 = psi1 * 6894.76 
print(p1)
p2 = psi2 * 6894.76
print(p2)
p3 = psi3 * 6894.76
print (p3)
p4 = psi4 * 6894.76
print (p4)
p5 = psi5 * 6894.76
print(p5)
p6 = psi6 * 6894.76
print(p6)
p7 = psi7 * 6894.76

RT = 297*300
print(RT) 

#exponent 
e = 2 / 1.4
print (e)

#parentheses 
bp = psi2 / psi1
print (bp)

bp2 = psi3 / psi2
print (bp2) 

bp3 = psi4 / psi3
print (bp3)

bp4 = psi5 / psi4
print (bp4) 

bp5 = psi6 / psi5
print (bp5)

bp6 = psi7 / psi6 
print (bp6)

#bracket psi 
bpsi1 = (((bp)**(e))-((bp)**(e)))
print (bpsi1)s

bpsi2 = (((bp2)**(e))-((bp2)**(e)))
print(bpsi2)

bpsi3 = (((bp3)**(e))-((bp3)**(e)))
print(bpsi3)

bpsi4 = (((bp4)**(e))-((bp4)**(e)))
print(bpsi4)

bpsi5 = (((bp5)**(e))-((bp5)**(e)))
print(bpsi5)

bpsi6 = (((bp6)**(e))-((bp6)**(e)))
print(bpsi6)

#rho values in pascals 
rho1 = p1/RT
print(rho1)
rho2 = p2/RT
print(rho2)
rho3 = p3/RT
print(rho3)
rho4 = p4/RT
print(rho4)
rho5 = p5/RT
print(rho5)
rho6 = p6/RT
print(rho6)


sqrt = math.sqrt(1.4/RT)
print(sqrt)
p = (2/2.4)**3
print(p)

#CD value for 90 bend 
bend= 1/math.sqrt(0.42*math.sin(90/2))+(2.56*math.sin(90/2)**3)
print (bend)

# mass flow for chamber 
def get_mass_flow(dp,cda,rho):
    mdot = cda*math.sqrt(2*dp*rho)
    return mdot

mdot = get_mass_flow(1,1,1)

print(mdot)


# mass flow for straight pipe (4ft)    
# Length = 4ft --> 48 in
def get_mass_flow_straight4(dp,cda,rho,L):
    mdot = cda*math.sqrt(2*dp*rho*L)
    return mdot

mdot = get_mass_flow_straight4(0.05,1,1,48)

print(mdot)


# mass flow at bend of pipe 
def get_mass_flow_bend(dp,cda,rho):
    mdot = cda*math.sqrt(2*dp*rho)
    return mdot

mdot = get_mass_flow_bend(1,1,1)

print(mdot)


# mass flow for straight pipe (3ft)
# Length = 3ft --> 36 in
def get_mass_flow_straight3(dp, cda, rho, L):
    mdot = cda*math.sqrt(2*dp*rho*L)
    return mdot

mdot = get_mass_flow_straight3(1,1,1,36)

print(mdot)


# mass flow for valve 
def get_mass_flow_valve(dp, cda, rho, cV):
    mdot = cda*math.sqrt(2*dp*rho*cV)
    return mdot

mdot = get_mass_flow_valve(1,1,1,1)

print(mdot)

# mass flow for outlet 
def get_mass_flow_outlet(dp,cda,rho):
    mdot = cda*math.sqrt(2*dp*rho)
    return mdot

mdot = get_mass_flow_outlet(1,1,1)

print(mdot)



# calculations for unchoked mass flow 

# mass flow for chamber 
def get_unchoked_mass_flow(cda,p1,p2,R,T):
    mdot = cda*math.sqrt(2+5)
    return mdot

mdot = get_unchoked_mass_flow(1,5000,4000,297,300)

print(mdot)

# mass flow for straight pipe (4ft)
def get_unchoked_mass_flow(cda,p1,p2,R,T):
    mdot = cda*math.sqrt((2*1.4/0.4)*R*T*((p2/p1)**2/1.4)-((p2/p1)**7))
    return mdot



print(mdot)


    













