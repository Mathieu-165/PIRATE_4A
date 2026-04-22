# Python Modules 
from pprint import pprint

import numpy as np
import time  

# Fluent Modules
import ansys.fluent.core as pyfluent

# Location of Fluent 2026 R1 (v261)
import os

# Path management setup
base_dir = os.getcwd()

# Define dynamic paths
autosave_dir = os.path.join(base_dir, "autosave_securite", "4deg")
export_pv_dir = os.path.join(base_dir, "export_pv", "4deg")
export_forces_dir = os.path.join(base_dir, "export_forces")
config_dir = os.path.join(base_dir, "configurations")

# Create directories if they don't exist
os.makedirs(autosave_dir, exist_ok=True)
os.makedirs(export_pv_dir, exist_ok=True)
os.makedirs(export_forces_dir, exist_ok=True)
os.makedirs(config_dir, exist_ok=True)

def to_fluent_path(path):
    """Convert Windows paths to Fluent-compatible paths."""
    return path.replace("\\", "/")

#==============================================================
# region ⚠️ ADAPTATION OF FLUENT PATH
#==============================================================

exact_fluent_path = r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent"
os.environ["PYFLUENT_FLUENT_ROOT"] = exact_fluent_path

#==============================================================
# region 1. FLOW CONDITIONS
#==============================================================

M = 0.5 # Mach number
# Altitude = 10000 ft
T = 268.15 # K
P = 69682 #Pa
R = 287.04 # J/kg/K
GAMMA = 1.4 
RHO = P / (R * T) # kg/m3
MU = 1.46e-6 * T**1.5 / (T + 110.4) # Pa.s
L = 1 # m Airfoil chord

a = (GAMMA * R * T) ** 0.5 # m/s
u = M * a # m/s
REYNOLDS = RHO * u * L / MU

print('\n----- Flow Conditions -----')
print(f'Mach: {M}')
print(f'Farfield static temperature: {T} K')
print(f'Farfield static pressure: {P} Pa')
print(f'Flow velocity: {u:.2f} m/s')
print(f'Reynolds: {REYNOLDS:.2e}')
print('Airfoil NACA 2414')
print('Angle of attack: 4°')

#==============================================================
# region 2. STARTING FLUENT AND LOADING THE MESH
#==============================================================

print("\nStarting Fluent in solver mode with 4 cores, double precision, 2D...")
solver = pyfluent.launch_fluent(precision="double", #double precision
                                processor_count=4, #number of cores
                                mode="solver", #background
                                start_timeout=120, #120s to start Fluent
                                dimension=2,
                                cwd=base_dir) #2D

print("\nLoading mesh...")
solver.tui.file.read_case("meshs/mesh_4deg.msh")
print("\nMesh loaded successfully.")

#==============================================================
# region 3. GENERAL CONFIGURATION AND PHYSICAL MODELS
#==============================================================

print("\nGeneral configuration...")

# Physical model: compressible flow (modern API)
solver.settings.setup.general.solver.type = "pressure-based"
solver.settings.setup.general.solver.time = "transient"
solver.settings.setup.models.energy.enabled = True # Enable energy

# Turbulence model: k-w-SST (modern API)
solver.settings.setup.models.viscous.model = "k-omega" 
solver.settings.setup.models.viscous.k_omega_model = "sst"

# Fluid properties: air
solver.settings.setup.materials.fluid['air'].density.option = "ideal-gas" #Ideal gas
solver.settings.setup.materials.fluid['air'].viscosity.option = "sutherland" #Sutherland viscosity

solver.setup.cell_zone_conditions.fluid["fluid-pi_ce-corps_surfacique"].material = "air"

#==============================================================
# region 3. BOUNDARY CONDITIONS
#==============================================================

print("\nConfiguring boundary conditions...")

solver.settings.setup.general.operating_conditions.operating_pressure = P

# --- INLET ---
solver.tui.define.boundary_conditions.zone_type("inlet", "velocity-inlet")
inlet = solver.setup.boundary_conditions.velocity_inlet['inlet']
inlet.momentum.vmag = u                                  # Momentum tab
inlet.turbulence.turb_intensity = 0.001                  # Turbulence tab
inlet.turbulence.turb_viscosity_ratio = 10              # Turbulence tab
inlet.thermal.temperature = T                                     # Thermal tab

# --- OUTLET ---
solver.tui.define.boundary_conditions.zone_type("outlet", "pressure-outlet")
outlet = solver.setup.boundary_conditions.pressure_outlet['outlet']
outlet.momentum.gauge_pressure = 0.0                      # Momentum tab
outlet.turbulence.turb_intensity = 0.001                  # Turbulence tab
outlet.turbulence.turb_viscosity_ratio = 10               # Turbulence tab
outlet.thermal.backflow_total_temperature = T             # Thermal tab

# --- MOVING WALLS ---
walls = solver.setup.boundary_conditions.wall['moving_walls']
walls.momentum.motion_bc = "Moving Wall"                  # Momentum tab
walls.momentum.vmag = u                                   # Momentum tab
walls.momentum.shear_bc = "No Slip"                       # Momentum tab
walls.momentum.direction = [1.0, 0.0]                     # Momentum tab

#==============================================================
# region 4. SOLUTION CONTROL AND SOLUTION STRATEGY
#==============================================================

print("\nConfiguring discretization schemes...")
# Discretization schemes
solver.solution.methods.p_v_coupling.flow_scheme = "Coupled" # Coupled scheme
solver.solution.methods.gradient_scheme = "least-square-cell-based"
solver.settings.solution.methods.transient_formulation = "unsteady-2nd-order"

# Convergence criteria
print("\nConfiguring convergence criteria...")
solver.solution.monitor.residual.equations['continuity'].absolute_criteria = 1e-4
solver.solution.monitor.residual.equations['x-velocity'].absolute_criteria = 1e-4
solver.solution.monitor.residual.equations['y-velocity'].absolute_criteria = 1e-4
solver.solution.monitor.residual.equations['energy'].absolute_criteria = 1e-6
solver.solution.monitor.residual.equations['k'].absolute_criteria = 1e-6
solver.solution.monitor.residual.equations['omega'].absolute_criteria = 1e-6

#==============================================================
# region 5. SIMULATION SETUP 
#==============================================================

print("\nInitializing the simulation: standard from the inlet...")

# Standard initialization
solver.solution.initialization.initialization_type = "standard"
solver.tui.solve.initialize.compute_defaults.velocity_inlet("inlet")
solver.solution.initialization.standard_initialize() # Standard initialization

# Simulation parameters
solver.settings.solution.run_calculation.transient_controls.time_step_size = 0.005 # s

#==============================================================
# region 6. BACKUP AUTOSAVE
#==============================================================
print("\nConfiguring backup autosave...")

autosave = solver.settings.file.auto_save

autosave.save_data_file_every = {
    "frequency_type": "time-step", 
    "save_frequency": 100
}
autosave.retain_most_recent_files = True
autosave.max_files = 3

autosave.root_name = to_fluent_path(os.path.join(autosave_dir, 'autosave_4deg'))

#==============================================================
# region 7. EXPORTING RESULTS FOR PARAVIEW
#==============================================================
# print("\nConfiguring export for ParaView...")

# import os

# # 1. We get the dynamic path 
# current_folder = os.getcwd()
# export_folder = os.path.join(current_folder, "export_pv", "4deg")

# # 2. We physically create the folder
# os.makedirs(export_folder, exist_ok=True)

# # 3. We create the full name of the final file
# full_path = os.path.join(export_folder, "export4deg")

# # 4. We replace all Windows \ with / for Fluent!
# fluent_path = full_path.replace("\\", "/")

# solver.settings.solution.calculation_activity.automatic_exports.visualize.create(name="export")
# export = solver.settings.solution.calculation_activity.automatic_exports.visualize["export"]

# export.set_state({
#     'file_name': fluent_path,
#     'frequency': 2,
#     'frequency_of': 'Time Step',
#     'cell_centered': True,
#     'scope': 'surface-select',
#     'cell_zones': None,
#     'surfaces': ['interior-pi_ce-corps_surfacique', 'interior-5'],
#     'quantities': ['pressure', 'velocity-magnitude', 'temperature', 'mach-number'],
# })
# from pprint import pprint
# pprint(export.get_state())

def export_ensight_step(solver, file_name_step, journal_path):
    journal_lines = [
        "/file/export/ensight-gold",
        file_name_step,                     
        "pressure",
        "mach-number", 
        "temperature",
        "q",
        "velocity",
        "q",                              
        "no",                            
    ]
    
    with open(journal_path, "w") as f:
        f.write("\n".join(journal_lines) + "\n")
    
    solver.tui.file.read_journal(to_fluent_path(journal_path))

#==============================================================
# region 8. FORCE REPORT: DRAG & LIFT
#==============================================================
print("\nConfiguring force reports...")

# DRAG
solver.settings.solution.report_definitions.drag.create(name="drag_report")
drag = solver.settings.solution.report_definitions.drag["drag_report"]
drag.set_state({
    'force_vector': [1, 0, 0],
    'zones': ['aile'],
    'report_output_type': 'Drag Force',  
    'average_over': 1,
})
# LIFT
solver.settings.solution.report_definitions.lift.create(name="lift_report")
lift = solver.settings.solution.report_definitions.lift["lift_report"]
lift.set_state({
    'force_vector': [0, 1, 0],
    'zones': ['aile'],
    'report_output_type': 'Lift Force',  
})

# REPORT FILE
print("\nConfiguring the report file for post-processing...")
solver.settings.solution.monitor.report_files.create(name="rapport_forces")
report = solver.settings.solution.monitor.report_files["rapport_forces"]
pprint(report.get_state())
report.report_defs = ["drag_report", "lift_report"]

report.file_name = to_fluent_path(os.path.join(export_forces_dir, "suivi_forces.out"))
report.frequency_of = "time-step"
report.frequency = 1 # Save at each time step

#==============================================================
# region 9. SAVING CONFIGURATION
#==============================================================

print("\nSaving configuration...")
solver.file.write(file_type="case", file_name=to_fluent_path(os.path.join(config_dir, "configuration_4deg.cas.h5")))

#==============================================================
# region 10. LAUNCHING THE CALCULATION
#==============================================================
print("\nLaunching the calculation...")
start_time = time.perf_counter()

base_path = to_fluent_path(export_pv_dir) + "/res_"

journal_path = os.path.join(base_dir, "export_tmp.jou")
transcript_path = to_fluent_path(os.path.join(base_dir, "transcript_export.txt"))

for loop in range(1,251) :
    print(f"\n--- loop {loop}/250 ---")

    file_name_step = base_path + f"{loop:03d}.vtk"

    solver.solution.run_calculation.dual_time_iterate(
        time_step_count=1,
        max_iter_per_step=10
    )

    solver.tui.file.start_transcript(transcript_path)
    export_ensight_step(solver, file_name_step, journal_path)
    solver.tui.file.stop_transcript()


    if os.path.exists(file_name_step):
        print(f"✅ Success: File {file_name_step} is properly on the disk.")
    else:
        print(f"❌ ALERT: Fluent did not create the file {file_name_step}.")
        break

end_time = time.perf_counter()
elapsed_time = end_time - start_time

hours = elapsed_time // 3600
minutes = (elapsed_time % 3600) // 60
seconds = elapsed_time % 60

print("\n\n\n")
print("="*40)
print(f"Calculation finished in {int(hours)}h {int(minutes)}m {seconds:.2f}s")
print("="*40)

print("\nShutting down Fluent...")
solver.exit()
print("\nFluent closed successfully.")