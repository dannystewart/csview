# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to [Semantic Versioning].

## [Unreleased]

## [0.1.3] (2025-04-08)

## Changed

- Renames `CSVViewer` class to `CSView` to better align with the project name.
- Updates type ignore comments to use more specific `[attr-defined]` syntax instead of blanket ignores.

## [0.1.2] (2025-04-07)

### Fixes

- Updates `polykit` dependency to 0.8.0 to fix `polykit_setup` import.

## [0.1.1] (2025-04-07)

### Added

- Adds script entry point in `pyproject.toml`, making the package executable via the `csview` command after installation.
- Adds comprehensive project documentation including README with features, installation instructions, and usage examples.
- Adds GitHub Actions workflows for automatic documentation publishing and PyPI releases.

### Changed

- Renames source files from `csv_viewer.py` to `csview.py` to maintain naming convention.
- Improves README formatting.
- Updates dependencies.

### Fixed

- Fixes CSS file path resolution by correctly converting the file location to a `Path` object before finding its parent.

### Internal

- Adds MIT license file, officially making the project open source (so you can legally steal my code now! 🎉).
- Expands `.gitignore` with comprehensive Python-specific patterns.

## [0.1.0] (2025-04-07)

Initial release. Changes name from `csv-viewer` to `csview`.

<!-- Links -->
[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[unreleased]: https://github.com/dannystewart/csview/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/dannystewart/csview/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/dannystewart/csview/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/dannystewart/csv-viewer/releases/tag/v0.1.1
[0.1.0]: https://github.com/dannystewart/csview/releases/tag/v0.1.0
