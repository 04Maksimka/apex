# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fixed the Messier objects guessing game
### Added
- images for each object in Messier objects guessing game

---

## [0.2.2] - 2026-02-26

### Fixed
- Restored the website to working state
- Minor cosmetic improvements to the documentation and website

### Changed
- Trivia game facts

---

## [0.2.1] - 2025-02-25

### Added
- Basic CLI via `click`: `astrageek` entry point
- Project documentation via Sphinx, deployed automatically with GitHub Actions
- Interactive constellations and Messier objects guessing game

### Changed
- Migrated the website and game to a dedicated server
- Internal docstrings reformatted and brought to reStructuredText (reST) style

### Fixed
- New visual style for star maps

---

## [0.2.0] - 2025-01-08

### Added
- Pinhole (gnomonic) projection mode for small sky areas
- Constellation outlines for all 88 IAU constellations
- Website with star map generator

---

## [0.1.0] - 2025-12-01

### Added
- Stereographic projection of the full sky
- Coordinate grids: horizontal and equatorial
- Great circles: ecliptic, celestial equator, and galactic equator
- Cardinal directions and zenith point
- Planet positions (inner and outer planets)
- PDF output support via matplotlib
