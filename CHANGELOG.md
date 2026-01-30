# Changelog - MyRVM-Edge

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
