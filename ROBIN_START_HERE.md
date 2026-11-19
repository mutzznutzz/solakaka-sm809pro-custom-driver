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

Robin created the GitHub fork. The prepared changes are on a separate development branch for review. No pull request or public executable release has been created. No installed manufacturer files or mouse settings were modified. A portable test executable has been built and its hardware-disabled startup test has passed; normal operation against the mouse still needs testing.

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

All three suites have now passed. The GUI suite was run in an isolated Python 3.12 environment with PySide6 6.12.0 and hardware access mocked out. It exercised the main window, overlay, profile matching/debounce/fallback, macros and connection handling. This does not substitute for a mouse hardware test.

## Working in Codex

Open this folder as the project. Read this file, CAPTURE_GUIDE.md and RELEASE_AND_FEATURES.md first. Review the git diff. Keep `NUM_BUTTONS=16`; the wheel entries are additional protocol slots, not two new physical GUI buttons. Never include the official installer or vendor DLLs/assets in a public build. Do not publish a fixed binary until permission/licensing and the hardware validation are resolved.

Build dependencies are PySide6, hidapi and PyInstaller. Use the clean build command below rather than invoking PyInstaller with an inherited system PATH.

## Packaging correction

The first portable build failed to import QtWidgets. Static dependency inspection found that PyInstaller had bundled Poppler's unrelated `icuuc.dll` from the inherited PATH; it lacked 20 symbols required by Qt6Core. The source GUI tests used Windows' compatible ICU and therefore passed.

Use `python tools/build_test.py` (or `build_exe.bat`) to build with a clean DLL search path. This avoids collecting unrelated libraries from installed tools. The output is `dist/wheel-fix-test-v2/SM809Pro.exe`.

The packaged application now has a hardware-disabled startup test:

```powershell
.\SM809Pro.exe --self-test --self-test-result startup-result.json
```

It creates and renders the real main window using temporary profiles, verifies the overlay exists, disables HID access and exits. Add `--self-test-native` to use the Windows Qt platform rather than offscreen rendering. A successful test writes `"ok": true` in the JSON result. It does not validate mouse writes. The rebuilt v2 executable passed this self-test with `ok=true`, `hardware_access=disabled` and `overlay_present=true`.
