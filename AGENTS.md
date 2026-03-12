# GoPoint Agent Rules

These instructions are mandatory for any agent working in this repository.

## Required Release Checklist

Before changing any of the following, read `docs/release-checklist.md` and follow it exactly:

- app version
- build scripts
- auto-update logic
- GitHub release notes
- GitHub release assets
- README update notices

Do not skip the checklist because a change looks small.

## Non-Negotiable Rules

1. Do not claim that auto-update works unless the packaged EXE path was verified. Source-mode checks are not enough.
2. If a previously released version cannot auto-update to the new version, add a prominent manual-install notice to:
   - README
   - GitHub release notes
   - any user-facing thread or announcement text requested in the task
3. GitHub release assets must keep the stable updater filename `GoPoint.exe`.
4. Local builds must also keep the versioned file `GoPoint_vX.Y.Z.exe`.
5. Do not publish a release until the release checklist items are completed and re-checked.
6. Do not remove or weaken these instructions without explicit user approval.
