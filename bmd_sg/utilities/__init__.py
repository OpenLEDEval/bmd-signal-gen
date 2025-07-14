"""
Utility functions for BMD signal generation.

This module provides helper functions and context managers for working with
the BMD signal generator, including output suppression and other utilities.
"""

import contextlib
import os
from collections.abc import Generator


@contextlib.contextmanager
def suppress_cpp_output() -> Generator[None]:
    """
    Context manager to suppress C++ library output by redirecting file descriptors.

    This context manager temporarily redirects stdout and stderr to /dev/null
    to suppress output from the underlying C++ DeckLink library, which can be
    verbose during frame operations. File descriptors are safely restored
    when the context exits.

    Yields
    ------
    None
        Context manager yields None during execution.

    Examples
    --------
    Suppress output during DeckLink operations:

    >>> with suppress_cpp_output():
    ...     decklink.display_frame(frame_data)  # C++ output suppressed

    Notes
    -----
    This function uses low-level file descriptor operations (os.dup, os.dup2)
    to redirect output streams. File descriptors are properly restored even
    if an exception occurs within the context.
    """
    with open(os.devnull, "w") as devnull:
        # Save original file descriptors
        old_stdout = os.dup(1)
        old_stderr = os.dup(2)

        # Redirect stdout and stderr to /dev/null
        os.dup2(devnull.fileno(), 1)
        os.dup2(devnull.fileno(), 2)

        try:
            yield
        finally:
            # Restore original file descriptors
            os.dup2(old_stdout, 1)
            os.dup2(old_stderr, 2)
            os.close(old_stdout)
            os.close(old_stderr)


__all__ = ["suppress_cpp_output"]
