# Agent instructions

Read `system_map.md` before modifying this project. It contains the architecture, media rules, APIs, build workflow and known limitations.

Whenever application code changes (Python, UI HTML/CSS/JavaScript, dependencies, or packaging), rebuild the Windows `.exe` from the final code and verify that executable before handing off. This is mandatory after every completed code modification session, even for a small fix. Run `python -X utf8 build_onefile.py`, verify startup through the launcher and exercise the changed behavior in the packaged app. Update the launcher if a new executable filename is needed; preserve running user sessions. If build or verification fails, report it as unfinished instead of presenting an old executable as updated. Documentation-only edits do not require rebuilding the executable.

After every completed modification session, run relevant checks, update the documents, commit the intended source changes and push the backup to `https://github.com/ngonco/AutoReel_SachHayMoiNgay` (`main`). Verify remote HEAD matches local HEAD. If push fails, preserve the local commit and report that the remote backup is incomplete. Never force-push.

Do not commit source videos, generated media, cache, logs, EXE/DLL files, Microsoft fonts, personal settings or credentials. Respect `.gitignore`. Preserve user media and settings. Do not shut down the computer during tests.

Use the server plan as the single source of truth for scene text, timing, video selection, speed and layout. Preview and export must use the same renderer. Bump `PLAN_VERSION` when changing render/layout/planning behavior.

Preserve `session_state.json` (autosaved draft/settings) and `footage_usage.json` (content-based footage turns) across upgrades. Production exports must go through JobManager or the tracked render wrapper with footage reservation/commit; low-level `render_plan` alone is for preview/isolated verification. Preview must not consume footage turns. Never reset real footage history to work around a conflict; use isolated `--workspace` profiles for mutation tests.
