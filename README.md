# PDF Decrypter Desktop App

A modern, fast, cross-platform PDF batch decryption application built with **Python**, **uv**, **CustomTkinter**, and **pypdf**.

---

## 🚀 How to Run the Application

Since the project uses `uv` for dependency management and setup, launching the application is extremely simple and requires no manual environment configuration:

1. Open your terminal in the workspace directory `cd pdf-decrypter`.
2. Run the application:
   ```bash
   uv run main.py
   ```
   *`uv` will automatically detect, create, and populate the virtual environment with all required packages (including `customtkinter`, `pypdf`, and `pycryptodome` for 256-bit AES decryption) and launch the GUI immediately.*

---

## 🎨 Design & UI Architecture

The interface is engineered around modern desktop aesthetics, utilizing a beautiful dark-blue themed sidebar layout:

### 1. Left Sidebar (Sidebar Options Panel)
* **Title & Subtitle**: `🔓 PDF DECRYPTER` - Batch Decryption Utility
* **Copy Unencrypted Files (Copy unencrypted files)**: When enabled, files in the input folder that are already decrypted will be copied as-is to the output folder. If disabled, they are skipped.
* **Overwrite Existing Files (Overwrite existing files)**: When enabled, it overwrites files in the output directory if there's a name collision. When disabled, the application automatically appends `_decrypted` (and incrementing numeric indexes like `_decrypted_1` if needed) to ensure no data is lost.
* **UI Theme Selector**: Real-time theme switcher allowing the user to select **Dark**, **Light**, or **System** appearance modes.

### 2. Main Workspace Panel
* **Paths Selection**: Input and Output directory entry fields equipped with native OS folder browsing dialog buttons (`Browse...`).
* **Interactive Passwords Entry**:
  * A multi-line scrollable text field to enter candidate passwords (one per line, ignoring comment lines starting with `#`).
  * A premium **Load Password File (.txt)** button allowing users to import large password wordlists directly from standard `.txt` text files.
* **Live logs console**: A terminal-style scrollable display that outputs active operations with precise colored feedback tags (Green for Success, Red for Errors, Yellow for Warnings, and Blue for General Info).
* **Progress Panel**: Displays a real-time progress bar, a calculated percentage indicator, and the name of the file currently being processed.
* **Double Action buttons**: A primary high-contrast **Start Decrypting** button and a danger-styled **Cancel** button (which is safely disabled except during decryption).

---

## ⚙️ Core Technical Engineering

* **Thread-Safe Architecture**: The decryption operations run fully asynchronously inside a background worker thread (`threading.Thread`). All callbacks (progress updates, terminal logging, and completion alerts) are scheduled on the main thread using standard Tkinter `root.after` dispatching. This prevents GUI freezes and eliminates any potential thread safety crashes on macOS or Windows.
* **Sequential Password Attack**: For every encrypted PDF, the decryptor tries candidate passwords sequentially in the exact order they are listed, immediately breaking and saving the file upon first success.
* **Graceful Cancellation**: Periodically verifies an atomic thread cancellation event signal. Clicking the red Cancel button immediately halts operations, deletes partially written files, logs the interrupt, and notifies the user via an alert dialog.
* **Safe Exit Interceptor**: Intercepts standard OS window close protocols (`WM_DELETE_WINDOW`) to verify if a decryption is in progress, preventing data corruption by prompting the user for verification.

---

## 🧪 Verification & Quality Control

### 1. Automated Tests
We created a self-contained unit test suite in [test_decryption.py](file:///c:/project/pdf-decrypter/tests/test_decryption.py). The test suite programmatically generates dummy encrypted PDFs and validates:
1. Sequential password trial and output decryption correctness.
2. Skipping or copying behavior of unencrypted PDFs.
3. Thread cancellation signals and abort routines.

#### Running Tests:
```bash
uv run python -m unittest discover -s tests
```
#### Output:
```text
...
----------------------------------------------------------------------
Ran 3 tests in 0.015s

OK
```

### 2. Manual Verification Checklist
When launching the GUI:
* Try selecting the same directory for input and output, and note the friendly warning pop-up informing you about auto-renaming behaviors.
* Load a sample text file of passwords using **Load Password File (.txt)** and verify it populates the text box correctly.
* Press the theme drop-down to toggle between Dark mode and Light mode, checking that the UI controls redraw flawlessly.
