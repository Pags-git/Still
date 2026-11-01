# Linux build validation

Development environment: Zorin OS 18.1 / Ubuntu 24.04, x86_64, Python 3.12, PySide6 6.12.0, PyAV 19.0.2 and PyInstaller 6.22.3.

The standalone bundle was launched without the development virtual environment. Test media was loaded, and the bundled forced-subtitle helper was checked independently. Multi-process handoff and stale-lock recovery were exercised. Other focused checks covered subtitle text/flags, OSD and notification timing, seek behavior, fullscreen geometry, resize hit areas, menu presentation and startup rendering.

These are development checks, not certification across all Linux distributions or graphics drivers. DRM playback is not supported. The AppImage is generated under `dist/` and is not stored in Git.

## Windows release status

Windows **v0.1.4** is available alongside the Linux AppImage in the [v0.1.4 release](https://github.com/Pags-git/Still/releases/tag/v0.1.4), as `Still.Installer.exe` with `Still.Installer.exe.sha256`.

The installer was supplied by Pags. Publication checks verified the uploaded file's size and SHA-256 hash against the supplied binary; the v0.1.4 installer was not executed on Windows during this workflow. Pags previously reported successful manual testing of the earlier Windows build. These Linux development checks should not be interpreted as Windows v0.1.4 runtime test results.
