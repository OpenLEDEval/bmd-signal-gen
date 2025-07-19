# Utilities Module Development Guide

**Primary Purpose**: System-level operations and C++ library integration support.

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

## Guidelines

**Context Manager Pattern**: Standard template with try/finally for robust resource management  
**Cross-Platform**: Use platform-specific paths (`"NUL"` vs `"/dev/null"`)  
**Design**: Lightweight, focused utilities with NumPy docstrings, maintain `__all__`, minimal overhead, cross-platform compatibility

Foundational support module - ensure utilities are robust and well-tested.