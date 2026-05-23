import os
import sys
from tkinter import messagebox
import customtkinter as ctk
from typing import List, Optional

# Set up module path to ensure local imports work if executed directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.decryptor import DecryptionWorker
from src.ui.app_window import MainWindow

class AppController:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.worker: Optional[DecryptionWorker] = None
        self.total_files = 0
        
        # Initialize UI
        self.view = MainWindow(
            root=self.root,
            on_start_decryption=self.start_decryption,
            on_cancel_decryption=self.cancel_decryption
        )
        
        # Intercept window close to handle clean exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_decryption(
        self,
        input_dir: str,
        output_dir: str,
        passwords: List[str],
        copy_unencrypted: bool,
        overwrite: bool
    ) -> None:
        """Controller action triggered when the user starts the decryption process."""
        self.view.clear_logs()
        self.view.log("Initializing decryption engine...", "info")
        self.view.update_progress(0, 0, "Scanning directory...")

        # Setup worker
        self.worker = DecryptionWorker(
            input_dir=input_dir,
            output_dir=output_dir,
            passwords=passwords,
            copy_unencrypted=copy_unencrypted,
            overwrite=overwrite,
            on_start=self._on_worker_start,
            on_progress=self._on_worker_progress,
            on_log=self._on_worker_log,
            on_complete=self._on_worker_complete,
            on_cancel=self._on_worker_cancel
        )
        
        # Start execution
        self.worker.start()

    def cancel_decryption(self) -> None:
        """Controller action triggered when the user clicks the cancel button."""
        if self.worker:
            self.view.log("Sending cancellation request, please wait...", "warning")
            self.worker.cancel()

    # ---------------- DECRYPTION ENGINE CALLBACKS (THREAD-SAFE BOUND) ----------------
    def _on_worker_start(self, total: int) -> None:
        def gui_action():
            self.total_files = total
            self.view.log(f"Batch processing started. Target PDF count: {total}", "info")
            self.view.update_progress(0, total, "Preparing...")
            if total == 0:
                self.view.log("No PDF files found in the input directory!", "warning")
        self.view.thread_safe(gui_action)

    def _on_worker_progress(self, file_idx: int, filename: str, status: str, detail: str) -> None:
        def gui_action():
            self.view.update_progress(file_idx, self.total_files, filename)
            
            # Formulate colored message depending on status
            log_level = "info"
            status_text = ""
            if status == "SUCCESS":
                log_level = "success"
                status_text = "SUCCESS"
            elif status == "FAILED":
                log_level = "error"
                status_text = "FAILED"
            elif status == "SKIPPED":
                log_level = "warning"
                status_text = "SKIPPED"

            self.view.log(f"File [{file_idx}/{self.total_files}] {filename} -> {status_text} ({detail})", log_level)
        self.view.thread_safe(gui_action)

    def _on_worker_log(self, message: str, level: str) -> None:
        def gui_action():
            # Translate worker levels to view terminal colors
            self.view.log(message, level)
        self.view.thread_safe(gui_action)

    def _on_worker_complete(self, success: int, failed: int, skipped: int) -> None:
        def gui_action():
            self.view.set_processing_state(False)
            self.view.update_progress(self.total_files, self.total_files, "Processing complete!")
            
            # Show a pop-up dialog summarizing results
            summary_msg = f"Processing complete!\n\nSuccessful: {success}\nFailed: {failed}\nSkipped: {skipped}"
            self.view.log("\n========================================", "info")
            self.view.log(f"Task complete! Success: {success} | Failed: {failed} | Skipped: {skipped}", "success" if failed == 0 else "warning")
            self.view.log("========================================\n", "info")
            
            messagebox.showinfo("Decryption Complete", summary_msg)
            self.worker = None
        self.view.thread_safe(gui_action)

    def _on_worker_cancel(self) -> None:
        def gui_action():
            self.view.set_processing_state(False)
            self.view.update_progress(0, self.total_files, "Operation cancelled")
            self.view.log("\n[!] Operation cancelled by user.", "error")
            messagebox.showwarning("Cancelled", "PDF decryption batch operation has been cancelled.")
            self.worker = None
        self.view.thread_safe(gui_action)

    def on_closing(self) -> None:
        """Fires when the window close button is pressed."""
        if self.worker:
            if messagebox.askyesno("In Progress", "Decryption task is currently in progress. Are you sure you want to force close and exit?"):
                self.worker.cancel()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    # Setup premium styling for CustomTkinter
    ctk.set_appearance_mode("System")  # Uses OS theme (Light/Dark) automatically
    ctk.set_default_color_theme("blue")  # Themes all UI elements in deep modern blue
    
    root = ctk.CTk()
    app = AppController(root)
    root.mainloop()

if __name__ == "__main__":
    main()
