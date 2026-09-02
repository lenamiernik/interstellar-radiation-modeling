"""
Build the finalized Voyager 1 proton spectrum used by the project.

Input:
    data/raw/voyager1_hydrogen_flux_2013_2021.txt

Outputs:
    data/processed/voyager1_proton_spectrum_final.csv
    data/processed/geant4_voyager_proton_source_bins.csv

Method:
- parse 1-day-average Voyager 1 hydrogen measurements,
- treat missing/sentinel measurements as NaN,
- retain LC3 rather than duplicate LD3 low-energy channels,
- calculate mean differential intensity for each unique measured bin,
- weight source bins by mean intensity × bin width,
- normalize those weights into Monte Carlo source probabilities.

No interpolation is performed across unmeasured energy gaps.
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd

RAW_FILE = Path("data/raw/voyager1_hydrogen_flux_2013_2021.txt")
OUT_SPECTRUM = Path("data/processed/voyager1_proton_spectrum_final.csv")
OUT_SOURCE = Path("data/processed/geant4_voyager_proton_source_bins.csv")

PLOT_ENERGY_MEV = {
    (3.000, 4.600): 3.8,
    (4.600, 6.200): 5.4,
    (6.200, 7.700): 6.9,
    (7.700, 12.800): 10.2,
    (12.800, 17.900): 15.4,
    (17.900, 30.000): 23.9,
    (30.000, 48.000): 39.0,
    (48.000, 56.000): 52.0,
    (74.471, 83.661): 79.1,
    (132.834, 154.911): 143.9,
    (154.911, 174.866): 164.9,
    (174.866, 187.713): 181.3,
    (187.713, 220.475): 204.1,
    (220.475, 270.050): 245.3,
    (270.050, 346.034): 308.0,
}

def parse_raw(path: Path) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    metadata = [line for line in lines if line.startswith("#")][1:19]
    pattern = re.compile(
        r"#\s+([\d.]+)\s*-\s*([\d.]+)\s+MeV/n "
        r"Hydrogen flux derived from\s+(\S+)"
    )

    channels = []
    for i, line in enumerate(metadata):
        m = pattern.match(line)
        if not m:
            raise ValueError(f"Could not parse channel metadata: {line}")
        channels.append({
            "index": i,
            "energy_min_MeV": float(m.group(1)),
            "energy_max_MeV": float(m.group(2)),
            "detector": m.group(3),
        })

    rows = []
    for line in lines:
        if not re.match(r"^\d{4}-\d{2}-\d{2}T", line):
            continue

        fields = line.split()
        if len(fields) != 91:
            raise ValueError(f"Expected 91 fields; found {len(fields)}")

        date = pd.to_datetime(fields[0])
        values = list(map(float, fields[1:]))

        for channel in channels:
            i = channel["index"]
            flux, error, count, livetime, gf = values[i*5:(i+1)*5]
            valid = count > 0 and flux > 0 and error >= 0

            rows.append({
                "date": date,
                **channel,
                "flux": flux if valid else np.nan,
                "error": error if valid else np.nan,
                "count": int(count),
                "livetime_s": livetime,
                "geometry_factor": gf if gf >= 0 else np.nan,
            })

    return pd.DataFrame(rows)

def main():
    df = parse_raw(RAW_FILE)

    # Remove duplicate LD3 versions of the three lowest-energy bins.
    duplicate_ld3 = (
        (df["detector"] == "LD3")
        & df["energy_min_MeV"].isin([3.0, 4.6, 6.2])
    )
    df = df[~duplicate_ld3].copy()

    spectrum = (
        df.groupby(
            ["energy_min_MeV", "energy_max_MeV", "detector"],
            as_index=False,
        )
        .agg(
            valid_days=("flux", "count"),
            mean_differential_intensity=("flux", "mean"),
            median_differential_intensity=("flux", "median"),
            daily_std=("flux", "std"),
            mean_reported_daily_error=("error", "mean"),
        )
    )

    spectrum["energy_width_MeV"] = (
        spectrum["energy_max_MeV"] - spectrum["energy_min_MeV"]
    )
    spectrum["energy_geometric_center_MeV"] = np.sqrt(
        spectrum["energy_min_MeV"] * spectrum["energy_max_MeV"]
    )
    spectrum["plot_energy_MeV"] = spectrum.apply(
        lambda r: PLOT_ENERGY_MEV[
            (float(r["energy_min_MeV"]), float(r["energy_max_MeV"]))
        ],
        axis=1,
    )
    spectrum["bin_integrated_intensity_per_sr"] = (
        spectrum["mean_differential_intensity"] * spectrum["energy_width_MeV"]
    )
    total = spectrum["bin_integrated_intensity_per_sr"].sum()
    spectrum["geant4_bin_probability"] = (
        spectrum["bin_integrated_intensity_per_sr"] / total
    )

    spectrum = spectrum.sort_values("energy_min_MeV").reset_index(drop=True)
    spectrum["geant4_cumulative_probability"] = (
        spectrum["geant4_bin_probability"].cumsum()
    )

    OUT_SPECTRUM.parent.mkdir(parents=True, exist_ok=True)
    spectrum.to_csv(OUT_SPECTRUM, index=False)

    source = spectrum[
        [
            "energy_min_MeV",
            "energy_max_MeV",
            "plot_energy_MeV",
            "mean_differential_intensity",
            "bin_integrated_intensity_per_sr",
            "geant4_bin_probability",
            "geant4_cumulative_probability",
        ]
    ]
    source.to_csv(OUT_SOURCE, index=False)

    print(f"Saved {len(spectrum)} unique measured proton bins.")
    print(f"Probability sum = {source['geant4_bin_probability'].sum():.12f}")

if __name__ == "__main__":
    main()
