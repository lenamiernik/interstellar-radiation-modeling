from pathlib import Path
import argparse
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


MEV_TO_J = 1.602176634e-13
SECONDS_PER_YEAR = 365.25 * 24 * 3600

# Integrated over the measured Voyager energy bands and converted
# from isotropic differential intensity to planar incident flux:
# F = pi * integral J(E)dE
DEFAULT_PLANAR_PROTON_FLUX = 14350.276  # protons / m^2 / s

SILICON_DENSITY_KG_M3 = 2330.0

DEFAULT_MISSIONS = {
    "0.1c (~50 yr)": 50.0,
    "0.01c (~500 yr)": 500.0,
    "Present-day-speed (~7000 yr)": 7000.0,
}


def summarize_file(path: Path) -> dict:
    df = pd.read_csv(path)

    required = {
        "shield_thickness_mm",
        "silicon_thickness_mm",
        "silicon_edep_MeV",
    }

    missing = required.difference(df.columns)

    if missing:
        raise ValueError(
            f"{path} is missing required columns: {sorted(missing)}"
        )

    edep = df["silicon_edep_MeV"].to_numpy(dtype=float)

    n = len(edep)

    if n == 0:
        raise ValueError(f"{path} contains no events.")

    mean_edep = float(np.mean(edep))
    std_edep = float(np.std(edep, ddof=1)) if n > 1 else 0.0
    sem_edep = std_edep / math.sqrt(n) if n > 1 else 0.0

    return {
        "file": path.name,
        "n_events": n,
        "shield_thickness_mm": float(df["shield_thickness_mm"].iloc[0]),
        "silicon_thickness_mm": float(df["silicon_thickness_mm"].iloc[0]),
        "mean_edep_MeV_per_incident_proton": mean_edep,
        "std_edep_MeV": std_edep,
        "sem_edep_MeV": sem_edep,
        "fraction_zero_edep": float(np.mean(edep == 0.0)),
        "mean_primary_energy_MeV": float(df["primary_energy_MeV"].mean()),
        "mean_cos_theta": float(df["cos_theta"].mean()),
    }


def calculate_mission_dose(
    mean_edep_mev: float,
    silicon_thickness_mm: float,
    mission_years: float,
    planar_flux: float,
) -> float:
    """
    Convert mean energy deposited per incident proton into accumulated
    absorbed dose in the silicon slab.

    Energy deposited per unit area:
        E/A = <Edep> * fluence

    Silicon areal mass:
        m/A = rho * thickness

    Dose:
        D = (E/A) / (m/A)
    """

    thickness_m = silicon_thickness_mm * 1e-3

    areal_mass_kg_m2 = (
        SILICON_DENSITY_KG_M3 * thickness_m
    )

    fluence_m2 = (
        planar_flux
        * mission_years
        * SECONDS_PER_YEAR
    )

    deposited_energy_j_m2 = (
        mean_edep_mev
        * MEV_TO_J
        * fluence_m2
    )

    return deposited_energy_j_m2 / areal_mass_kg_m2


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory containing shield_*mm.csv event files.",
    )

    parser.add_argument(
        "--planar-flux",
        type=float,
        default=DEFAULT_PLANAR_PROTON_FLUX,
        help=(
            "Measured-band planar proton flux in protons/m^2/s. "
            "Default corresponds to the finalized Voyager v1 spectrum."
        ),
    )

    parser.add_argument(
        "--output-dir",
        default="results/summary",
    )

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(results_dir.glob("shield_*mm.csv"))

    if not files:
        raise SystemExit(
            f"No shield_*mm.csv files found in {results_dir}"
        )

    summaries = [
        summarize_file(path)
        for path in files
    ]

    summary = pd.DataFrame(summaries).sort_values(
        "shield_thickness_mm"
    )

    for mission_name, years in DEFAULT_MISSIONS.items():
        summary[f"dose_Gy_{years:g}yr"] = summary.apply(
            lambda row: calculate_mission_dose(
                row["mean_edep_MeV_per_incident_proton"],
                row["silicon_thickness_mm"],
                years,
                args.planar_flux,
            ),
            axis=1,
        )

    summary_path = output_dir / "geant4_shielding_summary.csv"
    summary.to_csv(summary_path, index=False)

    # Plot mean deposited energy per incident proton.
    plt.figure(figsize=(8, 5.5))
    plt.errorbar(
        summary["shield_thickness_mm"],
        summary["mean_edep_MeV_per_incident_proton"],
        yerr=summary["sem_edep_MeV"],
        marker="o",
        capsize=3,
    )
    plt.xlabel("Aluminum shield thickness [mm]")
    plt.ylabel("Mean silicon energy deposition [MeV / incident proton]")
    plt.title("Voyager-derived proton transport through aluminum shielding")
    plt.tight_layout()
    plt.savefig(
        output_dir / "mean_edep_vs_shielding.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close()

    # Plot accumulated dose for mission scenarios.
    plt.figure(figsize=(8, 5.5))

    for mission_name, years in DEFAULT_MISSIONS.items():
        plt.plot(
            summary["shield_thickness_mm"],
            summary[f"dose_Gy_{years:g}yr"],
            marker="o",
            label=mission_name,
        )

    plt.yscale("log")
    plt.xlabel("Aluminum shield thickness [mm]")
    plt.ylabel("Estimated accumulated silicon dose [Gy]")
    plt.title("Mission-duration scaling of Voyager-band proton exposure")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        output_dir / "mission_dose_vs_shielding.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close()

    print(summary.to_string(index=False))
    print(f"\nSaved: {summary_path}")


if __name__ == "__main__":
    main()
