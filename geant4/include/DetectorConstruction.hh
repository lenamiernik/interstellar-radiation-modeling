#ifndef DETECTOR_CONSTRUCTION_HH
#define DETECTOR_CONSTRUCTION_HH

#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

class G4LogicalVolume;
class G4VPhysicalVolume;

class DetectorConstruction : public G4VUserDetectorConstruction {
public:
    explicit DetectorConstruction(G4double shieldThickness);
    ~DetectorConstruction() override = default;

    G4VPhysicalVolume* Construct() override;

    G4LogicalVolume* GetSiliconLogicalVolume() const {
        return fSiliconLogical;
    }

    G4double GetShieldThickness() const {
        return fShieldThickness;
    }

    G4double GetSiliconThickness() const {
        return fSiliconThickness;
    }

    G4double GetSourceZ() const;
    G4double GetSourceHalfSize() const {
        return fSourceHalfSize;
    }

private:
    G4double fShieldThickness;

    // Fixed v1 geometry parameters.
    const G4double fSiliconThickness;
    const G4double fSlabHalfSize;
    const G4double fSourceHalfSize;
    const G4double fSourceGap;

    G4LogicalVolume* fSiliconLogical = nullptr;
};

#endif
