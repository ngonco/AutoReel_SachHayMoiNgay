# Agent instructions

Read `system_map.md` before modifying this project. It contains the architecture, media rules, APIs, build workflow and known limitations.

After every completed modification session, run relevant checks, update the documents, commit the intended source changes and push the backup to `https://github.com/ngonco/AutoReel_SachHayMoiNgay` (`main`). Verify remote HEAD matches local HEAD. If push fails, preserve the local commit and report that the remote backup is incomplete. Never force-push.

Do not commit source videos, generated media, cache, logs, EXE/DLL files, Microsoft fonts, personal settings or credentials. Respect `.gitignore`. Preserve user media and settings. Do not shut down the computer during tests.

Use the server plan as the single source of truth for scene text, timing, video selection, speed and layout. Preview and export must use the same renderer. Bump `PLAN_VERSION` when changing render/layout/planning behavior.
