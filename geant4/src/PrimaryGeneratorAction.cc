#include "PrimaryGeneratorAction.hh"

#include "DetectorConstruction.hh"

#include "G4Event.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4PhysicalConstants.hh"
#include "G4ThreeVector.hh"
#include "G4Proton.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"

#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

namespace {

std::vector<std::string> SplitCsvLine(const std::string& line) {
    std::vector<std::string> fields;
    std::stringstream ss(line);
    std::string item;

    while (std::getline(ss, item, ',')) {
        if (!item.empty() && item.back() == '\r') {
            item.pop_back();
        }
        fields.push_back(item);
    }

    return fields;
}

}  // namespace

PrimaryGeneratorAction::PrimaryGeneratorAction(
    const DetectorConstruction* detector,
    const std::string& spectrumCsv
)
    : G4VUserPrimaryGeneratorAction(),
      fDetector(detector),
      fParticleGun(new G4ParticleGun(1)) {

    LoadSpectrum(spectrumCsv);

    fParticleGun->SetParticleDefinition(G4Proton::ProtonDefinition());
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() {
    delete fParticleGun;
}

void PrimaryGeneratorAction::LoadSpectrum(const std::string& spectrumCsv) {
    std::ifstream input(spectrumCsv);

    if (!input) {
        throw std::runtime_error(
            "Could not open Voyager spectrum CSV: " + spectrumCsv
        );
    }

    std::string line;

    if (!std::getline(input, line)) {
        throw std::runtime_error("Voyager spectrum CSV is empty.");
    }

    const auto header = SplitCsvLine(line);
    std::unordered_map<std::string, std::size_t> column;

    for (std::size_t i = 0; i < header.size(); ++i) {
        column[header[i]] = i;
    }

    const std::vector<std::string> required = {
        "energy_min_MeV",
        "energy_max_MeV",
        "geant4_bin_probability"
    };

    for (const auto& name : required) {
        if (column.find(name) == column.end()) {
            throw std::runtime_error(
                "Missing required spectrum column: " + name
            );
        }
    }

    G4double probabilitySum = 0.0;

    while (std::getline(input, line)) {
        if (line.empty()) {
            continue;
        }

        const auto fields = SplitCsvLine(line);

        VoyagerEnergyBin bin;
        bin.energyMinMeV =
            std::stod(fields.at(column.at("energy_min_MeV")));
        bin.energyMaxMeV =
            std::stod(fields.at(column.at("energy_max_MeV")));
        bin.probability =
            std::stod(fields.at(column.at("geant4_bin_probability")));

        if (bin.energyMaxMeV <= bin.energyMinMeV) {
            throw std::runtime_error(
                "Invalid Voyager energy bin encountered."
            );
        }

        if (bin.probability < 0.0) {
            throw std::runtime_error(
                "Negative source probability encountered."
            );
        }

        probabilitySum += bin.probability;
        fBins.push_back(bin);
    }

    if (fBins.empty() || probabilitySum <= 0.0) {
        throw std::runtime_error(
            "No valid Voyager source bins were loaded."
        );
    }

    // Normalize again in C++ so the simulation does not depend on
    // floating-point rounding in the CSV.
    G4double cumulative = 0.0;

    for (auto& bin : fBins) {
        bin.probability /= probabilitySum;
        cumulative += bin.probability;
        bin.cumulativeProbability = cumulative;
    }

    // Guarantee a closed cumulative distribution.
    fBins.back().cumulativeProbability = 1.0;
}

G4int PrimaryGeneratorAction::SampleBinIndex() const {
    const G4double u = G4UniformRand();

    for (std::size_t i = 0; i < fBins.size(); ++i) {
        if (u <= fBins[i].cumulativeProbability) {
            return static_cast<G4int>(i);
        }
    }

    return static_cast<G4int>(fBins.size() - 1);
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
    // ------------------------------------------------------------
    // Sample energy from the empirical Voyager measured-bin spectrum.
    //
    // Bin selection probability is proportional to J_i * DeltaE_i.
    // Within a selected bin, differential intensity is treated as
    // piecewise constant, so energy is sampled uniformly.
    // ------------------------------------------------------------

    fCurrentBinIndex = SampleBinIndex();

    const auto& bin = fBins.at(
        static_cast<std::size_t>(fCurrentBinIndex)
    );

    fCurrentEnergyMeV =
        bin.energyMinMeV
        + G4UniformRand() * (bin.energyMaxMeV - bin.energyMinMeV);

    fParticleGun->SetParticleEnergy(fCurrentEnergyMeV * MeV);

    // ------------------------------------------------------------
    // Position:
    // Sample uniformly over a centered source plane immediately
    // upstream of the aluminum shield.
    // ------------------------------------------------------------

    const G4double halfSize = fDetector->GetSourceHalfSize();

    const G4double x =
        (2.0 * G4UniformRand() - 1.0) * halfSize;

    const G4double y =
        (2.0 * G4UniformRand() - 1.0) * halfSize;

    const G4double z = fDetector->GetSourceZ();

    fParticleGun->SetParticlePosition(
        G4ThreeVector(x, y, z)
    );

    // ------------------------------------------------------------
    // Direction:
    //
    // Voyager intensity is treated as isotropic.
    //
    // For particles CROSSING a plane from an isotropic field,
    // p(mu) = 2 mu, where mu = cos(theta).
    // Therefore mu = sqrt(U), with U uniform on [0,1].
    // ------------------------------------------------------------

    const G4double mu = std::sqrt(G4UniformRand());
    const G4double phi = twopi * G4UniformRand();
    const G4double sinTheta = std::sqrt(1.0 - mu * mu);

    const G4ThreeVector direction(
        sinTheta * std::cos(phi),
        sinTheta * std::sin(phi),
        mu
    );

    fCurrentCosTheta = mu;

    fParticleGun->SetParticleMomentumDirection(direction);

    fParticleGun->GeneratePrimaryVertex(event);
}
