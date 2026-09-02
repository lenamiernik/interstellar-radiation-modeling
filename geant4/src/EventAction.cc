#include "EventAction.hh"

#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"

#include "G4Event.hh"
#include "G4SystemOfUnits.hh"

EventAction::EventAction(
    const PrimaryGeneratorAction* generator,
    RunAction* runAction
)
    : G4UserEventAction(),
      fGenerator(generator),
      fRunAction(runAction) {}

void EventAction::BeginOfEventAction(const G4Event*) {
    fSiliconEnergyDeposit = 0.0;
}

void EventAction::EndOfEventAction(const G4Event* event) {
    fRunAction->WriteEvent(
        event->GetEventID(),
        fGenerator->GetCurrentBinIndex(),
        fGenerator->GetCurrentEnergyMeV(),
        fGenerator->GetCurrentCosTheta(),
        fSiliconEnergyDeposit / MeV
    );
}
