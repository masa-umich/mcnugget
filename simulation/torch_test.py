from pathlib import Path
from simulation import Simulation

sim = Simulation(Path("sim-profiles/torch/torch.yaml"), Path("sim-profiles/torch/torch-aliases.yaml"))
chamber = next(v for v in sim.volumes if v.name == "torch chamber")

sim.set_valve_state("gse_vlv_2", True)  
sim.set_valve_state("gse_vlv_4", True)
sim.set_valve_state("gse_vlv_1", True)  # open Ox MPV
sim.set_valve_state("gse_vlv_3", True)  # open Fuel MPV

for i in range(100):  
    sim.simulation_step(0.02)
    if i % 10 == 0:
        print(f"t={i * 0.02:.2f}s  chamber={chamber.pressure:.1f} psi")