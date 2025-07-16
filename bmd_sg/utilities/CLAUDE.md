# Utilities Module Development Guide

## Primary Purpose

System-level operations and C++ library integration support.

## Core Utility: Output Suppression

```python
@contextlib.contextmanager
def suppress_cpp_output() -> Generator[None]:
    """Suppress C++ DeckLink library output by redirecting file descriptors."""
    with open(os.devnull, "w") as devnull:
        old_stdout, old_stderr = os.dup(1), os.dup(2)
        try:
            os.dup2(devnull.fileno(), 1)
            os.dup2(devnull.fileno(), 2)
            yield
        finally:
            os.dup2(old_stdout, 1)
            os.dup2(old_stderr, 2)
            os.close(old_stdout)
            os.close(old_stderr)
```

## Context Manager Pattern

Standard template for robust resource management:
```python
@contextlib.contextmanager
def robust_context_manager() -> Generator[SomeResource]:
    resource = None
    try:
        resource = acquire_resource()
        yield resource
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        if resource is not None:
            release_resource(resource)
```

## Cross-Platform Support

```python
def get_null_device() -> str:
    return "NUL" if platform.system() == "Windows" else "/dev/null"
```

## Key Guidelines

- Keep utilities lightweight and focused
- Use NumPy docstring format for all functions
- Maintain `__all__` list for clean public API
- Design for minimal overhead when not in use
- Ensure cross-platform compatibility

This module provides foundational support - ensure utilities are robust and well-tested.