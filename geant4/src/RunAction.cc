#include "RunAction.hh"

#include "G4Run.hh"
#include "G4SystemOfUnits.hh"

#include <iomanip>
#include <stdexcept>
#include <utility>

RunAction::RunAction(
    std::string outputCsv,
    G4double shieldThickness,
    G4double siliconThickness
)
    : G4UserRunAction(),
      fOutputCsv(std::move(outputCsv)),
      fShieldThickness(shieldThickness),
      fSiliconThickness(siliconThickness) {}

void RunAction::BeginOfRunAction(const G4Run*) {
    fOutput.open(fOutputCsv, std::ios::out);

    if (!fOutput) {
        throw std::runtime_error(
            "Could not open output CSV: " + fOutputCsv
        );
    }

    fOutput
        << "event_id,"
        << "source_bin_index,"
        << "primary_energy_MeV,"
        << "cos_theta,"
        << "shield_thickness_mm,"
        << "silicon_thickness_mm,"
        << "silicon_edep_MeV\n";

    fOutput << std::setprecision(12);
}

void RunAction::EndOfRunAction(const G4Run*) {
    if (fOutput.is_open()) {
        fOutput.flush();
        fOutput.close();
    }
}

void RunAction::WriteEvent(
    G4int eventId,
    G4int sourceBin,
    G4double primaryEnergyMeV,
    G4double cosTheta,
    G4double siliconEnergyDepositMeV
) {
    fOutput
        << eventId << ","
        << sourceBin << ","
        << primaryEnergyMeV << ","
        << cosTheta << ","
        << fShieldThickness / mm << ","
        << fSiliconThickness / mm << ","
        << siliconEnergyDepositMeV << "\n";
}
