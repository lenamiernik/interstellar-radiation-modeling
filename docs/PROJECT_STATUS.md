# Project status

## Completed

- Parsed Voyager 1 one-day-average hydrogen flux data from 2013-2021.
- Constructed a 15-bin empirical proton spectrum.
- Built normalized Geant4 energy-bin sampling probabilities.
- Validated the source sampler with 500,000 independent draws.
- Implemented Geant4 geometry for aluminum shielding and a silicon target.
- Implemented isotropic planar proton incidence.
- Implemented event-level silicon energy-deposition scoring.
- Implemented scripts for shielding sweeps and mission-dose post-processing.
- Rebuilt OpenMC matched-energy neutron model with aligned aluminum/silicon geometry.
- Corrected OpenMC silicon damage-energy and NRT normalization pipeline.

## Not yet executed

- Geant4 compilation in a Geant4-enabled environment.
- Proton transport validation.
- Shield-thickness production runs.
- Monte Carlo convergence study.
- Production-cut sensitivity study.
- Final mission-dose calculations.
- OpenMC matched-energy transport runs.

## Interpretation rule

The repository currently demonstrates:

- data acquisition and processing,
- empirical spectrum construction,
- Monte Carlo source design,
- radiation-transport model implementation,
- reproducible analysis architecture.

It does **not** yet claim validated Geant4 shielding results.
