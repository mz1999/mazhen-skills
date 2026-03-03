# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-03-02

### Added
- Initial release of searxng-auth skill
- HTTP Basic Auth support for protected SearXNG instances
- Support for multiple search categories (general, images, videos, news, map, music, files, it, science)
- Rich table output format with formatted search results
- JSON output format for programmatic use
- Language filter support
- Time range filter support (day, week, month, year)
- SSL verification enabled by default for secure public deployments
- Comprehensive error handling for authentication and connection issues
- Environment variable configuration for URL, username, and password
- No default URL - requires explicit configuration (security by design)

### Security
- Credentials always read from environment variables
- SSL certificate verification enabled
- Passwords never logged or displayed
- Clear error messages for authentication failures
