# Feature test v3, 20 November 2026

Robin confirmed that v2 starts successfully and scrolling continues to work in
the browser after configuring the mouse. The following changes address his
subsequent test feedback.

## Changes

- Separate Scroll Up and Scroll Down action pickers below the 16 numbered
  buttons. Normal scrolling can be restored without resetting other buttons.
  Wheel mappings are saved per profile and included when buttons or profiles
  are applied. Keyboard, mouse and media actions are supported here; macro and
  app-launch bindings remain restricted to the existing numbered buttons.
- Windows scroll lines/page control, applied only by its explicit button. It
  affects all mice and is not an onboard or per-profile mouse setting.
- Sparse enabled DPI rows survive edits, profile changes and restarts. Enabled
  rows are packed into consecutive device stages; device stage notifications
  map back to the correct visible row. For example rows 1, 3, 5, 7 become four
  hardware stages, with those rows' values and colours.
- Receiver PID 04F3:809F is recognised as 2.4 GHz. Wired PID 04F3:809E remains
  recognised as USB wired.
- Wired status displays USB powered and does not raise battery alerts based on
  the wired interface's zero battery reading. This does not claim a battery
  charge level or charge-completion state.
- Explicit polling changes show an immediate Applying message when the HUD is
  enabled, followed by command success/failure. Success means the HID write
  succeeded; the top bar remains based on device telemetry.
- Experimental custom side-lighting colour picker uses the existing RGB report
  fields and the same picker as DPI colours. The upstream author's firmware
  ignored these RGB fields in solid modes. Actual custom-colour support on
  Robin's firmware remains unverified; presets continue to be available.
- Original app artwork and a separate static-glow tray icon. No animation.
- Motion wake-up renamed to Wake mouse on movement, with an explanatory tooltip.
  Sleep time already supports one-minute steps, including 25 minutes.

## Validation

- Existing offline protocol suite: 49 passed.
- Existing wheel regression suite: 6 passed.
- New feedback regression suite: 7 passed.
- Existing complete offscreen GUI suite: ALL GOOD.
- Built executable startup check: passed with HID access disabled and temporary
  profiles; main window and overlay created successfully.
- No automated validation writes to the connected mouse or changes Windows
  scroll settings. Test stores are temporary and hardware access is mocked.

Physical DPI cycling, receiver reconnection, custom wheel shortcuts and custom
RGB still need testing on the mouse. In particular, the mapping fix addresses
disabled gaps and incorrect highlights; it does not establish whether this
firmware supports eight simultaneously enabled hardware stages. The report
format is unchanged rather than substituting unverified firmware commands.

Macros and application switching retain the existing implementations and pass
the existing simulated GUI checks. Robin's latest report did not physically
verify those features.

## Trying the build

Exit the previous custom app from its tray menu before launching v3. Keep a copy
of its portable config directory before replacing files. To carry settings over,
put v3 beside the same config directory. Existing profiles are read without a
migration; new wheel and sparse-DPI data are added when those controls are used.

Test rows 1, 3, 5, 7 first. The physical DPI buttons should cycle their configured
values and highlight those same four rows. Then reconnect through the receiver
and through the cable, checking the connection label and battery notice. Test
wheel shortcuts separately and use Restore normal scrolling afterwards.

Build with `python tools/build_test.py`. Output:
`dist/feature-test-v3/SM809Pro.exe`. This preserves the clean DLL search path
needed to avoid the previous QtWidgets startup error.
