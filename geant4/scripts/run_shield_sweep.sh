#!/usr/bin/env bash
set -euo pipefail

EXECUTABLE="${1:-./build/voyager_geant4}"
SPECTRUM="${2:-data/processed/geant4_voyager_proton_source_bins.csv}"
N_EVENTS="${N_EVENTS:-200000}"
BASE_SEED="${BASE_SEED:-12345}"

mkdir -p results

shield_values=(0 1 2 5 10 20)

for i in "${!shield_values[@]}"; do
    shield="${shield_values[$i]}"
    seed=$((BASE_SEED + i))

    echo "Running ${shield} mm Al with ${N_EVENTS} events..."

    "${EXECUTABLE}" \
        "${SPECTRUM}" \
        "${shield}" \
        "${N_EVENTS}" \
        "results/shield_${shield}mm.csv" \
        "${seed}"
done

echo "Sweep complete."
