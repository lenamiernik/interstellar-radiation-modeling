"""
Run matched-energy OpenMC shield sweeps.

Examples
--------
Export XML only:
    python run_sweep.py --export-only

Run supported energy cases:
    python run_sweep.py --run

Run a single energy:
    python run_sweep.py --run --energies 10.2 23.9 52.0

Optional hypothetical Voyager-weighted neutral source:
    python run_sweep.py --run --weighted-neutral
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import openmc
import pandas as pd

from model import ModelConfig, build_model


ROOT = Path(__file__).resolve().parent
ENERGY_GRID = ROOT / "data/openmc_matched_energy_grid.csv"
VOYAGER_SOURCE = ROOT / "data/voyager_matched_source_bins.csv"
RUNS_DIR = ROOT / "runs"

DEFAULT_SHIELDS_MM = [0, 1, 2, 5, 10, 20]


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute OpenMC after exporting model inputs.",
    )

    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Export XML inputs without running transport.",
    )

    parser.add_argument(
        "--energies",
        nargs="*",
        type=float,
        default=None,
        help="Optional subset of matched energies in MeV.",
    )

    parser.add_argument(
        "--shields",
        nargs="*",
        type=float,
        default=DEFAULT_SHIELDS_MM,
        help="Aluminum shield thicknesses in mm.",
    )

    parser.add_argument(
        "--batches",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--particles",
        type=int,
        default=50_000,
        help="Particles per batch.",
    )

    parser.add_argument(
        "--weighted-neutral",
        action="store_true",
        help=(
            "Also run a hypothetical neutron source with Voyager proton-spectrum "
            "weights. This is a sensitivity case, not a measured neutron field."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if not args.run and not args.export_only:
        args.export_only = True

    energy_df = pd.read_csv(ENERGY_GRID)

    if args.energies:
        energies = args.energies
    else:
        energies = energy_df["matched_neutron_energy_MeV"].tolist()

    manifest = []

    for shield_mm in args.shields:
        for energy_mev in energies:
            case_name = f"mono_{energy_mev:g}MeV_shield_{shield_mm:g}mm"
            case_dir = RUNS_DIR / case_name

            config = ModelConfig(
                shield_mm=shield_mm,
                source_mode="mono",
                energy_mev=energy_mev,
                batches=args.batches,
                particles_per_batch=args.particles,
            )

            model = build_model(config)
            model.export_to_xml(case_dir)

            statepoint = None

            if args.run:
                statepoint = model.run(
                    cwd=case_dir,
                    export_model_xml=False,
                )

            manifest.append(
                {
                    "case": case_name,
                    "source_mode": "mono",
                    "energy_mev": energy_mev,
                    "shield_mm": shield_mm,
                    "batches": args.batches,
                    "particles_per_batch": args.particles,
                    "statepoint": (
                        str(statepoint) if statepoint is not None else None
                    ),
                }
            )

    if args.weighted_neutral:
        for shield_mm in args.shields:
            case_name = f"voyager_weighted_neutral_shield_{shield_mm:g}mm"
            case_dir = RUNS_DIR / case_name

            config = ModelConfig(
                shield_mm=shield_mm,
                source_mode="voyager_weighted_neutral",
                batches=args.batches,
                particles_per_batch=args.particles,
            )

            model = build_model(
                config,
                voyager_source_csv=VOYAGER_SOURCE,
            )

            model.export_to_xml(case_dir)

            statepoint = None

            if args.run:
                statepoint = model.run(
                    cwd=case_dir,
                    export_model_xml=False,
                )

            manifest.append(
                {
                    "case": case_name,
                    "source_mode": "voyager_weighted_neutral",
                    "energy_mev": None,
                    "shield_mm": shield_mm,
                    "batches": args.batches,
                    "particles_per_batch": args.particles,
                    "statepoint": (
                        str(statepoint) if statepoint is not None else None
                    ),
                }
            )

    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    manifest_path = RUNS_DIR / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(f"Prepared {len(manifest)} OpenMC cases.")
    print(f"Manifest: {manifest_path}")

    if not args.run:
        print("Transport was NOT executed; XML inputs were exported only.")


if __name__ == "__main__":
    main()
