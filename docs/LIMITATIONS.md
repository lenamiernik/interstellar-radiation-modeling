# Limitations

The current model is intentionally simplified.

1. Only the selected Voyager 1 proton channels are included.
2. Helium and heavier galactic cosmic-ray species are not yet modeled.
3. Solar energetic particle events are excluded.
4. Unmeasured gaps between Voyager energy channels are not interpolated.
5. The 2013-2021 spectrum is treated as representative of a much longer hypothetical mission.
6. Spacecraft structure is represented as planar aluminum shielding rather than a full spacecraft geometry.
7. Silicon is used as an electronics proxy rather than a transistor- or device-level model.
8. The initial Geant4 physics list and production cut still require sensitivity checks.
9. Mission trajectories, acceleration/deceleration, stellar-environment changes near Proxima Centauri, and relativistic transformations of the external particle spectrum are outside the current model.
10. The OpenMC comparison is a matched-energy neutron sensitivity study and should not be interpreted as a direct simulation of the Voyager proton environment.
