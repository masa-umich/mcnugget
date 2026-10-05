# Simulation

Naive fluid & pressure simulation for verifying autosequence logic

Only supports pretty basic behavior as of now, feel free to enhance with things like combustion or configurable fluid types in the future.

## Usage
1. Must be running an active Synnax server. Go to their docs to find out how to install and setup for your OS: \
https://docs.synnaxlabs.com/reference/core/quick-start \
Note: If your simulation has 50+ channels you will need to also start this with our Synnax key
2. Run this script with uv:
```bash
uv run main.py -a <alias file> -s <sim params file>
```
Built-in example:
```bash
uv run main.py -a aliases.yaml -s sim-profiles/press-fill/press-fill.yaml
```
The corresponding Synnax project with PNID and plots can be found in the `sim-profiles/press-fill/` directory as well.

Valid alias and sim profile examples can be found in the sample files as well.

In some cases you may have to make fake volumes for the system to behave correctly or to attach instrumentation to the correct sections. For example, in the press-sim profile there is a "press fill manifold" which does not exist in real life, but exists so that there is some intermediate space between the 6k bottles and COPV, in reality there are only some pipes.

## Physics Simulation Details

`simulation_step(dt)` advances by `dt` seconds, subdividing large steps for
stability. Tank capacities stay fixed while gas amounts change.

Open valves transfer gas from higher to lower pressure; check valves only allow
inlet-to-outlet flow. The approximate transfer is
`Δn = 1000 * flow_coefficient * |ΔP| * P_atm * dt / (R * T_source)`.
Flow speed is assumed proportional to pressure difference. Pressure follows
`P_abs = nRT / V`, using moles, liters, kelvin, and
`R = 1.20591 psi·L/(mol·K)`. Gauge pressure is `P_abs - 14.6959 psi`.

Transferred gas carries energy `ΔU = Cp * T_source * Δn` between tanks.
Temperature follows `T = U / (nCv)`, with `Cv = 8.31446 / (γ - 1)` J/(mol·K)
and `Cp = γCv`. The default `γ = 1.4` approximates nitrogen.

With temperature simulation enabled, temperature relaxes toward ambient using
`T_new = T_ambient + (T - T_ambient) * exp(-dt / τ)`.
`thermal_equilibrium_time_constant` sets `τ` in seconds; larger values mean
slower settling. If omitted or `null`, `τ = nCv / heat_transfer_coefficient`.
Cooling lowers pressure even with closed valves. Disabling temperature
simulation holds temperatures constant.

Assumptions: ideal gas, uniform tank temperatures, fixed ambient temperature,
and an unlimited atmosphere reservoir. No real gas effects, choked flow, or
separate wall temperatures.

## TODO
 - [x] Reconfigurable simulation profiles with config files
 - [x] Temperature simulation (basic ideal gas law)
 - [ ] Option to automatically start a corresponding Synnax cluster while the script is running using Podman/Docker
 - [ ] Add a "Reset/Reload Sim" channel which just resets and reloads the simulation profile back to initial conditions without restarting the script
 - [ ] Configurable fluid types in config using coolprop
 - [ ] Some sort of very basic combustion simulation: \
       *Maybe just a bool in the sim profile that makes a volume's pressure & temperature increase when gas is transferred into it beyond equalibrium.*
 - [ ] More comprehensive and up-to-date example simulation profile of full system
