"""Invoke tasks for code quality and formatting."""

from invoke import task


@task
def lint(ctx, fix=False):
    """Run ruff linting with optional auto-fix."""
    cmd = "ruff check ."
    if fix:
        cmd += " --fix"
    ctx.run(cmd)


@task
def format(ctx, check=False):
    """Run ruff formatting with optional check-only mode."""
    cmd = "ruff format ."
    if check:
        cmd += " --check"
    ctx.run(cmd)


@task
def typecheck(ctx):
    """Run pyright type checking."""
    ctx.run("pyright")


@task
def commit_check(ctx):
    format(ctx, check=True)


@task
def check(ctx):
    """Run all code quality checks (lint, format check, typecheck)."""
    print("🔍 Running linting...")
    lint(ctx, fix=False)

    print("📐 Checking formatting...")
    format(ctx, check=True)

    print("🔬 Type checking...")
    typecheck(ctx)

    print("✅ All checks completed!")


@task
def check_fix(ctx):
    """Auto-fix linting issues and format code."""
    print("🔧 Fixing linting issues...")
    lint(ctx, fix=True)

    print("📝 Formatting code...")
    format(ctx, check=False)

    print("🔬 Type checking...")
    typecheck(ctx)

    print("✅ All fixes applied!")


@task
def ai_developer_quality(ctx):
    # AI Agents should use this task for quality checking.

    # After running task ai-developer-quality, ai agents will need to refresh
    # their context as these commands can change files safely.
    check_fix(ctx)
    typecheck(ctx)


@task
def clean(ctx):
    """Clean up build artifacts and cache files."""
    ctx.run("find . -type d -name '__pycache__' -exec rm -rf {} +", warn=True)
    ctx.run("find . -type f -name '*.pyc' -delete", warn=True)
    ctx.run("rm -rf .pytest_cache", warn=True)
    ctx.run("rm -rf .ruff_cache", warn=True)
    ctx.run("rm -f bmd_sg/decklink/libdecklink.dylib")
    print("🧹 Cleaned up cache files!")


@task
def test(ctx):
    """Run tests."""
    ctx.run("python -m pytest tests/")


@task(pre=[clean])
def build(ctx):
    """Build the C++ library and Python package."""
    print("🔨 Building C++ library...")
    ctx.run("cd cpp && make clean && make && cd ..")

    print("📦 Building Python package...")
    ctx.run("uv build")

    print("✅ Build completed!")


@task
def dev(ctx):
    """Quick development check: fix issues and run tests."""
    check_fix(ctx)
    test(ctx)
