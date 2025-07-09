# Contributing to bmd-signal-gen

## DRY Principle (Don't Repeat Yourself) — TOP PRIORITY
- All contributors (human or AI) must avoid duplicate logic, especially repeated switch/case or if/else statements for the same variable or type.
- If a function must branch on a type/format (e.g., pixel format), all related logic (validation, clamping, packing, etc.) must be handled in a single switch or if/else block.
- PRs that violate DRY will not be accepted.
- This is the top development priority for this project.
- If you see a pattern of repeated logic, refactor immediately, not later. Use helpers or tables to centralize logic.
- This rule applies to all code, including C++, Python, and build/config scripts.

## Other Coding Standards
- Maintain encapsulation: keep implementation details private, expose only clean public APIs.
- Prefer clear, maintainable, and testable code.
- Minimize sycophancy in code comments and commit messages.

## How to Contribute
- Fork the repo and create your branch from `main`.
- Ensure your code passes all tests and linter checks.
- Follow the DRY and coding standards above.
- Submit a pull request with a clear description of your changes. 