# 0 - Summary

In this RFC I will be detailing the autosequencing of the tanks as well as covering basic anomaly/failure cases of the tanks and pumps. 

only four possible states for the tanks:

# Tank Autosequencing Notes 
_**Changing from COPV (composite overwrapped pressure vessel) to tanks instead._  
# 1 - Vocabulary 

- _**Gas Booster**_: Colloquially known as "gooster". It is a pneumatic pump that is used to pressurize the tanks through pumping gass into the tanks. The model is Haskels AGD-32.
- _**Plumbing**_: The piping that connects the tanks to the gas booster and the valves.
- _**Valve**_: a device for controlling the passage of fluid or air through a pipe, duct, etc., especially an automatic device allowing movement in one direction only.
- _**Pressure Transducer**_: A device that measures the pressure of the gas in the tanks. 

# 2 - Motivation

We are writing this RFC to ensure that the autosequencing of the tanks is well documented and that the failure cases are well documented to prevent any injuries or damage in the future.

the autosequence is used to pressurize the tank efficiently and effectively for use in the rocket. things that are repetitive and pedantic, take out human error and make it automated. 

# 3 - Requirements -> expected inputs and expected outputs 
missing the most important requirement: 
authomate pressurization of the tanks, there is no mention of pressurization!!
- have the state machine should not be part of requirements
- have a configurable pressurization rate 
- press all the tanks at the same rate? (no!)
- what if we open the pressurization valve, the tank pressure doesn't rise? how to respond 
- open the valve, when pt reads certain value you close it 

The requirements for the autosequencing of the tanks are as follows:

## 3.1 Pressure Transducer
When the _**pressure transducer (PT)**_ is no longer reading correctly, regardless of operational state (hold or press), the appropriate action is to close the press valve and open the vent valve to release all pressure.

## 3.2 Valve Control 

### 3.2.1: 
In the event that the _**press valve**_ stops responding, move directing to the vent state. 
  
### 3.2.2:
In the event that the _**relief valve**_ stops responding, move directly to the vent state by closing the press valve and opening the vent valve **invalid logic 
   
### 3.2.3: 
In the event that the _**vent valve**_ responding, close the press valve immediately 
  
## 3.3 Plumbing 
  
### 3.3.1:
In the event of the _**tank rupturing or leaking**_ above the press rate, close the press valve and open the vent valve. 

### 3.3.2:
In the event that the _**plumbing leak rate**_ is faster than the press rate, move directly to the vent state by closing the press valve and opening the vent valve 

# 4 - Design -> how to get from input to the expected output

i.e. if a pt reads an anomalous reading, vent the tank
what is a anomalous reading? what does it mean to vent the tank 

## 4.1 Pressure Transducer
For a _**Pressure Transducer**_  to not be reading correctly when it is reading a pressure that is not within the expected range. The expected range is 0-[range max here] psi. If the _**Pressure Transducer**_ is reading a pressure that is not within the expected range, the appropriate action is to close the press valve and open the vent valve to release all pressure.
- negative pressures are physically impossible 
- maximum pressure specification
- consistently reads bad values for a certain duration of time how many values, how long of a duration

## 4.2 Valve Control 
### 4.2.1.0:
In the event that the _**press valve**_ is normally closed, if a failure where the press valve does not respond, move directly to the vent state by closing the press valve and opening the vent valve.
doesn't actuate
have multiple 
valve enable command, valve enable -> acknowledges if it was received in actuator or not
two channel feedback loop, feedback loop fails?
overpressure and then go into abort scenario 


### 4.2.1.1: 
In the event that the press valve will always be normally open and will only close when the tank is being pressurized. If a failure where the press valve does not respond, move directly to the vent state by closing the press valve and opening the vent valve.

at which point do we see fuck it, return control to operator? 

### 4.2.2:
In the event that the _**relief valve**_ stops responding, move directly to the vent state by closing the press valve and opening the vent valve is not actuated, it is like when it reaches a certain pressure it will relieve itself 

no response in a relief valve 

### 4.2.3:
In the event that the _**vent valve**_ responding, close the press valve immediately
vent valve can be normally closed or normally open, think of scenarios for each 

## 4.3 Plumbing 
### 4.3.1:
In the event of the _**tank rupturing or leaking**_ above the press rate, close the press valve and open the vent valve.

### 4.3.2:
In the event that the _**plumbing leak rate**_ is faster than the press rate, move directly to the vent state by closing the press valve and opening the vent valve


![img](../img/gmfu2.png)
![img](./../img/gmfu.png)
![img](./../img/np.png)