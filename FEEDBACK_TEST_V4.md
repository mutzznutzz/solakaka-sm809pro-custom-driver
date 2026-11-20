# Feature test v4, 20 November 2026

Robin confirmed that v3's wheel controls and sparse DPI stages work on the
physical mouse. Custom side-light RGB does not work on his firmware and has
been removed.

## Changes

- Performance and Lighting is now a single page. The separate Lighting entry is
  removed, and supported preset effects are at the bottom of the combined page.
  Old v3 custom-light profiles load as their underlying solid preset.
- Larger tray artwork fills more of the Windows icon slot and clearly shows a
  mouse, with two buttons, an orange wheel and cyan accents. The glow is static.
  Windows controls the slot size; the drawing is enlarged inside that slot.
- Concise tooltips explain sensor settings, lift-off distance, power controls,
  DPI toggles/sensitivity/colours, wheel actions, Windows scrolling, macro
  timing/play modes and automatic profile switching.
- A readable polling guide explains 125/250/500/1000 Hz as 8/4/2/1 ms between
  reports, with typical uses and the wireless battery / CPU trade-off. These are
  examples, not eligibility requirements for different kinds of gamer. The
  intervals are not total end-to-end input latency.
- Polling feedback now says Applying, then Polling setting sent or Couldn't
  change polling rate. Sending confirms the HID write, not a firmware ACK; the
  header continues to use live mouse telemetry.

## Connection bug and device routing

The old detector accepted every PID under Elan VID 04F3 and labelled unknown
ones Bluetooth. Robin's built-in ELAN0307 / HIDI2C touchpad (PID 3282, I2C bus)
was therefore a Bluetooth candidate. Bluetooth candidates had priority over the
USB receiver, explaining why adding receiver PID 809F alone did not fix v3.

Detection now requires a known mouse PID or SM809/Solakaka identity, excludes
I2C/SPI interfaces, and uses Bluetooth bus/path evidence. Unknown transports
remain unknown rather than being labelled Bluetooth. Even a manually forced
touchpad PID is rejected before opening a handle. Both receiver-to-cable and
cable-to-receiver changes are re-evaluated by connection maintenance.

Bluetooth pairing mode alone cannot prove a Bluetooth connection to this PC.
An unpaired mouse with its receiver still plugged in may instead be shown as
receiver present / mouse offline. Windows Bluetooth devices must actually
connect before they can be identified as Bluetooth by HID transport metadata.

Read-only live enumeration after the fix found one mouse mode on Robin's laptop:
04F3:809E, wired, configurable. The unrelated touchpad is excluded. Receiver
reconnection still needs Robin's physical test; the app was not launched in its
normal hardware-writing mode during automated verification.

## Checks

- Offline protocol checks: 49 passed.
- Wheel regression tests: 6 passed.
- Feedback regression tests: 7 passed.
- New transport/device-isolation tests: 9 passed.
- Existing complete offscreen GUI suite: ALL GOOD, with expected navigation
  positions updated for the combined page.
- Packaged executable startup passed in both offscreen and native Windows Qt
  modes with hardware access disabled and temporary profiles.
- Basic code review covered HID target selection, profile parsing, the local
  single-instance socket and explicit Run App launch bindings. No dynamic code
  evaluation or shell execution was found in those paths. This is not a full
  security audit or a malware-scanner certification.

All automated GUI checks use temporary profiles with hardware access disabled.
They do not alter Windows scroll settings. The direct executable is intended
for local testing; no GitHub binary release was created.

## Guidance sources

The in-app explanations paraphrase manufacturer documentation:

- Logitech: https://www.logi.com/en-gb/discover/a/polling-rate-on-a-mouse
- Corsair: https://www.corsair.com/ca/en/explorer/gamer/mice/understanding-advanced-mouse-sensor-features-motion-sync-lod-angle-snapping-and-ripple-control/
- HIDAPI transport enum: https://github.com/libusb/hidapi/blob/master/hidapi/hidapi.h

## Use

Exit v3 using its tray menu before launching v4. Keep the executable beside the
same portable config folder to retain settings. Build with
`python tools/build_test.py`; output is `dist/feature-test-v4/SM809Pro.exe`.
