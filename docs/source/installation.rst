Installation
============

Requirements
------------

Before installing BMD Signal Generator, ensure you have:

* **Python 3.12+** installed
* **Blackmagic Design Desktop Video drivers** (latest version)
* **Blackmagic Design DeckLink SDK 15.3** 
* **C++ compiler** with C++20 support

System Dependencies
-------------------

macOS
^^^^^

1. Install Xcode Command Line Tools::

    xcode-select --install

2. Download and install Blackmagic Desktop Video drivers from the 
   `Blackmagic Design Support page <https://www.blackmagicdesign.com/support/>`_

3. Download the DeckLink SDK 15.3 and extract headers to the project

Linux
^^^^^

1. Install build dependencies::

    sudo apt-get update
    sudo apt-get install build-essential g++ pkg-config

2. Download and install Desktop Video for Linux from Blackmagic Design

3. Extract DeckLink SDK headers

Windows
^^^^^^^

1. Install Visual Studio 2019+ or Visual Studio Build Tools
2. Download and install Desktop Video for Windows
3. Extract DeckLink SDK headers

Package Installation
--------------------

Install from PyPI (when available)::

    pip install bmd-signal-generator

Install from source::

    git clone https://github.com/OpenLEDEval/bmd-signal-gen.git
    cd bmd-signal-gen
    pip install uv
    uv sync
    uv run invoke build

Development Installation
------------------------

For development work::

    git clone https://github.com/OpenLEDEval/bmd-signal-gen.git
    cd bmd-signal-gen
    pip install uv
    uv sync --group dev --group docs
    uv run invoke build

Verification
------------

Verify the installation by checking for connected devices::

    bmd_signal_gen device-details

This should list any connected DeckLink devices and their capabilities.