# Modules Python 
import numpy as np
import time  

# Modules Fluent
import ansys.fluent.core as pyfluent

# Emplacement de Fluent 2026 R1 (v261)
import os

chemin_exact_fluent = r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent"
os.environ["PYFLUENT_FLUENT_ROOT"] = chemin_exact_fluent

#==============================================================
# region 1. CONDITIONS DE L'ÉCOULEMENT
#==============================================================

M = 0.5 # Mach number
# Altitude = 10000 ft
T = 268.15 # K
P = 69682 #Pa
R = 287.04 # J/kg/K
GAMMA = 1.4 
RHO = P / (R * T) # kg/m3
MU = 1.46e-6 * T**1.5 / (T + 110.4) # Pa.s
L = 1 # m Corde du profil

a = (GAMMA * R * T) ** 0.5 # m/s
u = M * a # m/s
REYNOLDS = RHO * u * L / MU

print('\n----- Conditions d\'écoulement -----')
print(f'Mach : {M}')
print(f'Température statique champ lointain : {T} K')
print(f'Pression statique champ lointain : {P} Pa')
print(f'Vitesse de l\'écoulement : {u:.2f} m/s')
print(f'Reynolds : {REYNOLDS:.2e}')
print('Profil NACA 2414')
print('Angle d\'attaque : 4°')

#==============================================================
# region 2. DÉMARRAGE DE FLUENT ET CHARGEMENT DU MAILLAGE
#==============================================================

print("\nDémarrage de Fluent en mode solveur avec 4 coeurs, précision double, 2D...")
solver = pyfluent.launch_fluent(precision="double", #double précision
                                processor_count=4, #nombre de coeurs
                                mode="solver", #arrière plan
                                start_timeout=120, #120s pour démarrer Fluent
                                dimension=2) #2D

print("\nChargement du maillage...")
solver.settings.file.read_mesh(file_name="maillages/mesh_4deg.msh")
solver.tui.define.mesh_interfaces.one_to_one_pairing("yes")
print("\nMaillage chargé avec succès.")

#==============================================================
# region 3. CONFIGURATION GÉNÉRALE ET MODÈLES PHYSIQUES
#==============================================================

print("\nConfiguration générale...")

# Modèle physique : écoulement compressible (API moderne)
solver.settings.setup.general.solver.type = "pressure-based"
solver.settings.setup.general.solver.time = "transient"
solver.settings.setup.models.energy.enabled = True # Activer l'énergie

# Modèle de turbulence : k-w-SST (API moderne)
solver.settings.setup.models.viscous.model = "k-omega" 
solver.settings.setup.models.viscous.k_omega_model = "sst"

# Propriétés du fluide :air
solver.settings.setup.materials.fluid['air'].density.option = "ideal-gas" #Gaz parfait
solver.settings.setup.materials.fluid['air'].viscosity.option = "sutherland" #Viscosité de Sutherland

solver.settings.setup.cell_zone_conditions.fluid['fluid-pi_ce-corps_surfacique'].material = "air"

#==============================================================
# region 3. CONDITIONS AU LIMITES
#==============================================================

print("\nConfiguration des conditions aux limites...")

solver.settings.setup.general.operating_conditions.operating_pressure = P

# --- INLET ---
inlet = solver.setup.boundary_conditions.velocity_inlet['inlet']
inlet.momentum.vmag = u                                  # Onglet Momentum
inlet.turbulence.turb_intensity = 0.001                  # Onglet Turbulence
inlet.turbulence.turb_viscosity_ratio = 10              # Onglet Turbulence
inlet.thermal.temperature = T                                     # Onglet Thermal

# --- OUTLET ---
outlet = solver.setup.boundary_conditions.pressure_outlet['outlet']
outlet.momentum.gauge_pressure = 0.0                     # Onglet Momentum
outlet.turbulence.turb_intensity = 0.001                  # Onglet Turbulence
outlet.turbulence.turb_viscosity_ratio = 10               # Onglet Turbulence
outlet.thermal.backflow_total_temperature = T                                    # Onglet Thermal

# --- MOVING WALLS ---
murs = solver.setup.boundary_conditions.wall['moving_walls']
murs.momentum.motion_bc = "Moving Wall"                  # Onglet Momentum
murs.momentum.vmag = u                                   # Onglet Momentum
murs.momentum.shear_bc = "No Slip"                       # Onglet Momentum
murs.momentum.direction = [1.0, 0.0]                                # Onglet Momentum

#==============================================================
# region 4. CONTRÔLE DE LA SOLUTION ET STRATÉGIE DE SOLUTION
#==============================================================

print("\nConfiguration des schémas de discrétisation...")
# Schémas de discrétisation
solver.solution.methods.p_v_coupling.flow_scheme = "Coupled" # Schéma couplé
solver.solution.methods.gradient_scheme = "least-square-cell-based"
solver.settings.solution.methods.transient_formulation = "unsteady-2nd-order"

# Critères de convergence
print("\nConfiguration des critères de convergence...")
solver.solution.monitor.residual.equations['continuity'].absolute_criteria = 1e-4
solver.solution.monitor.residual.equations['x-velocity'].absolute_criteria = 1e-4
solver.solution.monitor.residual.equations['y-velocity'].absolute_criteria = 1e-4
solver.solution.monitor.residual.equations['energy'].absolute_criteria = 1e-6
solver.solution.monitor.residual.equations['k'].absolute_criteria = 1e-6
solver.solution.monitor.residual.equations['omega'].absolute_criteria = 1e-6

#==============================================================
# region 5. PARAMÉTRAGE DE LA SIMULATION 
#==============================================================

print("\nInitialisation de la simulation : standard à partir de l'inlet...")

# Initialisation standard
solver.solution.initialization.initialization_type = "standard"
solver.tui.solve.initialize.compute_defaults.velocity_inlet("inlet")
solver.solution.initialization.standard_initialize() # Initialisation standard

# Paramètres de la simulation
solver.settings.solution.run_calculation.transient_controls.time_step_size = 0.005 # s

#==============================================================
# region 6. AUTOSAVE DE SECOURS
#==============================================================
print("\nConfiguration de l'autosave de sécurité...")

autosave = solver.settings.file.auto_save

autosave.save_data_file_every = {
    "frequency_type": "time-step", 
    "save_frequency": 100
}
autosave.retain_most_recent_files = True
autosave.max_files = 3

autosave.root_name = "autosave_securite/4deg/autosave_4deg"

#==============================================================
# region 7. EXPORT DES RÉSULTATS POUR PARAVIEW
#==============================================================
print("\nConfiguration de l'export pour ParaView...")

solver.settings.file.export.create(obj_name="export_paraview")
export = solver.settings.file.export["export_paraview"]

export.format = "ensight-gold"
export.frequency_of = "time-step"
export.frequency = 2
export.variables = ["pressure", "velocity", "mach-number", "temperature"]

# C'est ICI qu'on choisit le dossier pour ParaView
export.file_name = "export_paraview/4deg/export_4deg"

#==============================================================
# region 8. RAPPORT DE FORCES : DRAG & LIFT
#==============================================================
print("\nConfiguration des force report...")

# DRAG
solver.settings.solution.report_definitions.drag.create(obj_name="drag_report")
drag = solver.settings.solution.report_definitions.drag["drag_report"]
drag.force_vector = [1, 0, 0] # Direction X
drag.thread_names = ['aile']

# LIFT
solver.settings.solution.report_definitions.lift.create(obj_name="lift_report")
lift = solver.settings.solution.report_definitions.lift["lift_report"]
lift.force_vector = [0, 1, 0] # Direction Y
lift.thread_names = ['aile']

# FICHIER RAPPORT
print("\nConfiguration du fichier de rapport pour post-traitement...")
solver.settings.solution.report_files.create(obj_name="rapport_forces")
report = solver.settings.solution.report_files["rapport_forces"]
report.report_definitions = ["drag_report", "lift_report"]

report.file_name = "export_forces/suivi_forces.out"
report.frequency_of = "time-step"
report.frequency = 1 # On enregistre à chaque pas de temps

#==============================================================
# region 9. SAUVEGARDE DE LA CONFIGURATION
#==============================================================

print("\nSauvegarde de la configuration...")
solver.file.write(file_type="case", file_name="configurations/configuration_4deg.cas.h5")

#==============================================================
# region 10. LANCEMENT DU CALCUL
#==============================================================
print("\nLancement du calcul...")
start_time = time.perf_counter()

solver.solution.run_calculation.calculate(
    time_step_count=400,
    max_iter_per_step=100
)

end_time = time.perf_counter()
elapsed_time = end_time - start_time

heures = elapsed_time // 3600
minutes = (elapsed_time % 3600) // 60
secondes = elapsed_time % 60

print("\n \n \n","="*40)
print(f"Calcul terminé en {int(heures)}h {int(minutes)}m {secondes:.2f}s")
print("="*40)

print("\nExtinction de FLuent...")
solver.exit()
print("\nFluent fermé avec succès.")