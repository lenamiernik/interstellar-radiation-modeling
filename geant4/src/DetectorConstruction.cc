#include "DetectorConstruction.hh"

#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"

DetectorConstruction::DetectorConstruction(G4double shieldThickness)
    : G4VUserDetectorConstruction(),
      fShieldThickness(shieldThickness),
      fSiliconThickness(0.5 * mm),
      fSlabHalfSize(1.0 * m),
      fSourceHalfSize(5.0 * cm),
      fSourceGap(1.0 * mm) {}

G4double DetectorConstruction::GetSourceZ() const {
    // Source plane is placed just upstream of the aluminum shield.
    // With zero shielding it is placed upstream of the silicon layer.
    if (fShieldThickness > 0.0) {
        return -0.5 * fShieldThickness - fSourceGap;
    }

    return -0.5 * fSiliconThickness - fSourceGap;
}

G4VPhysicalVolume* DetectorConstruction::Construct() {
    auto* nist = G4NistManager::Instance();

    auto* vacuum = nist->FindOrBuildMaterial("G4_Galactic");
    auto* aluminum = nist->FindOrBuildMaterial("G4_Al");
    auto* silicon = nist->FindOrBuildMaterial("G4_Si");

    // Large world volume so the slab model can accommodate oblique incidence.
    auto* worldSolid = new G4Box(
        "World",
        1.5 * m,
        1.5 * m,
        1.5 * m
    );

    auto* worldLogical = new G4LogicalVolume(
        worldSolid,
        vacuum,
        "World"
    );

    auto* worldPhysical = new G4PVPlacement(
        nullptr,
        {},
        worldLogical,
        "World",
        nullptr,
        false,
        0,
        true
    );

    // Aluminum shield. For the 0 mm case this volume is omitted.
    if (fShieldThickness > 0.0) {
        auto* shieldSolid = new G4Box(
            "AluminumShield",
            fSlabHalfSize,
            fSlabHalfSize,
            0.5 * fShieldThickness
        );

        auto* shieldLogical = new G4LogicalVolume(
            shieldSolid,
            aluminum,
            "AluminumShield"
        );

        new G4PVPlacement(
            nullptr,
            G4ThreeVector(0, 0, 0),
            shieldLogical,
            "AluminumShield",
            worldLogical,
            false,
            0,
            true
        );
    }

    // Silicon electronics proxy: a 0.5 mm silicon slab immediately downstream.
    const G4double siliconCenterZ =
        (fShieldThickness > 0.0)
            ? 0.5 * fShieldThickness + 0.5 * fSiliconThickness
            : 0.0;

    auto* siliconSolid = new G4Box(
        "SiliconTarget",
        fSlabHalfSize,
        fSlabHalfSize,
        0.5 * fSiliconThickness
    );

    fSiliconLogical = new G4LogicalVolume(
        siliconSolid,
        silicon,
        "SiliconTarget"
    );

    new G4PVPlacement(
        nullptr,
        G4ThreeVector(0, 0, siliconCenterZ),
        fSiliconLogical,
        "SiliconTarget",
        worldLogical,
        false,
        0,
        true
    );

    return worldPhysical;
}
