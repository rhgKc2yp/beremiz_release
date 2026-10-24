# Build and release

Install Flatpak, GNU tar, Python 3 and the Flathub remote, then install
`org.gnome.Sdk//51` and `org.gnome.Platform//51`.

```sh
python3 scripts/resolve.py --tag v1.6.0 --revision 1
bash scripts/run-build.sh
```

The resolver uses the official stable Beremiz tag and the exact dependency
revisions from the recorded upstream distribution recipe. All downloaded
application source archives have SHA-256 entries in `SOURCES.lock.json`.
Upstream's Python dependency lock is used, with wxPython 4.2.4 supplied by the
official Ubuntu 26.04 packages, matching upstream's documented distribution
dependency setup and the GNOME SDK's Python 3.14. Other Python wheels are built
in the SDK. Ubuntu package indexes are checked against the release metadata;
every downloaded package has its size and SHA-256 checked and recorded in
`UBUNTU-PACKAGES.json`. No Beremiz source file is patched.

GCC, binutils, C headers and libc development files come from the recorded
SDK commit. Runtime validation uses the Platform, with networking disabled,
so it cannot accidentally use the SDK compiler. The extracted release archive
is tested a second time at a different path. The test compiles the upstream
IEC language project, transfers it to the local runtime, starts it and requires
its `ALL TESTS OK` result. It does not verify hardware or optional fieldbuses.

The default workflow builds on pushes and pull requests without publishing.
Scheduled runs follow new stable upstream releases. A manual run with `publish`
enabled publishes after both native x86_64 and aarch64 builds pass. Existing
release assets are never replaced; increment `revision` for a rebuild.
Only the final release job has repository write permissions.

The application source archives, build locks and installed Python package list
accompany the payload. Source URLs and exact commits for Python VCS packages
are in the requirements file. GCC/binutils and runtime sources are those of
the recorded GNOME/Freedesktop SDK commit; retain their licence notices and
corresponding sources when redistributing the toolchain.

After publishing, run FlatPark's resolver and `scripts/update-pins.mjs` against
the real release assets. Never submit a manifest with placeholder hashes or
an unavailable release URL. Test the installed Flatpak, including its GUI,
settings persistence and PLC compile/run workflow, before opening a PR.
