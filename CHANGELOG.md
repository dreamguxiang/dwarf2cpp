# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Generate an additional grouped header copy with virtual functions, data members, and static members collected together.

### Changed
- Improve generated header spacing around access labels and top-level declarations.
- Preserve nested type declarations that do not have their own DWARF source line.

## [0.1.0] - 2026-05-16

### Added
- Initial release
- Generate C++ headers from DWARF debug information
- Support for Windows (MSVC), Linux (GCC), and macOS (Apple Clang)
- pybind11 bindings for LLVM DWARF DebugInfo
- Jinja2 template-based header generation
