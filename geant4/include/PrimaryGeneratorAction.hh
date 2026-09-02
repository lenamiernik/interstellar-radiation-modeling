#ifndef PRIMARY_GENERATOR_ACTION_HH
#define PRIMARY_GENERATOR_ACTION_HH

#include "G4VUserPrimaryGeneratorAction.hh"
#include "globals.hh"

#include <string>
#include <vector>

class DetectorConstruction;
class G4Event;
class G4ParticleGun;

struct VoyagerEnergyBin {
    G4double energyMinMeV;
    G4double energyMaxMeV;
    G4double probability;
    G4double cumulativeProbability;
};

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction {
public:
    PrimaryGeneratorAction(
        const DetectorConstruction* detector,
        const std::string& spectrumCsv
    );

    ~PrimaryGeneratorAction() override;

    void GeneratePrimaries(G4Event* event) override;

    G4double GetCurrentEnergyMeV() const {
        return fCurrentEnergyMeV;
    }

    G4double GetCurrentCosTheta() const {
        return fCurrentCosTheta;
    }

    G4int GetCurrentBinIndex() const {
        return fCurrentBinIndex;
    }

private:
    void LoadSpectrum(const std::string& spectrumCsv);
    G4int SampleBinIndex() const;

    const DetectorConstruction* fDetector;
    G4ParticleGun* fParticleGun;

    std::vector<VoyagerEnergyBin> fBins;

    G4double fCurrentEnergyMeV = 0.0;
    G4double fCurrentCosTheta = 1.0;
    G4int fCurrentBinIndex = -1;
};

#endif
