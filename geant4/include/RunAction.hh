#ifndef RUN_ACTION_HH
#define RUN_ACTION_HH

#include "G4UserRunAction.hh"
#include "globals.hh"

#include <fstream>
#include <string>

class G4Run;

class RunAction : public G4UserRunAction {
public:
    RunAction(
        std::string outputCsv,
        G4double shieldThickness,
        G4double siliconThickness
    );

    ~RunAction() override = default;

    void BeginOfRunAction(const G4Run* run) override;
    void EndOfRunAction(const G4Run* run) override;

    void WriteEvent(
        G4int eventId,
        G4int sourceBin,
        G4double primaryEnergyMeV,
        G4double cosTheta,
        G4double siliconEnergyDepositMeV
    );

private:
    std::string fOutputCsv;
    G4double fShieldThickness;
    G4double fSiliconThickness;
    std::ofstream fOutput;
};

#endif
