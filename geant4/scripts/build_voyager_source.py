"""
Rebuild the Geant4 proton source table from the raw Voyager 1 export.

The raw file contains one-day-average hydrogen flux measurements in:

    particles / m^2-s-sr-MeV/nuc

For protons, MeV/nuc == MeV.

The final source:
- keeps the standard LC3 low-energy channels rather than duplicate LD3 bins,
- uses the arithmetic mean daily differential intensity from 2013-2021,
- weights each measured energy bin by mean_intensity * bin_width,
- normalizes those weights into Monte Carlo source probabilities,
- does NOT interpolate across unmeasured energy gaps.
"""

from pathlib import Path
import re

import numpy as np
import pandas as pd


RAW_FILE = Path(
    "data/raw/voyager1_hydrogen_flux_2013_2021.txt"
)

OUTPUT_FILE = Path(
    "data/processed/geant4_voyager_proton_source_bins.csv"
)


def parse_raw_file(path: Path) -> pd.DataFrame:
    lines = path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines()

    channel_lines = [
        line for line in lines
        if line.startswith("#")
    ][1:19]

    pattern = re.compile(
        r"#\s+([\d.]+)\s*-\s*([\d.]+)\s+MeV/n "
        r"Hydrogen flux derived from\s+(\S+)"
    )

    channels = []

    for index, line in enumerate(channel_lines):
        match = pattern.match(line)

        if not match:
            raise ValueError(
                f"Could not parse channel metadata: {line}"
            )

        channels.append(
            {
                "channel_index": index,
                "energy_min_MeV": float(match.group(1)),
                "energy_max_MeV": float(match.group(2)),
                "detector": match.group(3),
            }
        )

    rows = []

    for line in lines:
        if not re.match(
            r"^\d{4}-\d{2}-\d{2}T",
            line,
        ):
            continue

        fields = line.split()

        if len(fields) != 91:
            raise ValueError(
                f"Expected 91 fields, found {len(fields)}"
            )

        date = pd.to_datetime(fields[0])
        values = list(map(float, fields[1:]))

        for channel in channels:
            i = channel["channel_index"]

            flux, error, count, livetime, gf = (
                values[i * 5 : (i + 1) * 5]
            )

            valid = (
                count > 0
                and flux > 0
                and error >= 0
            )

            rows.append(
                {
                    "date": date,
                    **channel,
                    "flux": flux if valid else np.nan,
                    "error": error if valid else np.nan,
                    "count": int(count),
                    "livetime_s": livetime,
                    "geometry_factor": (
                        gf if gf >= 0 else np.nan
                    ),
                }
            )

    return pd.DataFrame(rows)


def main():
    df = parse_raw_file(RAW_FILE)

    # Remove duplicate LD3 versions of the three lowest-energy
    # ranges and retain the standard LC3 channels.
    duplicate_low_energy_ld3 = (
        (df["detector"] == "LD3")
        & df["energy_min_MeV"].isin(
            [3.0, 4.6, 6.2]
        )
    )

    df = df[~duplicate_low_energy_ld3].copy()

    spectrum = (
        df.groupby(
            [
                "energy_min_MeV",
                "energy_max_MeV",
                "detector",
            ],
            as_index=False,
        )["flux"]
        .mean()
        .rename(
            columns={
                "flux": "mean_differential_intensity"
            }
        )
    )

    spectrum["energy_width_MeV"] = (
        spectrum["energy_max_MeV"]
        - spectrum["energy_min_MeV"]
    )

    spectrum["bin_integrated_intensity_per_sr"] = (
        spectrum["mean_differential_intensity"]
        * spectrum["energy_width_MeV"]
    )

    total = spectrum[
        "bin_integrated_intensity_per_sr"
    ].sum()

    spectrum["geant4_bin_probability"] = (
        spectrum["bin_integrated_intensity_per_sr"]
        / total
    )

    spectrum = spectrum.sort_values(
        "energy_min_MeV"
    ).reset_index(drop=True)

    spectrum["geant4_cumulative_probability"] = (
        spectrum["geant4_bin_probability"]
        .cumsum()
    )

    # Keep only the columns the source generator needs plus
    # useful provenance values.
    output = spectrum[
        [
            "energy_min_MeV",
            "energy_max_MeV",
            "mean_differential_intensity",
            "bin_integrated_intensity_per_sr",
            "geant4_bin_probability",
            "geant4_cumulative_probability",
        ]
    ]

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(output)
    print(
        "\nProbability sum:",
        output["geant4_bin_probability"].sum(),
    )


if __name__ == "__main__":
    main()
