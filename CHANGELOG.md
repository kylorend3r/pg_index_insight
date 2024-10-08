# Changelog

## [0.0.7]
### Added
- Implemented pre-running checks to ensure that the PostgreSQL version is greater than 12.
- Added validation to check if the user provides a system database (e.g., `postgres` or `template`).
- Introduced warnings when a user provides superuser credentials to enhance security awareness.
