# GoPoint Release Checklist

This document exists to prevent repeat mistakes in versioning, auto-update, and release communication.

Follow every item for every public release.

## 1. Versioning

- Update `APP_VERSION` in `GoPoint.py`.
- Update any build script version fields, including `build_nuitka.bat`.
- Add changelog entries for all supported languages already maintained in the app.
- Update the README top section for the new version when the release is user-facing.

## 2. Build Rules

- GitHub release asset name must be `GoPoint.exe`.
- Local build output must also include `GoPoint_vX.Y.Z.exe`.
- Do not change the updater asset naming convention unless the updater logic is changed and re-verified.

## 3. Auto-Update Safety Rules

- Never decide auto-update status from source-mode execution alone.
- Any change to updater logic, packaged build detection, build toolchain, or EXE replacement flow must be validated against the packaged EXE path.
- If the currently public version cannot auto-update to the next version, treat it as a release-blocking communication issue.

## 4. Minimum Verification Before Release

- Run `python -m py_compile GoPoint.py`.
- Run the packaged build, currently `cmd /c build_nuitka.bat`.
- Confirm `dist/GoPoint.exe` exists.
- Confirm `dist/GoPoint_vX.Y.Z.exe` exists.
- Confirm the updater target asset name is still `GoPoint.exe`.
- If the release includes updater changes, verify the packaged build no longer falls into the `Auto-update is only supported in the packaged .exe build.` error path.

## 5. Communication Rules

If any previously shared version needs a one-time manual install:

- Put the notice at the top of the GitHub release notes.
- Put the notice near the top of `README.md`.
- When users ask for a thread notice, explicitly mention:
  - which version is affected
  - that auto-update does not work for that version
  - that one manual install is required
  - which fixed version to install

Make the notice visually prominent. Use strong wording such as `IMPORTANT` or `EMERGENCY NOTICE`.

## 6. Release Procedure

1. Verify the working tree state with `git status --short --branch`.
2. Commit the release changes.
3. Push the release commit to `main`.
4. Create the GitHub release with:
   - asset `dist/GoPoint.exe`
   - any supporting image assets referenced in the release notes
5. Verify the release page, uploaded assets, and final note text using `gh release view`.

## 7. Final Sanity Check

Before telling the user that a release is done, confirm all of the following:

- the release tag exists
- the release URL is reachable
- the correct assets are attached
- the release notes contain any required warning text
- the local repo is in the expected state

If any item is missing, do not say the release is complete.
