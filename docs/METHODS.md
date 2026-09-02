# Methods

## Voyager spectrum construction

The raw Voyager 1 file contains one-day-average hydrogen differential intensity measurements.

For each unique measured energy bin `i`:

`J_i = mean daily differential intensity`

The energy-integrated directional intensity represented by the bin is approximated as:

`I_i = J_i * ΔE_i`

where:

`ΔE_i = E_max,i - E_min,i`

The Geant4 source probability is:

`P_i = I_i / ΣI_i`

Energy is sampled uniformly inside the selected measured bin for the first implementation.

## Isotropic planar incidence

Voyager intensity is treated as isotropic.

For an isotropic intensity incident on a plane from one hemisphere, the directional distribution of particles crossing the plane is:

`p(μ) = 2μ`

where:

`μ = cos(θ)`.

Sampling is performed with:

`μ = sqrt(U)`

for `U ~ Uniform(0,1)`.

## Geant4 scoring

The silicon target is a 0.5 mm slab placed behind an aluminum shielding layer.

The primary score is:

`total energy deposited in silicon per incident proton`

The score includes energy deposited by both the primary proton and generated secondary particles.

The initial shielding thickness sweep is:

`0, 1, 2, 5, 10, 20 mm Al`

## Mission scaling

If Geant4 returns mean deposited energy per incident proton, `<E_dep>`, and the mission fluence is `Φ`, then energy deposited per unit area is:

`E/A = <E_dep> * Φ`

For silicon areal mass:

`m/A = ρ_Si * t_Si`

absorbed dose is:

`D = (E/A) / (m/A)`.

Mission durations are simplified constant-speed cases of approximately 50, 500, and 7000 years.

## OpenMC comparison

The OpenMC model will use neutron energies aligned to representative Voyager proton energies. It is a neutral-particle sensitivity study, not a proton proxy.

The intended response variable is neutron damage energy in silicon, followed by an exploratory NRT displacement estimate.
