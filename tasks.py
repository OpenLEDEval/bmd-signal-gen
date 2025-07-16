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

    print("📖 Spell checking...")
    spellcheck(ctx)

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
    print("📝 Formatting code...")
    format(ctx, check=False)

    print("🔧 Fixing linting issues...")
    lint(ctx, fix=True)

    print("🔬 Type checking...")
    typecheck(ctx)

    print("📖 Spell checking...")
    spellcheck(ctx)


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
def spellcheck(ctx: Context) -> None:
    """Run spell checking using cspell.

    Checks for spelling errors in Python, C++, and documentation files.
    Provides helpful installation and configuration guidance if needed.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    import shutil

    print("📝 Running spell check...")

    # Check if npx is available
    if not shutil.which("npx"):
        print("❌ npx not found!")
        print("📦 Please install Node.js to get npx:")
        print("   • macOS: brew install node")
        print("   • Other: https://nodejs.org/")
        return

    # Try to run cspell, handle if not installed
    try:
        result = ctx.run(
            'npx cspell "bmd_sg/**/*" "cpp/**/*" "docs/**/*" "tests/**/*" "examples/**/*" "*.md" --no-progress',
            warn=True,
        )

        if result and result.ok:
            print("✅ No spelling errors found!")
        else:
            print("⚠️  Spelling errors detected!")
            print("🔧 To fix these issues:")
            print("   1. Correct any genuine spelling mistakes")
            print("   2. Add legitimate technical terms to cspell.json")
            print("   3. Technical terms should go in the 'words' array")
            print("📖 Edit cspell.json to add new technical vocabulary")

    except Exception as e:
        if "command not found" in str(e).lower() or "not found" in str(e).lower():
            print("📦 cspell not found. For faster execution, install globally:")
            print("   npm install -g cspell")
            print("🔄 Trying to install and run cspell temporarily...")
            try:
                ctx.run(
                    'npx cspell "bmd_sg/**/*" "cpp/**/*" "docs/**/*" "tests/**/*" "examples/**/*" "*.md" --no-progress',
                    warn=True,
                )
            except Exception:
                print(
                    "❌ Failed to run cspell. Please check your Node.js installation."
                )
        else:
            print(f"❌ Error running cspell: {e}")


@task
def dev(ctx: Context) -> None:
    """Quick development check: fix issues and run tests.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    check_fix(ctx)
    typecheck(ctx)
    spellcheck(ctx)
    test(ctx)
