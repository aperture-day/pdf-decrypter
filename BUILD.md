# Build & Developer Guide - PDF Decrypter

This document provides instructions on how to set up the development environment, run, test, and package the PDF Decrypter desktop application using **`uv`**.

---

## 📋 Prerequisites

To run or build this application, you need:
1. **Python**: Version 3.10 or newer (tested on Python 3.13).
2. **uv**: A modern, lightning-fast Python package and project manager. If you do not have it installed, execute:
   * **Windows (PowerShell)**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
   * **macOS/Linux**: `curl -sSf https://astral.sh/uv/install.sh | sh`

---

## 🛠️ Environment Setup

`uv` manages dependencies and virtual environments automatically. You do **not** need to manually create virtual environments, activate them, or run `pip` installation steps. 

When you run any `uv run` command, `uv` will automatically discover the project's dependencies specified in `pyproject.toml`, build a local virtual environment (`.venv`) if it does not exist, install requirements, and execute your command in that context.

---

## 🚀 Running the Application

To start the graphical user interface, run the following command in the project directory:

```bash
uv run main.py
```

---

## 🧪 Running Unit Tests

We have a robust unit test suite that validates the PDF decryption worker, sequential password trials, unencrypted file handlers, and cancel event signals.

Run the automated tests using:

```bash
uv run python -m unittest discover -s tests
```

---

## 📦 Packaging Standalone Desktop Apps

Packaging converts the Python scripts into platform-native, standalone desktop files that run independently without requiring a Python installation on the target machine.

### 1. Building for Windows (`PDF Decrypter.exe`)

On Windows, run the PyInstaller command inside your project directory. We run this inside the `uv` environment so that PyInstaller can resolve and bundle all active environment packages and CustomTkinter's assets (fonts, themes, icons):

```bash
uv run --with pyinstaller pyinstaller --onefile --windowed --name="PDF Decrypter" --collect-all customtkinter main.py
```

* **Output**: The packaged binary will be available in **`dist/PDF Decrypter.exe`**.

---

### 2. Building for macOS (`PDF Decrypter.dmg`)

Because PyInstaller builds binaries native to the host OS it runs on, **you must execute these commands on a macOS machine** to generate macOS binaries.

#### Step A: Compile the `.app` bundle
On your Mac, open the terminal in the project root directory and run:

```bash
uv run --with pyinstaller pyinstaller --onefile --windowed --name="PDF Decrypter" --collect-all customtkinter main.py
```
* **Output**: This generates the standalone bundle **`dist/PDF Decrypter.app`**.

#### Step B: Wrap the `.app` into a `.dmg` Disk Image
To create a clean, distributable disk image package, use the native macOS `hdiutil` utility in your terminal:

```bash
hdiutil create -fs HFS+ -volname "PDF Decrypter" -srcfolder "dist/PDF Decrypter.app" "dist/PDF Decrypter.dmg"
```
* **Output**: This will output **`dist/PDF Decrypter.dmg`**, which can be distributed to users for traditional drag-to-install deployment.
