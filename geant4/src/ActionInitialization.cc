#include "ActionInitialization.hh"

#include "DetectorConstruction.hh"
#include "EventAction.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "SteppingAction.hh"

#include <utility>

ActionInitialization::ActionInitialization(
    const DetectorConstruction* detector,
    std::string spectrumCsv,
    std::string outputCsv
)
    : G4VUserActionInitialization(),
      fDetector(detector),
      fSpectrumCsv(std::move(spectrumCsv)),
      fOutputCsv(std::move(outputCsv)) {}

void ActionInitialization::Build() const {
    auto* runAction = new RunAction(
        fOutputCsv,
        fDetector->GetShieldThickness(),
        fDetector->GetSiliconThickness()
    );

    SetUserAction(runAction);

    auto* generator = new PrimaryGeneratorAction(
        fDetector,
        fSpectrumCsv
    );

    SetUserAction(generator);

    auto* eventAction = new EventAction(
        generator,
        runAction
    );

    SetUserAction(eventAction);

    SetUserAction(
        new SteppingAction(
            fDetector,
            eventAction
        )
    );
}
