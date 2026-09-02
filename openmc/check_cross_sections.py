"""
Inspect the configured OpenMC neutron library before attempting high-energy runs.

Why this exists:
The Voyager-matched grid extends above 300 MeV, but continuous-energy neutron
libraries do not necessarily contain evaluated data over that full range.
The supported model grid must be restricted to the energies available in the
installed nuclear-data library.

This helper reports the configured cross_sections.xml path and provides the
matched energies that should be checked before production runs.
"""

from pathlib import Path
import os

import pandas as pd


ROOT = Path(__file__).resolve().parent
ENERGY_GRID = ROOT / "data/openmc_matched_energy_grid.csv"


def main():
    grid = pd.read_csv(ENERGY_GRID)

    cross_sections = os.environ.get(
        "OPENMC_CROSS_SECTIONS"
    )

    print("Configured OPENMC_CROSS_SECTIONS:")
    print(cross_sections or "  [not set]")

    print("\nRequested matched neutron energies [MeV]:")
    print(
        ", ".join(
            f"{x:g}"
            for x in grid["matched_neutron_energy_MeV"]
        )
    )

    print(
        "\nBefore production runs, verify that the installed Al and Si neutron "
        "data support every requested incident energy. Unsupported high-energy "
        "cases should be excluded rather than extrapolated."
    )


if __name__ == "__main__":
    main()
