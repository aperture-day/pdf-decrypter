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
        self.view.log("初始化解密引擎...", "info")
        self.view.update_progress(0, 0, "正在讀取資料夾...")

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
            self.view.log("正在發出取消請求，請稍候...", "warning")
            self.worker.cancel()

    # ---------------- DECRYPTION ENGINE CALLBACKS (THREAD-SAFE BOUND) ----------------
    def _on_worker_start(self, total: int) -> None:
        def gui_action():
            self.total_files = total
            self.view.log(f"開始進行批次處理，目標 PDF 檔案數：{total}", "info")
            self.view.update_progress(0, total, "準備開始...")
            if total == 0:
                self.view.log("未在輸入資料夾中發現任何 PDF 檔案！", "warning")
        self.view.thread_safe(gui_action)

    def _on_worker_progress(self, file_idx: int, filename: str, status: str, detail: str) -> None:
        def gui_action():
            self.view.update_progress(file_idx, self.total_files, filename)
            
            # Formulate colored message depending on status
            log_level = "info"
            status_text = ""
            if status == "SUCCESS":
                log_level = "success"
                status_text = "成功"
            elif status == "FAILED":
                log_level = "error"
                status_text = "失敗"
            elif status == "SKIPPED":
                log_level = "warning"
                status_text = "跳過"

            self.view.log(f"檔案 [{file_idx}/{self.total_files}] {filename} -> {status_text} ({detail})", log_level)
        self.view.thread_safe(gui_action)

    def _on_worker_log(self, message: str, level: str) -> None:
        def gui_action():
            # Translate worker levels to view terminal colors
            self.view.log(message, level)
        self.view.thread_safe(gui_action)

    def _on_worker_complete(self, success: int, failed: int, skipped: int) -> None:
        def gui_action():
            self.view.set_processing_state(False)
            self.view.update_progress(self.total_files, self.total_files, "處理完成！")
            
            # Show a pop-up dialog summarizing results
            summary_msg = f"處理完畢！\n\n成功個數: {success}\n失敗個數: {failed}\n跳過個數: {skipped}"
            self.view.log("\n========================================", "info")
            self.view.log(f"任務完成！ 成功: {success} | 失敗: {failed} | 跳過: {skipped}", "success" if failed == 0 else "warning")
            self.view.log("========================================\n", "info")
            
            messagebox.showinfo("解密完成", summary_msg)
            self.worker = None
        self.view.thread_safe(gui_action)

    def _on_worker_cancel(self) -> None:
        def gui_action():
            self.view.set_processing_state(False)
            self.view.update_progress(0, self.total_files, "操作已取消")
            self.view.log("\n[!] 操作已遭使用者強制取消。", "error")
            messagebox.showwarning("已取消", "PDF 解密批次操作已取消。")
            self.worker = None
        self.view.thread_safe(gui_action)

    def on_closing(self) -> None:
        """Fires when the window close button is pressed."""
        if self.worker:
            if messagebox.askyesno("正在執行中", "解密任務正在進行，確定要強制關閉並離開嗎？"):
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
