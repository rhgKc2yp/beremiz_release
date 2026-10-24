# Beremiz community Linux releases

Builds unmodified [Beremiz](https://beremiz.org/) sources into a Linux archive
for FlatPark. This repository is independent of the Beremiz project. Upstream
publishes Linux Snap packages; this build does not unpack or depend on Snap.

The archive contains Beremiz, MatIEC, Modbus, CANopen, open62541, Python
dependencies and a GCC toolchain. It targets `org.gnome.Platform//51`, rather
than arbitrary host distributions. Optional BACnet and Inkscape/SVG HMI support
are not included. wxPython is staged from official Ubuntu 26.04 packages, as in
upstream's documented Linux dependency setup. See [the build instructions](docs/build.md).
