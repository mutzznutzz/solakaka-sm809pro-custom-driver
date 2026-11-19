# Release permissions and feature shortlist

## Licence check, 19 November 2026

Both current repository trees were inspected, and GitHub's repository metadata reports no declared licence. Neither inspected tree contains a LICENSE or COPYING file. No licence grant was found in the Pro README. The other project's README currently has a large feature reference; do not treat its public visibility as permission to copy its implementation.

- Pro app: https://github.com/lacno29/solakaka-sm809pro-custom-driver
- Wired-only app: https://github.com/Jayden-Dollaga/solakaka-sm809-wired-custom-driver

GitHub says users can view and fork public repositories on GitHub, but a missing licence does not grant general rights to distribute modified copies. Credit alone doesn't supply that permission. Check again immediately before release; ask each author for a suitable licence/permission covering the material you want to redistribute. Do not put your own MIT licence over someone else's unlicensed code.

GitHub's explanation: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository

Suggested message to the Pro author (draft only):

> Hi, I'm the person who reported issue #2 about the scroll wheel. I'd like to maintain a fork with the fix and possibly add a few features, while crediting your work. I couldn't find a licence in the repository. Would you be happy to add an open-source licence, or clarify what permission you give for modified source and executable releases?

If we later reuse code from the wired project, ask its author separately. General feature ideas can be implemented independently; don't copy its source or assets without resolving permission. The wired project's Holtek protocol, 64-slot tables and device-only features do not apply directly to Robin's Elan Pro.

Before publishing: retain upstream authorship/history, document changes, satisfy the eventual licence's notice/source requirements, inspect dependency licences and the chosen Qt/PySide6 distribution obligations, and exclude vendor installer/DLLs/artwork/captures containing unrelated traffic. Review any vendor-derived material separately rather than assuming the app authors can license it.

## What stays

The clean existing interface and click-through DPI/profile overlay stay. The overlay is a display fed by controller signals, not the writer that damaged the wheel mappings. It does not need replacing. Existing per-app matching/debounce and base-profile fallback stay too.

## Features worth adding

| Priority | Feature | Evidence / source of idea | Approach for this Pro project |
| --- | --- | --- | --- |
| First | Reliable wheel rotation after every profile write | Official restored profile and 18-slot writer | Implemented in this branch; capture/hardware verification pending |
| First | Correct wired 809E detection | Windows USB inventory and upstream classification bug | Implemented; label isn't proof of successful writes |
| Next | Manual Apply mode and changed-settings preview | Wired Studio's documented manual/automatic apply modes | Stage edits and show what will be sent; preserve existing auto-switch semantics |
| Next | Profile backup before writes; export/import and migration | Official Import/Export and wired Studio profile management | Build on existing JSON and .psf import; retain the full profile and macro libraries |
| Next | Diagnostic log with command names, sequence, result and active profile | Wired Studio diagnostics | Explicitly distinguish a clean USB write from confirmed hardware acceptance; no false success ACK claims |
| Next | Wheel direction/binding settings, including restore normal rotation | Official Wheel Up/Down actions | Store two extra wheel fields separately from 16 physical buttons; verify alternative actions by capture |
| Later | Windows scroll lines/page mode, pointer precision and double-click speed | Installed official language strings and profile fields | Use documented Windows APIs and label these as system-wide settings, not mouse firmware settings; avoid silently changing them on every auto-switch |
| Later | Profile search/duplicate/reorder and batch import/export | Wired Studio's documented feature set | Independently implement reusable UI ideas after fixing the core write path |
| Later | Foreground app picker and better elevated-game matching | Wired Studio's documented app detection | Test normal/elevated apps; don't make every launch require admin just for convenience |
| Later | More overlay controls and explicit apply status | Both projects' overlay designs | Keep current styling; add monitor/position controls only where missing and show errors rather than assuming device acceptance |

The installed manufacturer's labels also mention tilt, pairing and additional action types. A label alone doesn't establish that this mouse has a physical tilt wheel or that a particular command is supported. Treat those as research candidates, not promised features. Recoil controls, extra hardware profile banks and Holtek-specific lighting from the wired-only model are not portable features to copy into the Pro backend.

## Current validation boundary

The fix is a source patch with passing offline tests. No live traffic has yet been captured for this project and no patched binary has been run on Robin's mouse. Full GUI tests require PySide6 and were not run in the analysis environment. Robin has created the GitHub fork at https://github.com/mutzznutzz/solakaka-sm809pro-custom-driver; no executable release has been created. An official-packet capture is available as a targeted additional verification step, rather than a reconstruction of the whole application. Complete an explicit hardware test session before describing a release as verified.
