# Control Centre v5 test build

Display name: **SM809 Pro Control Centre**. About version: **0.5.0-test**.
V4 remains available separately; this build reads the same portable config files.

## Backup and restore

Profiles now has **Back up all settings** and **Restore backup** buttons.
One `.sm809backup` file contains every profile, its assignments and DPI/lighting/
performance settings, wheel actions, macros, auto-switch rules and app
preferences, including overlay settings. Existing autosave remains in place.
Windows-wide scroll settings and Windows startup registration are not included.

The backup is versioned JSON data, not an executable or archive. Restore validates
its format, references, action bytes, settings types and bounds before writing.
It shows profile/macro counts and asks before replacing current settings. If it
contains app-launch assignments, that is noted explicitly in the confirmation.
Backups are limited to 8 MB, 500 profiles and 1,000 macros.

Before a restore, a timestamped recovery backup is written to `config/backups`.
Each settings file is replaced via a fully written, flushed temporary file. A
failure during the second replacement rolls back the first; the recovery backup
also remains available. Two file replacements are not one crash-atomic database
transaction: after sudden power loss during restore, use the recovery backup if
needed. Successful restore refreshes the app's stores, panels and preferences
and applies the restored active mouse profile without requiring a restart.

Restore pauses auto-switching while its dialogs are open and refuses to replace
settings while mouse commands are still applying. Export and restore report
write failures; normal profile/macro autosaves also now use atomic replacement.

## Undo

The sidebar's **Undo setting change** button restores up to 20 previous setting
snapshots per profile during the current session. Switching profiles does not
mix their histories. Restoring a backup clears undo history.

Undo covers button mappings, wheel mappings, DPI, lighting, polling, lift-off,
power and sensor edits. It does not undo macro editing, profile creation/deletion,
renaming, sorting, auto-switch rules, factory resets or app preference changes.
Factory reset clears that profile's undo history. The distinction
is stated in the button tooltip.

While implementing undo, an existing persistence bug was found: editing an
auto-selected profile saved its settings into the manual base profile. Edits and
undo now target the profile displayed/applied by the app, leaving the manual
fallback profile intact.

## About and diagnostics

The About page credits the original project by lacno29 and credits enhancements,
feature direction and hardware testing to **Robin Luxton at MutzNutz Media and
Design**. It includes repository links, version, changes, a short AI-assisted
development note and the actual unresolved upstream licensing position. It does
not claim MutzNutz Media and Design is an incorporated company or claim exclusive
ownership of the original code.

Diagnostics are read-only and refreshed on request. They show detected mouse
VID/PIDs, transport, collection counts, configuration availability, runtime
versions, recent communication errors and recorded autosave failures. Copy report
is an explicit user action. Reports omit profile bindings, macro contents,
serial numbers and raw device paths. Recognisable HID paths and the user's home
directory are redacted from errors. Reports are not sent anywhere.

## Validation

- Existing protocol checks: 49 passed.
- Existing wheel regression tests: 6 passed.
- Existing feedback regression tests: 7 passed.
- Transport isolation tests: 9 passed.
- New backup/persistence tests: 6 passed, including complete round trip,
  malformed/oversized data rejection and second-file failure rollback.
- New GUI integration tests: 8 passed, covering undo, auto-profile isolation,
  export and restore dialogs, cancellation, UI/store refresh and diagnostic
  privacy/credits.
- Complete headless GUI suite: ALL GOOD, including existing macro and
  auto-switch integration checks.
- About and Profiles layouts visually reviewed using isolated temporary stores.
- Packaged startup passed using both offscreen and native Windows Qt, with HID
  disabled and temporary settings.

Automated tests disable HID access and never change the user's real config or
Windows scroll settings. No normal hardware-writing app launch is performed by
the tests. Actual v5 use still needs Robin's hardware check.

Build: `python tools/build_test.py`.
Output: `dist/control-centre-v5/SM809Pro.exe`.
