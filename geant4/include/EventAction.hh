#ifndef EVENT_ACTION_HH
#define EVENT_ACTION_HH

#include "G4UserEventAction.hh"
#include "globals.hh"

class G4Event;
class PrimaryGeneratorAction;
class RunAction;

class EventAction : public G4UserEventAction {
public:
    EventAction(
        const PrimaryGeneratorAction* generator,
        RunAction* runAction
    );

    ~EventAction() override = default;

    void BeginOfEventAction(const G4Event* event) override;
    void EndOfEventAction(const G4Event* event) override;

    void AddSiliconEnergyDeposit(G4double energy) {
        fSiliconEnergyDeposit += energy;
    }

private:
    const PrimaryGeneratorAction* fGenerator;
    RunAction* fRunAction;

    G4double fSiliconEnergyDeposit = 0.0;
};

#endif
