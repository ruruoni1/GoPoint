# Local Update Testing

This repository can test auto-update without GitHub.

## Default lookup order

1. `GOPOINT_UPDATE_MANIFEST` environment variable
2. `update-test/update.json` next to the running app
3. GitHub latest release API

For packaged EXE testing, the practical location is:

- `dist/update-test/update.json`
- `dist/update-test/GoPoint.exe`

## Quick setup

Stage the currently built EXE into the local test folder:

```bat
stage_local_update.bat 1.0.16
```

Or stage a specific file:

```bat
stage_local_update.bat 1.0.16 "D:\path\to\GoPoint.exe"
```

## Manifest format

```json
{
  "version": "1.0.16",
  "url": "GoPoint.exe"
}
```

Supported `url` values:

- relative path
- absolute path
- `file:///...`
- `https://...`

## Recommended test flow

1. Build the new version.
2. Run `stage_local_update.bat NEW_VERSION`.
3. Launch an older packaged build from `dist`.
4. Click update check.
5. Confirm the app updates from `dist/update-test/GoPoint.exe`.

## Current local test target

You can immediately test:

- current app in `dist/update-test/GoPoint.exe`
- from `dist/GoPoint_v1.0.15.exe`
- to local manifest version `1.0.16`
