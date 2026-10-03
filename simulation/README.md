# Simulation

## Usage
Run with:
```bash
uv run main.py -a <alias file> -s <sim params file>
```

Container support coming eventually

## Temperature simulation

With `do_temp_simulation: true`, gas transfer carries energy between tanks and
pressure follows the ideal gas law. `gas_specific_heat_ratio` defaults to `1.4`
for nitrogen. The previous `5/3` assumption described a monatomic gas and, with
no heat loss, drove an initially atmospheric tank toward roughly 215 C when
filled with gas at 20 C.

The gas now also exchanges heat with a fixed wall/environment temperature set
by `ambient_temperature` (default 20 C). `default_heat_transfer_coefficient`
(default 10 W/K) sets the effective thermal conductance. Larger values produce
less heating during filling and faster recovery toward ambient after filling
or venting. Set it to zero for an adiabatic model. Override individual tanks
with a `heat_transfer_coefficients` mapping, for example `copv: 20`.

Heat exchange uses `Q_dot = conductance * (ambient_temperature - temperature)`
and gas heat capacity `n * R / (gamma - 1)`, so a tank's thermal response changes
as its gas inventory changes. Cooling is integrated exponentially to remain
stable for large time steps, and pressure is recalculated without changing
the gas amount. These conductances are tuning parameters, not measured tank
properties. The model does not separately simulate wall or sensor temperatures;
all thermocouples on a volume report its gas temperature. With temperature
simulation disabled, temperatures remain constant.
