# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project Homepage

Check metadata fields in `pyproject.toml` for the project home page and author
information.

## Project Overview

This project is a cross-platform BMD (Blackmagic Design) signal generator that
outputs test patterns via DeckLink devices. For detailed architecture and component
information, see `.memories/PROJECT_SUMMARY.md`.

## Common Commands

**Build:** `uv run invoke build` - Builds C++ library and Python package

**Quality:** `uv run invoke ai-developer-quality` (AI agents), `check` (all), `fix` (auto-fix), `dev` (fix+test)

**Testing:** `uv run invoke test` or `uv run pytest -v --tb-no <files>`

**CLI:** `uv run bmd-signal-gen [--mock-device] <command>`

**Tools:** `uv run invoke lint|format|typecheck|clean`, `uv run pre-commit install`

## Development Guidelines

### Critical Standards
- **DRY Principle**: Eliminate duplicate logic, especially pixel format switch/case statements
- **Centralized Logic**: Use helpers/utilities rather than repeating validation/conversion code
- **Refactor Immediately**: Don't defer deduplication - fix patterns when found

### Documentation Standards
- **All public code** must use **NumPy-style docstrings** with Parameters, Returns, Raises, Examples
- **Complete documentation** required for modules, classes, functions, constants
- **Practical examples** and cross-references in docstrings

### HDR & Device Management
- **HDR default**: MaxCLL=10,000 nits (project-specific, not industry standard)
- **Pixel format preference**: 12-bit RGB → 10-bit RGB → 10-bit YUV → 8-bit RGB
- **Device management**: Global state in API server, enumeration at init

## Testing

Use `uv run invoke test` to run the test suite. See the Common Commands section above for more testing options.

## Common Issues

- **Library Loading**: Ensure `libdecklink.dylib` is built and in correct
  location
- **Device Access**: Requires BMD Desktop Video drivers and proper device
  connection
- **Pixel Format**: Some formats may not be supported by all devices
- **HDR Metadata**: Complete metadata structure required for proper HDR output

## Troubleshooting

**Build fails**: Ensure DeckLink SDK headers in `cpp/include/DeckLinkAPI/`, clang++ with C++20, Desktop Video drivers

**Library not found**: Run `uv run invoke build`, check `bmd_sg/decklink/libdecklink.dylib` exists

**No devices found**: Use `--mock-device` for testing, check connections/drivers, try `device-details` command

**Color validation errors**: Check bit depth ranges (8-bit: 0-255, 12-bit: 0-4095), use integers not floats

**Pre-commit/tests fail**: Run `uv run invoke fix` or `ai-developer-quality`, use `--mock-device` for testing

**Slow patterns**: Use NumPy operations, `np.ascontiguousarray()` for buffers, pre-allocate arrays

## Dependencies

See DEVELOPERS.md for complete setup instructions including prerequisites and
SDK installation.

## Claude Code Guidelines

### Refactoring Workflow
- Use edit/multi-edit tools for refactor suggestions (not code snippets)
- Describe suggestions briefly first, wait for confirmation
- Break API for improvements if needed (make corrections throughout codebase)

### Code Quality
- Add return types and type annotations to all functions
- Don't return `Optional` types - raise errors instead of returning None
- Use specific exception types with detailed error messages and context

### Error Handling by Module
- **CLI**: `typer.echo(f"Error: {e}", err=True)` and `typer.Exit(1)`
- **DeckLink**: Translate SDK errors to specific exceptions (`DeviceNotFoundError`, `PixelFormatError`)
- **Pattern Generation**: Use `ColorRangeError` for color validation failures
- **API**: Return standardized `ErrorResponse` format with error details

### Development Environment
- **Always use `uv run python` instead of invoking python directly**
- **Always use `uv run pre-commit` instead of invoking pre-commit directly**
- Change to root directory for `uv run` tasks, return to previous after if needed

### Testing: Hardware vs Mock Device
- **Hardware (preferred)**: Test with real DeckLink device when available
- **Mock device**: Use `--mock-device` flag for development without hardware
- **Mock capabilities**: Simulates all operations, validates parameters, provides realistic timing
- **Workflow**: Start with mock device testing, use hardware for final validation
- **CLI methods**: Primary: `uv run bmd-signal-gen`, Alternative: `uv run python -m bmd_sg.cli.main`

### Development Tools
- **Always try `uv run invoke ai-developer-quality` before other quality tools**
- Re-read files after quality checks (some modify files)
- Request permission to bypass checks for unrelated code (remove bypass after project)

### Module Maintenance
- Keep `__all__` declarations up to date by searching for public member usages
- Ensure usage and documentation are current with latest changes

### Reference Files
- Read `DEVELOPERS.md` for setup and development standards
- Check `.memories/PROJECT_SUMMARY.md` for architecture details  
- Search `.memories/DesktopVideoSDKManual.md` for BMD SDK documentation
- Use `cpp/Blackmagic\ DeckLink\ SDK\ 14.4/Mac/Samples/SignalGenHDR` as known-good example code