# Changelog - MyRVM-Edge

## [1.2.0] - 2026-01-31
### Added
- Virtual Environment (venv) support in `setup_service.sh` for dependency isolation.
- Remote command handling for `GIT_PULL` (update) and `RESTART` from Dashboard.
- Automatic version reporting in Heartbeat from `VERSION` file.

### Changed
- Improved `setup_service.sh` to automate venv creation and requirement installation.
- Refined `main.py` loop to process remote commands every heartbeat.

## [1.1.0] - 2026-01-30
### Added
- Systemd service configuration for auto-start.
- Auto-updater mechanism (Systemd Timer) for routine `git pull`.
- Heartbeat version reporting to Server.
- Manual update command handling via Heartbeat response.
- `scripts/setup_service.sh` for automated deployment.
- `scripts/remove_service.sh` for service cleanup.

### Changed
- Improved GPIO resilience in hardware drivers.
- Updated `api_client.py` to support versioning and command processing.
