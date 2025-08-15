"""Invoke tasks for code quality and formatting."""

import os
import platform
import shutil
import tarfile
import zipfile
from pathlib import Path

import requests
from invoke.context import Context
from invoke.tasks import task


@task
def python_lint(ctx: Context, fix: bool = False) -> None:
    """Run ruff linting on Python code with optional auto-fix.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    fix : bool, optional
        Whether to auto-fix issues, by default False
    """
    print("🔍 Linting Python code...")
    cmd = "ruff check ."
    if fix:
        cmd += " --fix"
    ctx.run(cmd)


@task
def lint(ctx: Context, fix: bool = False) -> None:
    """Run all linting (Python and C++) with optional auto-fix.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    fix : bool, optional
        Whether to auto-fix issues, by default False
    """
    python_lint(ctx, fix=fix)
    cpp_lint(ctx, fix=fix)


@task
def format(ctx: Context, check: bool = False) -> None:
    """Run ruff and clang-format with optional check-only mode.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    check : bool, optional
        Whether to check formatting without applying changes, by default False
    """
    # Format Python code
    print("📝 Formatting Python code...")
    cmd = "ruff format ."
    if check:
        cmd += " --check"
    ctx.run(cmd)

    # Format C++ code
    print("📝 Formatting C++ code...")
    cpp_format(ctx, check=check)


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
    """Run all code quality checks (lint, format check, typecheck, spellcheck).

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
    """Auto-fix linting issues and format code (Python and C++).

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
    ctx.run("rm -rf cpp/build", warn=True)
    ctx.run("rm -f cpp/compile_commands.json", warn=True)
    print("🧹 Cleaned up cache files and build artifacts!")


@task
def pristine(ctx: Context) -> None:
    """Clean up all build artifacts, cache files, and toolchain.

    This is a more aggressive clean that removes everything including
    the local toolchain. Use this for a complete reset.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    # Run regular clean first
    clean(ctx)

    # Clean up toolchain directory
    toolchain_dir = Path(".toolchain")
    if toolchain_dir.exists():
        shutil.rmtree(toolchain_dir)
        print("🧹 Cleaned up .toolchain directory")

    print("✨ Repository reset to pristine state!")


@task
def test(ctx: Context) -> None:
    """Run tests.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    ctx.run("python -m pytest tests/")


def _get_cmake_path() -> str:
    """Get path to cmake binary, preferring local toolchain over system."""
    # Check for local cmake first
    system = platform.system()
    if system == "Darwin":
        toolchain_cmake = Path(".toolchain/CMake.app/Contents/bin/cmake")
    else:
        toolchain_cmake = Path(".toolchain/cmake/bin")
        cmake_exe = "cmake.exe" if system == "Windows" else "cmake"
        toolchain_cmake = toolchain_cmake / cmake_exe

    if toolchain_cmake.exists():
        return str(toolchain_cmake)
    elif shutil.which("cmake"):
        return "cmake"
    else:
        raise RuntimeError(
            "cmake not found! Run 'uv run invoke setup-cmake' to install local toolchain"
        )


@task(pre=[clean])
def build(ctx: Context) -> None:
    """Build the C++ library and Python package using CMake.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    """
    try:
        cmake_path = _get_cmake_path()
    except RuntimeError as e:
        print(f"❌ {e}")
        print("🔧 Setting up CMake first...")
        setup_cmake(ctx)
        cmake_path = _get_cmake_path()

    print("🔨 Building C++ library with CMake...")

    # Ensure build directory exists
    build_dir = Path("cpp/build")
    build_dir.mkdir(parents=True, exist_ok=True)

    # Configure with CMake (generates compile_commands.json)
    print("⚙️  Configuring build with CMake...")
    result = ctx.run(f'"{cmake_path}" -B cpp/build -S cpp -DCMAKE_BUILD_TYPE=Release')

    if not result or not result.ok:
        print("❌ CMake configuration failed!")
        return

    # Build
    print("🏗️  Building with CMake...")
    result = ctx.run(f'"{cmake_path}" --build cpp/build')

    if not result or not result.ok:
        print("❌ CMake build failed!")
        return

    # Copy compile_commands.json to cpp directory for clang-tidy
    compile_commands_src = Path("cpp/build/compile_commands.json")
    compile_commands_dst = Path("cpp/compile_commands.json")

    if compile_commands_src.exists():
        import shutil

        shutil.copy2(compile_commands_src, compile_commands_dst)
        print("📋 Copied compile_commands.json for clang-tidy")
    else:
        print("⚠️  compile_commands.json not generated")

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


def _download_file(url: str, filename: str) -> None:
    """Download a file from URL with progress display."""
    print(f"⬇️  Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Download with progress
    total_size = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r   Progress: {percent:.1f}%", end="", flush=True)
    print()  # New line after progress


def _extract_archive(filename: str, target_dir: Path, special_handling=None) -> None:
    """Extract archive to target directory with optional special handling."""
    print(f"📂 Extracting {filename}...")

    # Clean up existing target directory
    if target_dir.exists():
        shutil.rmtree(target_dir)

    # Extract based on file extension
    if filename.endswith((".tar.xz", ".tar.gz")):
        mode = "r:xz" if filename.endswith(".tar.xz") else "r:gz"
        with tarfile.open(filename, mode) as tar:
            members = tar.getnames()
            if not members:
                raise RuntimeError(f"Empty archive: {filename}")
            top_dir = members[0].split("/")[0]
            tar.extractall()

    elif filename.endswith(".zip"):
        with zipfile.ZipFile(filename, "r") as zip_file:
            members = zip_file.namelist()
            if not members:
                raise RuntimeError(f"Empty archive: {filename}")
            top_dir = members[0].split("/")[0]
            zip_file.extractall()
    else:
        raise RuntimeError(f"Unsupported archive format: {filename}")

    # Handle extraction with special or default logic
    if special_handling:
        special_handling(filename, top_dir, target_dir)
    else:
        # Default behavior: move extracted directory to target
        shutil.move(top_dir, target_dir)


def _download_and_extract(
    url: str, filename: str, target_dir: Path, special_handling=None
) -> str:
    """Download and extract a package from URL to target directory.

    Parameters
    ----------
    url : str
        Download URL for the package
    filename : str
        Local filename to save the download
    target_dir : Path
        Directory where the extracted content should be placed
    special_handling : callable, optional
        Optional function to handle special extraction logic.
        Should accept (filename, top_dir, target_dir) and return None.

    Returns
    -------
    str
        Path to the top-level extracted directory
    """
    _download_file(url, filename)
    _extract_archive(filename, target_dir, special_handling)

    # Clean up downloaded file
    os.remove(filename)

    return str(target_dir)


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
def setup_llvm(_: Context, version: str = "20.1.8") -> None:
    """Download and setup local LLVM toolchain with clang-tidy and clang-format.

    Downloads LLVM binary release for the current platform and extracts
    it to .toolchain/llvm/. This provides clang-tidy, clang-format, and other
    LLVM tools for development.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    version : str, optional
        LLVM version to download, by default "20.1.8"
    """
    toolchain_dir = Path(".toolchain")
    llvm_dir = toolchain_dir / "llvm"

    # Skip if already installed
    clang_tidy_exe = (
        "clang-tidy.exe" if platform.system() == "Windows" else "clang-tidy"
    )

    if (llvm_dir / "bin" / clang_tidy_exe).exists():
        print(f"✅ LLVM toolchain already installed at {llvm_dir}")
        return

    print(f"📦 Setting up LLVM {version}...")

    # Create directories
    toolchain_dir.mkdir(exist_ok=True)

    # Determine platform-specific download URL
    system = platform.system()
    if system == "Darwin":
        prefix = "LLVM"
        arch = "macOS-ARM64"
    elif system == "Windows":
        prefix = "clang+llvm"
        arch = "x86_64-pc-windows-msvc"
    else:
        prefix = "LLVM-"
        arch = "x86_64-linux-gnu-ubuntu-18.04"

    filename = f"{prefix}-{version}-{arch}.tar.xz"
    download_url = f"https://github.com/llvm/llvm-project/releases/download/llvmorg-{version}/{filename}"

    # Download and extract using helper function (LLVM uses default extraction)
    _download_and_extract(download_url, filename, llvm_dir)

    # Verify installation
    clang_tidy_path = llvm_dir / "bin" / clang_tidy_exe
    if not clang_tidy_path.exists():
        raise RuntimeError(f"clang-tidy not found at {clang_tidy_path}")

    print("✅ LLVM toolchain installed successfully!")
    print(f"📍 Location: {llvm_dir}")
    print(f"🔧 clang-tidy: {clang_tidy_path}")


def _handle_cmake_extraction(_: str, top_dir: str, target_dir: Path) -> None:
    """Special handler for CMake extraction on macOS (app bundle)."""
    system = platform.system()
    toolchain_dir = target_dir.parent

    if system == "Darwin":
        # For macOS, move the entire CMake.app bundle to toolchain directory
        extracted_cmake_app = Path(top_dir) / "CMake.app"
        if extracted_cmake_app.exists():
            shutil.move(str(extracted_cmake_app), str(toolchain_dir / "CMake.app"))
        else:
            # Fallback: move the whole directory and assume it's CMake.app
            shutil.move(top_dir, str(toolchain_dir / "CMake.app"))
        # Remove the now-empty extracted directory
        if Path(top_dir).exists():
            shutil.rmtree(top_dir)
    else:
        # For Linux/Windows, use default behavior
        shutil.move(top_dir, target_dir)


@task
def setup_cmake(_: Context, version: str = "4.1.0") -> None:
    """Download and setup local CMake build system.

    Downloads CMake binary release for the current platform and extracts
    it to .toolchain/cmake/. This provides CMake for cross-platform builds
    and compile_commands.json generation.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    version : str, optional
        CMake version to download, by default "4.1.0"
    """
    toolchain_dir = Path(".toolchain")
    system = platform.system()

    # Platform-specific directory structure
    if system == "Darwin":
        cmake_dir = toolchain_dir / "CMake.app" / "Contents"
    else:
        cmake_dir = toolchain_dir / "cmake"

    # Skip if already installed
    cmake_exe = "cmake.exe" if system == "Windows" else "cmake"
    if (cmake_dir / "bin" / cmake_exe).exists():
        print(f"✅ CMake already installed at {cmake_dir}")
        return

    print(f"📦 Setting up CMake {version}...")

    # Create directories
    toolchain_dir.mkdir(exist_ok=True)

    # Determine platform-specific CMake download
    if system == "Darwin":
        cmake_filename = f"cmake-{version}-macos-universal.tar.gz"
    elif system == "Windows":
        cmake_filename = f"cmake-{version}-windows-x86_64.zip"
    else:
        cmake_filename = f"cmake-{version}-linux-x86_64.tar.gz"

    cmake_download_url = f"https://github.com/Kitware/CMake/releases/download/v{version}/{cmake_filename}"

    # Download and extract using helper function
    _download_and_extract(
        cmake_download_url,
        cmake_filename,
        cmake_dir,
        special_handling=_handle_cmake_extraction,
    )

    # Verify CMake installation
    cmake_path = cmake_dir / "bin" / cmake_exe
    if not cmake_path.exists():
        raise RuntimeError(f"cmake not found at {cmake_path}")

    print("✅ CMake installed successfully!")
    print(f"📍 Location: {cmake_dir}")
    print(f"🔧 cmake: {cmake_path}")


@task
def setup(
    ctx: Context, version: str = "20.1.8", cmake_version: str = "4.1.0"
) -> None:
    """Download and setup complete development toolchain (LLVM + CMake).

    Orchestrates installation of both LLVM tools and CMake by calling the
    individual setup tasks. This provides a convenient single command to
    set up the entire development environment.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    version : str, optional
        LLVM version to download, by default "20.1.8"
    cmake_version : str, optional
        CMake version to download, by default "4.1.0"
    """
    print("📦 Setting up complete development toolchain...")

    # Install LLVM tools (clang-tidy, clang-format, etc.)
    setup_llvm(ctx, version=version)

    # Install CMake
    setup_cmake(ctx, version=cmake_version)

    print("✅ Development toolchain setup complete!")


@task
def cpp_format(ctx: Context, check: bool = False) -> None:
    """Run clang-format on C++ source files.

    Uses local clang-format from .toolchain if available, falls back to system.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    check : bool, optional
        Whether to check formatting without applying changes, by default False
    """
    # Check for local clang-format first
    toolchain_clang_format = Path(".toolchain/llvm/bin")
    clang_format_exe = (
        "clang-format.exe" if platform.system() == "Windows" else "clang-format"
    )

    if (toolchain_clang_format / clang_format_exe).exists():
        clang_format_path = str(toolchain_clang_format / clang_format_exe)
        print(f"🔧 Using local clang-format: {clang_format_path}")
    elif shutil.which("clang-format"):
        clang_format_path = "clang-format"
        print("🔧 Using system clang-format")
    else:
        print("❌ clang-format not found!")
        print("💡 Run 'uv run invoke setup-toolchain' to install local toolchain")
        return

    cpp_files = []
    cpp_dir = Path("cpp")
    if cpp_dir.exists():
        # Find all C++ files but exclude DeckLink SDK
        all_cpp_files = []
        all_cpp_files.extend(cpp_dir.glob("*.cpp"))
        all_cpp_files.extend(cpp_dir.glob("*.hpp"))
        all_cpp_files.extend(cpp_dir.glob("*.cc"))
        all_cpp_files.extend(cpp_dir.glob("*.h"))

        # Filter out SDK files
        cpp_files = [
            f for f in all_cpp_files if "Blackmagic DeckLink SDK" not in str(f)
        ]

    if not cpp_files:
        print("📂 No C++ files found in cpp/ directory")
        return

    print(f"🔍 Running clang-format on {len(cpp_files)} C++ files...")

    # Build clang-format command
    cmd_parts = [clang_format_path]
    if check:
        cmd_parts.append("--dry-run")
        cmd_parts.append("--Werror")
    else:
        cmd_parts.append("-i")

    # Add source files
    cmd_parts.extend(str(f) for f in cpp_files)

    cmd = " ".join(f'"{part}"' if " " in part else part for part in cmd_parts)
    result = ctx.run(cmd, warn=True)

    if result and result.ok:
        if check:
            print("✅ No C++ formatting issues found!")
        else:
            print("✅ C++ files formatted successfully!")
    else:
        if check:
            print("⚠️  C++ formatting issues detected!")
        else:
            print("⚠️  C++ formatting encountered issues!")


@task
def cpp_lint(ctx: Context, fix: bool = False) -> None:
    """Run clang-tidy on C++ source files.

    Uses xcrun to find the correct macOS SDK for local clang-tidy compatibility.

    Parameters
    ----------
    ctx : Context
        Invoke context object
    fix : bool, optional
        Whether to auto-fix issues, by default False
    """
    # Check for local clang-tidy first
    toolchain_clang_tidy = Path(".toolchain/llvm/bin")
    clang_tidy_exe = (
        "clang-tidy.exe" if platform.system() == "Windows" else "clang-tidy"
    )

    if (toolchain_clang_tidy / clang_tidy_exe).exists():
        clang_tidy_path = str(toolchain_clang_tidy / clang_tidy_exe)
        print(f"🔧 Using local clang-tidy: {clang_tidy_path}")
    elif shutil.which("clang-tidy"):
        clang_tidy_path = "clang-tidy"
        print("🔧 Using system clang-tidy")
    else:
        print("❌ clang-tidy not found!")
        print("💡 Run 'uv run invoke setup-toolchain' to install local toolchain")
        return

    # Find C++ files (exclude DeckLink SDK)
    cpp_dir = Path("cpp")
    if not cpp_dir.exists():
        print("📂 No cpp/ directory found")
        return

    all_cpp_files = []
    all_cpp_files.extend(cpp_dir.glob("*.cpp"))
    all_cpp_files.extend(cpp_dir.glob("*.hpp"))
    all_cpp_files.extend(cpp_dir.glob("*.cc"))
    all_cpp_files.extend(cpp_dir.glob("*.h"))

    cpp_files = [f for f in all_cpp_files if "Blackmagic DeckLink SDK" not in str(f)]

    if not cpp_files:
        print("📂 No C++ files found in cpp/ directory")
        return

    print(f"🔍 Running clang-tidy on {len(cpp_files)} C++ files...")

    # Get macOS SDK path using xcrun
    try:
        sdk_result = ctx.run("xcrun --show-sdk-path", hide=True)
        if sdk_result and sdk_result.stdout:
            sdk_path = sdk_result.stdout.strip()
            print(f"📍 Using macOS SDK: {sdk_path}")
        else:
            print("❌ Failed to get SDK path from xcrun")
            return
    except Exception as e:
        print(f"❌ Failed to get SDK path: {e}")
        return

    # Build clang-tidy command
    cmd_parts = [clang_tidy_path]
    if fix:
        cmd_parts.append("--fix")

    # Add source files
    cmd_parts.extend(str(f) for f in cpp_files)

    # Configure with proper sysroot and target
    cmd_parts.extend(
        [
            f"--extra-arg-before=--sysroot={sdk_path}",
            "--extra-arg-before=-target",
            "--extra-arg-before=arm64-apple-macos",
        ]
    )

    # Add compile commands if available
    if Path("cpp/compile_commands.json").exists():
        cmd_parts.extend(["-p", "cpp"])
    else:
        # Add basic include paths for BMD project
        cmd_parts.extend(
            [
                "--",
                "-std=c++20",
                "-I",
                "cpp/Blackmagic DeckLink SDK 14.4/Mac/include",
            ]
        )

    cmd = " ".join(f'"{part}"' if " " in part else part for part in cmd_parts)
    result = ctx.run(cmd, warn=True)

    if result and result.ok:
        print("✅ No C++ linting issues found!")
    else:
        print("⚠️  C++ linting issues detected!")


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
