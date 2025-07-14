"""Invoke tasks for code quality and formatting."""

from invoke.context import Context
from invoke.tasks import task


@task
def lint(ctx: Context, fix: bool = False) -> None:
    """Run ruff linting with optional auto-fix.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    fix : bool, optional
        Whether to auto-fix issues, by default False
    """
    cmd = "ruff check ."
    if fix:
        cmd += " --fix"
    ctx.run(cmd)


@task
def format(ctx: Context, check: bool = False) -> None:
    """Run ruff formatting with optional check-only mode.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    check : bool, optional
        Whether to check formatting without applying changes, by default False
    """
    cmd = "ruff format ."
    if check:
        cmd += " --check"
    ctx.run(cmd)


@task
def typecheck(ctx: Context) -> None:
    """Run pyright type checking.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    ctx.run("pyright")


@task
def check(ctx: Context) -> None:
    """Run all code quality checks (lint, format check, typecheck).

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    print("🔍 Running linting...")
    lint(ctx, fix=False)

    print("📐 Checking formatting...")
    format(ctx, check=True)

    print("🔬 Type checking...")
    typecheck(ctx)

    print("✅ All checks completed!")


@task
def check_fix(ctx: Context) -> None:
    """Auto-fix linting issues and format code.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    print("🔧 Fixing linting issues...")
    lint(ctx, fix=True)

    print("📝 Formatting code...")
    format(ctx, check=False)

    print("🔬 Type checking...")
    typecheck(ctx)

    print("✅ All fixes applied!")


@task
def ai_developer_quality(ctx: Context) -> None:
    """Run comprehensive quality checks for AI agents.

    AI Agents should use this task for quality checking.
    After running this task, AI agents will need to refresh
    their context as these commands can change files safely.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    check_fix(ctx)


@task
def clean(ctx: Context) -> None:
    """Clean up build artifacts and cache files.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    ctx.run("find . -type d -name '__pycache__' -exec rm -rf {} +", warn=True)
    ctx.run("find . -type f -name '*.pyc' -delete", warn=True)
    ctx.run("rm -rf .pytest_cache", warn=True)
    ctx.run("rm -rf .ruff_cache", warn=True)
    ctx.run("rm -f bmd_sg/decklink/libdecklink.dylib")
    print("🧹 Cleaned up cache files!")


@task
def test(ctx: Context) -> None:
    """Run tests.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    ctx.run("python -m pytest tests/")


@task(pre=[clean])
def build(ctx: Context) -> None:
    """Build the C++ library and Python package.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    print("🔨 Building C++ library...")
    ctx.run("cd cpp && make clean && make && cd ..")

    print("📦 Building Python package...")
    ctx.run("uv build")

    print("✅ Build completed!")


@task
def docs(ctx: Context, clean_build: bool = False) -> None:
    """Build Sphinx documentation.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    clean_build : bool, optional
        Whether to clean build directory first, by default False
    """
    if clean_build:
        print("🧹 Cleaning documentation build directory...")
        ctx.run("rm -rf docs/build/*", warn=True)

    print("📚 Building Sphinx documentation...")
    ctx.run("uv run sphinx-build -b html docs/source docs/build/html")

    print("✅ Documentation built successfully!")
    print("📖 Open docs/build/html/index.html to view documentation")


@task
def serve_docs(ctx: Context, port: int = 8000) -> None:
    """Serve documentation locally with HTTP server.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    port : int, optional
        Port number for the web server, by default 8000
    """
    import os

    docs_path = "docs/build/html"

    # Check if documentation exists
    if not os.path.exists(docs_path):
        print("📚 Documentation not found. Building first...")
        docs(ctx)

    print(f"🌐 Starting web server on port {port}...")
    print(f"📖 Open http://localhost:{port} in your browser")
    print("💡 Press Ctrl+C to stop the server")

    try:
        ctx.run(f"cd {docs_path} && python -m http.server {port}")
    except KeyboardInterrupt:
        print("\n🛑 Documentation server stopped.")


@task
def dev(ctx: Context) -> None:
    """Quick development check: fix issues and run tests.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    check_fix(ctx)
    test(ctx)
