# Data

## Raw

`raw/voyager1_hydrogen_flux_2013_2021.txt`

Voyager 1 one-day-average hydrogen flux export used to build the project spectrum.

Flux units:

`particles / m²-s-sr-MeV/nuc`

## Processed

`processed/voyager1_proton_spectrum_final.csv`

Final 15-bin empirical proton spectrum and descriptive statistics.

`processed/geant4_voyager_proton_source_bins.csv`

Compact source table used by the Geant4 primary generator.

The raw file is preserved unchanged. Processing decisions are implemented in `analysis/build_voyager_spectrum.py`.
