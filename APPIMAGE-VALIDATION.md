# Linux build validation

Development environment: Zorin OS 18.1 / Ubuntu 24.04, x86_64, Python 3.12, PySide6 6.12.0, PyAV 19.0.2 and PyInstaller 6.22.3.

The standalone bundle was launched without the development virtual environment. Test media was loaded, and the bundled forced-subtitle helper was checked independently. Multi-process handoff and stale-lock recovery were exercised. Other focused checks covered subtitle text/flags, OSD and notification timing, seek behavior, fullscreen geometry, resize hit areas, menu presentation and startup rendering.

These are development checks, not certification across all Linux distributions or graphics drivers. Windows builds and DRM playback are not validated. The AppImage is generated under `dist/` and is not stored in Git.
