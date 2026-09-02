#ifndef ACTION_INITIALIZATION_HH
#define ACTION_INITIALIZATION_HH

#include "G4VUserActionInitialization.hh"

#include <string>

class DetectorConstruction;

class ActionInitialization : public G4VUserActionInitialization {
public:
    ActionInitialization(
        const DetectorConstruction* detector,
        std::string spectrumCsv,
        std::string outputCsv
    );

    ~ActionInitialization() override = default;

    void Build() const override;

private:
    const DetectorConstruction* fDetector;
    std::string fSpectrumCsv;
    std::string fOutputCsv;
};

#endif
