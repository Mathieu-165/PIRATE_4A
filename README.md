# ❄️ Impact of Frost Accretion on the Aerodynamic Performance of a NACA 2414 Airfoil

This student research project aims to estimate the impact of frost accretion on an airfoil under fixed flight conditions. This study is conducted exclusively through numerical simulation (CFD).

The initial phase focuses on the flow around the "clean" (non-iced) airfoil. We establish a drag polar to serve as a baseline for comparing performance degradation once icing conditions are applied.

---

## Table of Contents

1. [Flow Conditions](#flow-conditions)
2. [Software Suite](#software-suite)
3. [Solver Configuration](#solver-configuration)
4. [Note on the Buffeting Phenomenon](#note-on-the-buffeting-phenomenon)
5. [Future Objectives](#future-objectives)
6. [Authors](#authors)

---

## Flow Conditions

The simulation replicates conditions typically encountered at **10,000 ft** at **Mach 0.5**:

* **Static Temperature ($T_s$):** 268.15 K
* **Static Pressure ($P_s$):** 69,682 Pa
* **Ratio of Specific Heats ($\gamma$):** 1.4
* **Chord Length ($c$):** 1.0 m

**Fluid Modeling:**
Air is modeled as an **Ideal Gas**. Density ($\rho$) is determined via the Ideal Gas Law, and **viscosity** follows **Sutherland's Law**.

**Dimensionless Numbers:**
Under these conditions, the chord-based Reynolds number is:  
**$Re_c = 8.7 \times 10^6$**

*Note: The current study is restricted to 2D space.*

---

## Software Suite

To conduct this CFD analysis, we utilize **ANSYS Fluent 2026R1**. This version allows for precise geometry drafting and meshing of the 2D domain. 

We integrate **PyAnsys** to automate the solver configuration and flow condition inputs. This programmatic approach streamlines our workflow and resolves version compatibility issues between personal setups (2026) and institutional workstations (2024).

---

## Solver Configuration

### 1. Polar Generation (Steady-State)
* **Type:** Pressure-based, stationary formulation.
* **Turbulence Model:** $k-\omega$ SST (maintaining $y^+ \approx 1$).
* **Pressure-Velocity Coupling:** "Coupled" scheme.
* **Gradients:** Least-Square Cell-Based.
* **Angular Range:** $\alpha \in [-5^\circ, +20^\circ]$.
* **Convergence:** 750 iterations per AoA (to ensure stabilized $C_L$ and $C_D$ values for $\alpha > 11^\circ$).

### 2. Clean Flow Analysis (Unsteady-State)
* **Type:** Pressure-based, Unsteady 2nd-order formulation.
* **Turbulence Model:** $k-\omega$ SST.
* **AoA ($\alpha$):** 4°.
* **Time Parameters:** 1,000 time steps of 0.005 s (Total flow time: 5 s), with 100 iterations per time step.

---

## Note on the Buffeting Phenomenon

For angles of attack starting at **11°**, we observe a **buffeting phenomenon**. A supersonic pocket forms on the upper surface (extrados), leading to a shock-boundary layer interaction. This causes the shock position to oscillate along the chord. 

By extracting the time-varying shock position ($x$) and performing a Fast Fourier Transform (FFT), we identified the following characteristics:
* **Frequency ($f$):** 7.0 Hz
* **Strouhal Number ($St$):** 0.04

---

## Future Objectives

The next phase of research focuses on modeling **frost accretion**. Our primary methodology involves:
* **Eulerian/Lagrangian Droplet Modeling:** Leveraging the latest Fluent solver capabilities to manage droplet generation and trajectory tracking.
* **Ice Growth Simulation:** Implementing ice formation physics, potentially through custom User-Defined Functions (UDFs) or the PyAnsys framework.

Detailed documentation review, specifically regarding the PyAnsys icing modules, is currently underway.

---

## ✍️ Authors

* **Mathieu Granger** – 3rd-year Aerospace Engineering Student, ESTACA – [LinkedIn Profile](https://www.linkedin.com/in/mathieu-grng/)
* **Valentin Gitta** – 3rd-year Aerospace Engineering Student, ESTACA – [LinkedIn Profile](https://www.linkedin.com/in/valentin-gitta/)