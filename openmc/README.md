# OpenMC matched-energy neutron sensitivity model

This model is the **neutral-particle complement** to the Geant4 Voyager-proton transport model.

## Research question

> How does neutron-induced displacement damage in silicon change with particle energy and aluminum shielding thickness when the neutron energy grid is aligned to the representative energies of the Voyager 1 proton spectrum?

Voyager 1 did **not** measure this neutron field. The matched-energy design is a controlled sensitivity study that lets the project compare charged- and neutral-particle response across similar energy scales without treating protons and neutrons as physically interchangeable.

---

## Why the original model was rebuilt

The original research notebook used a 100 cm silicon sphere with a point neutron source at its center and manually assigned several source energies. It also mixed silicon and iron parameters in the downstream DPA calculation.

The rebuilt model changes four things:

1. **External irradiation instead of an internal point source**
2. **Aluminum shield + silicon target geometry aligned with the Geant4 model**
3. **Voyager-aligned representative energy points instead of arbitrary energies**
4. **Silicon-only NRT normalization with no iron constants**

---

## Geometry

```text
cosine-weighted external neutron field
                  ↓
        aluminum shielding
       0 / 1 / 2 / 5 / 10 / 20 mm
                  ↓
          silicon target
             0.5 mm
```

The material slabs are infinite in the lateral directions, eliminating arbitrary lateral-edge effects. The source itself is sampled over a 10 cm × 10 cm plane upstream of the shield.

---

## Angular source

The source uses the same plane-crossing approximation as the Geant4 model.

For an isotropic field incident on a plane:

`p(μ) = 2μ`, for `0 ≤ μ ≤ 1`

where:

`μ = cos(θ)`.

OpenMC implements that distribution with a power-law distribution in `μ` with exponent 1 and a uniform azimuth.

---

## Matched-energy source grid

The primary model runs **one neutron energy at a time** using representative energies associated with the measured Voyager proton channels.

The grid is stored in:

`data/openmc_matched_energy_grid.csv`

This is the preferred comparison because it produces a direct response curve:

```text
neutron energy
      ↓
shield thickness
      ↓
silicon damage energy
      ↓
NRT displacement response
```

An additional optional `voyager_weighted_neutral` mode uses the same relative energy weights as the Voyager proton spectrum. That case is explicitly hypothetical and is included only as a sensitivity test.

---

## Tallies

Two silicon-cell tallies are defined:

### Damage energy

OpenMC score:

`damage-energy`

Output:

`eV / source neutron`

This is the primary neutral-particle response metric.

### Flux

OpenMC score:

`flux`

This provides a transport / transmission metric inside the silicon region.

---

## NRT displacement estimate

The damage-energy tally is converted with the simplified NRT relation:

`N_d = 0.8 T_d / (2 E_d)`

where:

- `T_d` is OpenMC damage energy,
- `E_d = 20.5 eV` is the silicon threshold-displacement parameter retained from the original study.

The code reports:

- NRT displacements per source neutron
- normalized NRT-DPA per `1e15 neutrons/cm²`

For a planar source, the arbitrary source area cancels when converting to a fluence-normalized DPA:

`DPA = N_d × Φ / (n_atoms × t_Si)`

where `n_atoms × t_Si` is the silicon atom areal density.

This is an exploratory NRT metric, not a device-level failure prediction.

---

## Files

```text
openmc/
|
|-- model.py
|-- run_sweep.py
|-- analyze_results.py
|-- check_cross_sections.py
|
|-- data/
|   |-- openmc_matched_energy_grid.csv
|   `-- voyager_matched_source_bins.csv
|
|-- scripts/
|
`-- results/
```

---

## Export model inputs

If OpenMC is installed:

```bash
cd openmc
python run_sweep.py --export-only
```

This creates the full matched-energy × shield-thickness model matrix without executing transport.

---

## Execute selected cases

Start with a few lower-energy cases that are known to be supported by the installed neutron library:

```bash
python run_sweep.py \
  --run \
  --energies 3.8 10.2 23.9 \
  --shields 0 5 20
```

Then extract the statepoint results:

```bash
python analyze_results.py
```

---

## Nuclear-data limitation

The Voyager-matched grid reaches above 300 MeV.

OpenMC continuous-energy neutron transport relies on an external evaluated nuclear-data library. The usable incident-energy range is therefore determined by the installed Al and Si neutron data, not by the Voyager data.

The model intentionally does **not** extrapolate missing neutron cross sections. Before final production runs:

```bash
python check_cross_sections.py
```

and restrict the sensitivity grid to supported energies.

---

## Current status

### Implemented

- aluminum / silicon planar geometry
- matched-energy neutron source
- cosine-weighted planar incidence
- shield-thickness sweep
- damage-energy tally
- silicon flux tally
- corrected silicon NRT normalization
- optional Voyager-weighted neutral sensitivity source
- result-extraction pipeline

### Pending execution

- nuclear-data range check
- OpenMC transport runs
- convergence testing
- final damage-energy and NRT response figures

No unexecuted transport value is presented as a result.
