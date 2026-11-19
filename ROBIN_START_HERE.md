# Robin's SM809 Pro project

This is a local working branch of lacno29's SM809 Pro application. It keeps the existing PySide6 interface, DPI/profile overlay, macro system and per-app profile switching.

Upstream: https://github.com/lacno29/solakaka-sm809pro-custom-driver

Starting commit: `83674c897f6a132a6e923904ccbbe2773974b553`.
Local branch: `fix/preserve-scroll-wheel`.

Robin's GitHub fork: https://github.com/mutzznutzz/solakaka-sm809pro-custom-driver
The local `origin` remote points to Robin's fork; `upstream` points to lacno29's original repository.

## What is implemented

- The UI and saved profiles still contain 16 physical-button assignments.
- The writer adds two separate wheel entries, producing 18 protocol slots in two nine-entry packets.
- Wheel Up is `10 20 00`; Wheel Down is `10 40 00`.
- The existing packet builder calculates the sequence/checksum. There is no fixed 32-byte packet blindly replayed to the mouse.
- USB product ID `04F3:809E` is classified as wired, rather than Bluetooth.
- New regression tests check wheel bytes, all physical-button remaps, repeated maps/macro references, checksums, write failure reporting, capture decoding and device classification.
- `tools/inspect_key_report.py` reads a pasted report offline and checks its framing/checksum. It cannot open or write a mouse.

The wheel values come from Robin's working official profile after Restore. Static disassembly of the installed GamingMS.exe showed an 18-entry map with 9+9 writes. The old custom writer sent 9+7 and filled the two remaining entries with FF bytes. This patch is supported by those observations and offline tests, but is NOT yet verified by a live USB capture or a patched-app hardware trial. Other hardware/firmware revisions also need testing.

## What to do next

1. Follow [CAPTURE_GUIDE.md](CAPTURE_GUIDE.md) to capture the original software. Keep the old custom executable closed.
2. Share the capture or the two complete mapping reports. We can compare them with the writer before testing the patched app.
3. Export the working official profile before a hardware trial. Test one side-button remap, wheel up/down and middle click first. Then test two profiles and per-app switching, including the overlay.
4. Resolve the licence questions in [RELEASE_AND_FEATURES.md](RELEASE_AND_FEATURES.md) before redistributing.

Robin created the GitHub fork. The prepared changes are on a separate development branch for review. No pull request or executable release has been created. No installed manufacturer files or mouse settings were modified. No patched executable has been built or launched.

## Offline tests

From this directory:

```powershell
python tests/test_offline.py
python tests/test_wheel_regression.py
```

The existing GUI suite needs PySide6:

```powershell
python tests/test_gui_headless.py
```

The first two suites were run during preparation. The GUI suite wasn't run because PySide6 isn't installed in the analysis Python environment. The patch doesn't edit GUI or auto-switch source, but that is not a substitute for a full GUI and hardware test.

## Working in Codex

Open this folder as the project. Read this file, CAPTURE_GUIDE.md and RELEASE_AND_FEATURES.md first. Review the git diff. Keep `NUM_BUTTONS=16`; the wheel entries are additional protocol slots, not two new physical GUI buttons. Never include the official installer or vendor DLLs/assets in a public build. Do not publish a fixed binary until permission/licensing and the hardware validation are resolved.

Build instructions for the upstream app are still in README.md. Build dependencies include PySide6, hidapi and PyInstaller. Installation/building was not performed as part of this preparation.
