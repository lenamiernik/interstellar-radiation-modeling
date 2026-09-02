#include "ActionInitialization.hh"
#include "DetectorConstruction.hh"

#include "G4EmStandardPhysics_option4.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"
#include "QGSP_BIC.hh"

#include "Randomize.hh"

#include <CLHEP/Random/Random.h>

#include <cstdlib>
#include <exception>
#include <iostream>
#include <string>

namespace {

void PrintUsage(const char* program) {
    std::cerr
        << "Usage:\n  "
        << program
        << " <spectrum.csv> <shield_mm> <n_events> <output.csv> [seed]\n\n"
        << "Example:\n  "
        << program
        << " data/processed/geant4_voyager_proton_source_bins.csv "
        << "5 200000 results/shield_5mm.csv 12345\n";
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 5 || argc > 6) {
        PrintUsage(argv[0]);
        return EXIT_FAILURE;
    }

    try {
        const std::string spectrumCsv = argv[1];
        const G4double shieldThicknessMm = std::stod(argv[2]);
        const G4int numberOfEvents = std::stoi(argv[3]);
        const std::string outputCsv = argv[4];

        const long seed =
            (argc == 6)
                ? std::stol(argv[5])
                : 12345L;

        if (shieldThicknessMm < 0.0) {
            throw std::runtime_error(
                "Shield thickness cannot be negative."
            );
        }

        if (numberOfEvents <= 0) {
            throw std::runtime_error(
                "Number of events must be positive."
            );
        }

        // Serial run manager keeps file output simple and reproducible.
        auto* runManager = new G4RunManager();

        auto* detector = new DetectorConstruction(
            shieldThicknessMm * mm
        );

        runManager->SetUserInitialization(detector);

        // QGSP_BIC uses Binary Cascade for proton/nucleon interactions
        // over the energy range relevant to this project.
        auto* physics = new QGSP_BIC();

        // Replace the default EM constructor with Geant4's high-accuracy
        // standard electromagnetic option.
        physics->ReplacePhysics(
            new G4EmStandardPhysics_option4()
        );

        // Production cut. This is a model parameter and should later
        // be checked in a convergence study.
        physics->SetDefaultCutValue(0.01 * mm);

        runManager->SetUserInitialization(physics);

        runManager->SetUserInitialization(
            new ActionInitialization(
                detector,
                spectrumCsv,
                outputCsv
            )
        );

        CLHEP::HepRandom::setTheSeed(seed);

        runManager->Initialize();

        runManager->BeamOn(numberOfEvents);

        delete runManager;

        return EXIT_SUCCESS;

    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return EXIT_FAILURE;
    }
}
