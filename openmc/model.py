"""
Matched-energy OpenMC neutron sensitivity model.

Purpose
-------
This model complements, rather than replaces, the Geant4 proton model.

Voyager 1 measured energetic hydrogen nuclei/protons. Here, neutrons are
simulated at representative energies aligned to the Voyager proton channels
to study how a neutral particle field changes damage-energy deposition in
silicon behind aluminum shielding.

Primary outputs
---------------
- silicon damage-energy [eV / source neutron]
- silicon flux [particle-cm / source neutron]
- NRT displacements / source neutron
- normalized NRT-DPA per 1e15 incident neutrons / cm^2

Geometry
--------
cosine-weighted planar neutron source
        ↓
aluminum shield: 0, 1, 2, 5, 10, 20 mm
        ↓
silicon electronics proxy: 0.5 mm
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from pathlib import Path
from typing import Literal

import numpy as np
import openmc
import pandas as pd


SILICON_DENSITY_G_CM3 = 2.33
SILICON_MOLAR_MASS_G_MOL = 28.0855
AVOGADRO = 6.02214076e23

# Constant threshold-displacement energy carried forward from the original
# research notebook. This is deliberately treated as a simplified model
# parameter rather than a universal material constant.
SI_DISPLACEMENT_THRESHOLD_EV = 20.5

SILICON_THICKNESS_CM = 0.05  # 0.5 mm
SOURCE_HALF_WIDTH_CM = 5.0
SOURCE_Z_CM = -0.5

DEFAULT_BATCHES = 20
DEFAULT_PARTICLES_PER_BATCH = 50_000

SourceMode = Literal["mono", "voyager_weighted_neutral"]


@dataclass(frozen=True)
class ModelConfig:
    shield_mm: float
    source_mode: SourceMode = "mono"
    energy_mev: float | None = None
    batches: int = DEFAULT_BATCHES
    particles_per_batch: int = DEFAULT_PARTICLES_PER_BATCH


def build_materials() -> tuple[openmc.Material, openmc.Material, openmc.Materials]:
    """Create aluminum shielding and natural-silicon target materials."""
    aluminum = openmc.Material(name="Aluminum shield")
    aluminum.set_density("g/cm3", 2.70)
    aluminum.add_element("Al", 1.0)

    silicon = openmc.Material(name="Silicon electronics proxy")
    silicon.set_density("g/cm3", SILICON_DENSITY_G_CM3)
    silicon.add_element("Si", 1.0)

    return aluminum, silicon, openmc.Materials([aluminum, silicon])


def build_geometry(
    aluminum: openmc.Material,
    silicon: openmc.Material,
    shield_mm: float,
) -> tuple[openmc.Geometry, openmc.Cell]:
    """
    Build an effectively infinite planar slab geometry.

    OpenMC geometry dimensions are in centimeters.
    The source is localized to a 10 cm × 10 cm patch, while the slabs are
    infinite in x and y. This removes arbitrary lateral edge effects.
    """
    if shield_mm < 0:
        raise ValueError("shield_mm must be non-negative")

    shield_cm = shield_mm / 10.0

    z_world_min = openmc.ZPlane(z0=-1.0, boundary_type="vacuum")
    z_shield_front = openmc.ZPlane(z0=0.0)
    z_si_front = openmc.ZPlane(z0=shield_cm)
    z_si_back = openmc.ZPlane(z0=shield_cm + SILICON_THICKNESS_CM)
    z_world_max = openmc.ZPlane(
        z0=shield_cm + SILICON_THICKNESS_CM + 1.0,
        boundary_type="vacuum",
    )

    cells: list[openmc.Cell] = []

    upstream = openmc.Cell(
        name="Upstream vacuum",
        region=+z_world_min & -z_shield_front,
    )
    cells.append(upstream)

    if shield_cm > 0:
        shield = openmc.Cell(
            name="Aluminum shield",
            fill=aluminum,
            region=+z_shield_front & -z_si_front,
        )
        cells.append(shield)

    silicon_cell = openmc.Cell(
        name="Silicon target",
        fill=silicon,
        region=+z_si_front & -z_si_back,
    )
    cells.append(silicon_cell)

    downstream = openmc.Cell(
        name="Downstream vacuum",
        region=+z_si_back & -z_world_max,
    )
    cells.append(downstream)

    return openmc.Geometry(cells), silicon_cell


def cosine_weighted_planar_angle() -> openmc.stats.PolarAzimuthal:
    """
    Angular distribution for particles crossing a plane from an isotropic field.

    p(mu) = 2*mu, 0 <= mu <= 1, where mu = cos(theta).
    A PowerLaw exponent n=1 produces a normalized density proportional to mu.
    """
    mu = openmc.stats.PowerLaw(0.0, 1.0, 1.0)
    phi = openmc.stats.Uniform(0.0, 2.0 * pi)

    return openmc.stats.PolarAzimuthal(
        mu=mu,
        phi=phi,
        reference_uvw=(0.0, 0.0, 1.0),
    )


def planar_source_space() -> openmc.stats.CartesianIndependent:
    """Uniform 10 cm × 10 cm source plane located upstream of the shield."""
    return openmc.stats.CartesianIndependent(
        x=openmc.stats.Uniform(-SOURCE_HALF_WIDTH_CM, SOURCE_HALF_WIDTH_CM),
        y=openmc.stats.Uniform(-SOURCE_HALF_WIDTH_CM, SOURCE_HALF_WIDTH_CM),
        z=openmc.stats.Discrete([SOURCE_Z_CM], [1.0]),
    )


def load_voyager_matched_source(
    csv_path: str | Path,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Load representative energies and normalized Voyager-derived weights.

    This does NOT imply that Voyager observed neutrons. It creates an optional
    hypothetical neutral source whose energy weights mirror the measured
    proton spectrum for sensitivity analysis only.
    """
    df = pd.read_csv(csv_path)

    energies_mev = df["plot_energy_MeV"].to_numpy(dtype=float)
    probabilities = df["geant4_bin_probability"].to_numpy(dtype=float)

    probabilities = probabilities / probabilities.sum()

    return energies_mev, probabilities


def build_source(
    config: ModelConfig,
    voyager_source_csv: str | Path | None = None,
) -> openmc.IndependentSource:
    source = openmc.IndependentSource()
    source.particle = "neutron"
    source.space = planar_source_space()
    source.angle = cosine_weighted_planar_angle()

    if config.source_mode == "mono":
        if config.energy_mev is None:
            raise ValueError("energy_mev is required for mono source mode")

        source.energy = openmc.stats.Discrete(
            [config.energy_mev * 1.0e6],
            [1.0],
        )

    elif config.source_mode == "voyager_weighted_neutral":
        if voyager_source_csv is None:
            raise ValueError(
                "voyager_source_csv is required for voyager_weighted_neutral mode"
            )

        energies_mev, probabilities = load_voyager_matched_source(
            voyager_source_csv
        )

        source.energy = openmc.stats.Discrete(
            energies_mev * 1.0e6,
            probabilities,
        )

    else:
        raise ValueError(f"Unsupported source mode: {config.source_mode}")

    return source


def build_tallies(silicon_cell: openmc.Cell) -> openmc.Tallies:
    """Score both neutral-particle transmission and silicon damage response."""
    cell_filter = openmc.CellFilter(silicon_cell)

    damage = openmc.Tally(name="silicon_damage_energy")
    damage.filters = [cell_filter]
    damage.scores = ["damage-energy"]

    flux = openmc.Tally(name="silicon_flux")
    flux.filters = [cell_filter]
    flux.scores = ["flux"]

    return openmc.Tallies([damage, flux])


def build_model(
    config: ModelConfig,
    voyager_source_csv: str | Path | None = None,
) -> openmc.Model:
    aluminum, silicon, materials = build_materials()

    geometry, silicon_cell = build_geometry(
        aluminum=aluminum,
        silicon=silicon,
        shield_mm=config.shield_mm,
    )

    settings = openmc.Settings()
    settings.run_mode = "fixed source"
    settings.batches = config.batches
    settings.inactive = 0
    settings.particles = config.particles_per_batch
    settings.source = build_source(
        config,
        voyager_source_csv=voyager_source_csv,
    )

    tallies = build_tallies(silicon_cell)

    return openmc.Model(
        geometry=geometry,
        materials=materials,
        settings=settings,
        tallies=tallies,
    )


def nrt_displacements_per_source(
    damage_energy_ev_per_source: float,
    displacement_threshold_ev: float = SI_DISPLACEMENT_THRESHOLD_EV,
) -> float:
    """
    Simplified NRT displacement estimate.

    N_d = 0.8 * T_d / (2 * E_d)
    """
    return (
        0.8
        * damage_energy_ev_per_source
        / (2.0 * displacement_threshold_ev)
    )


def silicon_atom_number_density_cm3() -> float:
    return (
        SILICON_DENSITY_G_CM3
        / SILICON_MOLAR_MASS_G_MOL
        * AVOGADRO
    )


def dpa_per_fluence(
    displacements_per_source: float,
    fluence_n_cm2: float,
    silicon_thickness_cm: float = SILICON_THICKNESS_CM,
) -> float:
    """
    Convert displacements/source to a planar fluence-normalized DPA estimate.

    For a uniform plane source, one source particle spread over source area A
    represents fluence 1/A. Dividing by the silicon atom areal density causes
    the arbitrary source area to cancel:

        DPA = N_d/source * Phi / (n_atoms * t)
    """
    atom_areal_density = (
        silicon_atom_number_density_cm3()
        * silicon_thickness_cm
    )

    return (
        displacements_per_source
        * fluence_n_cm2
        / atom_areal_density
    )
