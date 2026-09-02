#include "SteppingAction.hh"

#include "DetectorConstruction.hh"
#include "EventAction.hh"

#include "G4LogicalVolume.hh"
#include "G4Step.hh"
#include "G4VPhysicalVolume.hh"

SteppingAction::SteppingAction(
    const DetectorConstruction* detector,
    EventAction* eventAction
)
    : G4UserSteppingAction(),
      fDetector(detector),
      fEventAction(eventAction) {}

void SteppingAction::UserSteppingAction(const G4Step* step) {
    auto* physicalVolume =
        step->GetPreStepPoint()->GetTouchableHandle()->GetVolume();

    if (physicalVolume == nullptr) {
        return;
    }

    if (
        physicalVolume->GetLogicalVolume()
        != fDetector->GetSiliconLogicalVolume()
    ) {
        return;
    }

    // Includes energy deposited by the primary proton and all secondaries.
    fEventAction->AddSiliconEnergyDeposit(
        step->GetTotalEnergyDeposit()
    );
}
