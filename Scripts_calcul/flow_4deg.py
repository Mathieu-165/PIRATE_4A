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
print("\nMaillage chargé avec succès.")

#==============================================================
# region 3. CONFIGURATION GÉNÉRALE ET MODÈLES PHYSIQUES
#==============================================================

print("\nConfiguration générale...")

# Modèle physique : écoulement compressible
solver.tui.define.general.set_solver("pressure-based")
solver.tui.define.general.set_time("transient")
solver.setup.models.energy.enabled = True # Activer l'énergie pour les écoulements compressibles

# Modèle de turbulence : k-w-SST
solver.tui.setup.models.turbulence.ke_sst.enabled = True
solver.setup.models.viscous.k_omega_options.production_limiter = True #Limiter de production pour éviter les problèmes de convergence à proximité des parois
solver.setup.models.viscous.k_omega_options.compressibility_effects = True #Pour être plus rigoureux dans le traitement de la turbulence dans les écoulements compressibles
solver.setup.models.viscous.k_omega_options.curvature_correction = False
solver.setup.models.viscous.k_omega_options.kw_low_re_correction = False

# Propriétés du fluide :air
solver.setup.materials.fluid['air'].density.option = "ideal-gas" #Gaz parfait
solver.setup.materials.fluid['air'].viscosity.option = "sutherland" #Viscosité de Sutherland

solver.setup.cell_zone_conditions.fluid['fluid-pi_ce-corps_surfacique'].material = "air"

#==============================================================
# region 3. CONDITIONS AU LIMITES
#==============================================================

print("\nConfiguration des conditions aux limites...")

solver.settings.setup.general.operating_conditions.operating_pressure = P

# Inlet : vitesse imposée
solver.setup.boundary_conditions.velocity_inlet['inlet'].vmag = u # m/s
solver.setup.boundary_conditions.velocity_inlet['inlet'].ke_spec = "Intensity and Viscosity Ratio"
solver.setup.boundary_conditions.velocity_inlet['inlet'].turb_intensity = 0.001 # 0.1% d'intensité turbulente
solver.setup.boundary_conditions.velocity_inlet['inlet'].turb_viscosity_ratio = 10 # Ratio de viscosité turbulente
solver.setup.boundary_conditions.velocity_inlet['inlet'].t0 = T # Kelvin

# Outlet : pression imposée
solver.setup.boundary_conditions.pressure_outlet['Outlet'].gauge_pressure = 0.0 # Pa
solver.setup.boundary_conditions.pressure_outlet['Outlet'].t0 = T # Kelvin

# Movings Walls : parois mobiles pour simuler le mouvement de l'air autour du profil
solver.setup.boundary_conditions.wall['moving_walls'].motion_bc = "Moving Wall"
solver.setup.boundary_conditions.wall['moving_walls'].vmag = u # m/s
solver.setup.boundary_conditions.wall['moving_walls'].shear_bc = "No Slip"
solver.setup.boundary_conditions.wall['moving_walls'].x_dir = 1 # Mouvement dans la direction X
solver.setup.boundary_conditions.wall['moving_walls'].y_dir = 0 # Pas de mouvement dans la direction Y

#==============================================================
# region 4. CONTRÔLE DE LA SOLUTION ET STRATÉGIE DE SOLUTION
#==============================================================

print("\nConfiguration des schémas de discrétisation...")
# Schémas de discrétisation
solver.solution.methods.p_v_coupling.flow_scheme = "Coupled" # Schéma couplé
solver.solution.methods.gradient_scheme = "least-square-cell-based"
solver.solution.methods.pressure_scheme = "second-order"
solver.solution.methods.momentum_scheme = "second-order"
solver.solution.methods.energy_scheme = "second-order"
solver.solution.methods.turbulence_scheme = "second-order"
solver.solution.methods.density_scheme = "second-order"
solver.solution.methods.time_scheme = "second-order implicit"

# Critères de convergence
print("\nConfiguration des critères de convergence...")
solver.solution.monitor.residual.equations['continuity'].absolute_tolerance = 1e-4
solver.solution.monitor.residual.equations['x-velocity'].absolute_tolerance = 1e-4
solver.solution.monitor.residual.equations['y-velocity'].absolute_tolerance = 1e-4
solver.solution.monitor.residual.equations['pressure'].absolute_tolerance = 1e-4
solver.solution.monitor.residual.equations['energy'].absolute_tolerance = 1e-6
solver.solution.monitor.residual.equations['k'].absolute_tolerance = 1e-6
solver.solution.monitor.residual.equations['omega'].absolute_tolerance = 1e-6

#==============================================================
# region 5. PARAMÉTRAGE DE LA SIMULATION 
#==============================================================

print("\nInitialisation de la simulation : standard à partir de l'inlet...")

# Initialisation standard
solver.solution.initialization.initialization_type = "standard"
solver.tui.solve.initialize.compute_defaults("inlet")
solver.solution.initialization.standard_initialize() # Initialisation standard

# Paramètres de la simulation
solver.solution.run_time_options.time_step = 0.005 # s

#==============================================================
# region 6. AUTOSAVE DE SECOURS
#==============================================================
print("\nConfiguration de l'autosave de sécurité...")
solver.settings.file.autosave.interval = 100
solver.settings.file.autosave.file_name_type = "time-step"
solver.settings.file.autosave.retain_most_recent_files = True
solver.settings.file.autosave.number_of_files_to_retain = 3

solver.settings.file.autosave.root_name = "autosave_securite/4deg/autosave_4deg"

#==============================================================
# region 7. EXPORT DES RÉSULTATS POUR PARAVIEW
#==============================================================
print("\nConfiguration de l'export pour ParaView...")
if "export_paraview" in solver.settings.calculation_activities.data_export:
    solver.settings.calculation_activities.data_export.delete(obj_name="export_paraview")

solver.settings.calculation_activities.data_export.create(obj_name="export_paraview")
export = solver.settings.calculation_activities.data_export["export_paraview"]

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
    time_step_count=500,
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