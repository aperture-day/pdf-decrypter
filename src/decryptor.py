import os
import shutil
import threading
from typing import List, Callable, Optional
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError, DependencyError

class DecryptionWorker:
    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        passwords: List[str],
        copy_unencrypted: bool = True,
        overwrite: bool = False,
        on_start: Optional[Callable[[int], None]] = None,
        on_progress: Optional[Callable[[int, str, str, str], None]] = None,
        on_log: Optional[Callable[[str, str], None]] = None,
        on_complete: Optional[Callable[[int, int, int], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.passwords = passwords
        self.copy_unencrypted = copy_unencrypted
        self.overwrite = overwrite
        
        # Callbacks
        self.on_start = on_start
        self.on_progress = on_progress
        self.on_log = on_log
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        
        # Cancellation event
        self.cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Starts the decryption process in a background thread."""
        self.cancel_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        """Requests cancellation of the decryption process."""
        self.cancel_event.set()

    def _log(self, message: str, level: str = "info") -> None:
        if self.on_log:
            self.on_log(message, level)

    def _get_unique_output_path(self, filename: str) -> str:
        """Generates a unique filename in the output directory if overwrite is False."""
        base_path = os.path.join(self.output_dir, filename)
        if self.overwrite or not os.path.exists(base_path):
            return base_path
            
        # File collision occurs and overwrite is False: insert "_decrypted" or increment
        name, ext = os.path.splitext(filename)
        # Try appending _decrypted first
        decrypted_name = f"{name}_decrypted{ext}"
        decrypted_path = os.path.join(self.output_dir, decrypted_name)
        if not os.path.exists(decrypted_path):
            return decrypted_path
            
        # If even that exists, start incrementing
        counter = 1
        while True:
            inc_name = f"{name}_decrypted_{counter}{ext}"
            inc_path = os.path.join(self.output_dir, inc_name)
            if not os.path.exists(inc_path):
                return inc_path
            counter += 1

    def _run(self) -> None:
        """The main decryption loop executed in the background thread."""
        try:
            self._log("開始掃描資料夾...", "info")
            if not os.path.exists(self.input_dir):
                self._log(f"錯誤：輸入資料夾不存在 - {self.input_dir}", "error")
                if self.on_complete:
                    self.on_complete(0, 0, 0)
                return

            # Scan the input folder (non-recursive)
            all_files = os.listdir(self.input_dir)
            pdf_files = [f for f in all_files if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(self.input_dir, f))]
            total_files = len(pdf_files)

            self._log(f"掃描完成。共找到 {total_files} 個 PDF 檔案。", "info")
            if self.on_start:
                self.on_start(total_files)

            if total_files == 0:
                self._log("沒有需要處理的 PDF 檔案。", "warning")
                if self.on_complete:
                    self.on_complete(0, 0, 0)
                return

            # Ensure output directory exists
            try:
                os.makedirs(self.output_dir, exist_ok=True)
            except Exception as e:
                self._log(f"無法建立輸出資料夾：{e}", "error")
                if self.on_complete:
                    self.on_complete(0, 0, 0)
                return

            success_count = 0
            failed_count = 0
            skipped_count = 0

            for idx, filename in enumerate(pdf_files):
                # Check for cancellation before processing each file
                if self.cancel_event.is_set():
                    self._log("使用者已取消操作。", "warning")
                    if self.on_cancel:
                        self.on_cancel()
                    return

                in_path = os.path.join(self.input_dir, filename)
                self._log(f"[{idx+1}/{total_files}] 正在處理：{filename}", "info")

                try:
                    reader = PdfReader(in_path)
                    
                    # 1. Check if the PDF is encrypted
                    if not reader.is_encrypted:
                        if self.copy_unencrypted:
                            out_path = self._get_unique_output_path(filename)
                            self._log(f" └ 檔案未加密。正在複製到輸出資料夾...", "info")
                            shutil.copy2(in_path, out_path)
                            success_count += 1
                            if self.on_progress:
                                self.on_progress(idx + 1, filename, "SUCCESS", f"未加密，複製成功 -> {os.path.basename(out_path)}")
                        else:
                            self._log(f" └ 檔案未加密，跳過。", "info")
                            skipped_count += 1
                            if self.on_progress:
                                self.on_progress(idx + 1, filename, "SKIPPED", "未加密且設定跳過")
                        continue

                    # 2. Try candidate passwords
                    decrypted_successfully = False
                    tried_passwords_count = 0
                    
                    # Standardize passwords list: filter out empty entries
                    valid_passwords = [pw for pw in self.passwords if pw]
                    
                    if not valid_passwords:
                        self._log(f" └ 檔案已加密，但未提供任何密碼候選字。", "error")
                        failed_count += 1
                        if self.on_progress:
                            self.on_progress(idx + 1, filename, "FAILED", "已加密，但無輸入密碼")
                        continue

                    for pw in valid_passwords:
                        tried_passwords_count += 1
                        try:
                            # Try decryption
                            decrypt_status = reader.decrypt(pw)
                            
                            # Verify decryption by trying to access pages or checking status
                            # status standard: 0 = not decrypted, 1 = user, 2 = owner
                            if decrypt_status != 0:
                                # Access a page to trigger any lazy-loaded decryption error and verify
                                if len(reader.pages) >= 0:
                                    # Verification passed!
                                    decrypted_successfully = True
                                    self._log(f" └ 解密成功！使用的密碼第 {tried_passwords_count} 組", "success")
                                    
                                    # Save decrypted file
                                    out_path = self._get_unique_output_path(filename)
                                    writer = PdfWriter()
                                    for page in reader.pages:
                                        writer.add_page(page)
                                    
                                    with open(out_path, "wb") as f:
                                        writer.write(f)
                                        
                                    success_count += 1
                                    if self.on_progress:
                                        self.on_progress(idx + 1, filename, "SUCCESS", f"解密成功 -> {os.path.basename(out_path)}")
                                    break
                        except Exception as e:
                            # Decryption failed with this password, log internally and continue trying
                            self._log(f" └ 嘗試密碼 '{pw[:3]}***' 失敗：{str(e)}", "debug")
                            continue

                    if not decrypted_successfully:
                        self._log(f" └ 錯誤：所有候選密碼均無法解密此檔案。", "error")
                        failed_count += 1
                        if self.on_progress:
                            self.on_progress(idx + 1, filename, "FAILED", f"密碼錯誤 (嘗試了 {tried_passwords_count} 組)")

                except PdfReadError:
                    self._log(f" └ 錯誤：檔案非有效的 PDF 格式或已損毀。", "error")
                    failed_count += 1
                    if self.on_progress:
                        self.on_progress(idx + 1, filename, "FAILED", "無效的 PDF 檔案")
                except DependencyError as de:
                    self._log(f" └ 錯誤（缺少依賴）：{str(de)}", "error")
                    failed_count += 1
                    if self.on_progress:
                        self.on_progress(idx + 1, filename, "FAILED", "系統缺少解密所需之依賴")
                except Exception as e:
                    self._log(f" └ 處理時發生未預期錯誤：{str(e)}", "error")
                    failed_count += 1
                    if self.on_progress:
                        self.on_progress(idx + 1, filename, "FAILED", f"未預期錯誤: {str(e)}")

            # Process complete
            self._log(f"處理完畢！成功: {success_count}, 失敗: {failed_count}, 跳過: {skipped_count}", "info")
            if self.on_complete:
                self.on_complete(success_count, failed_count, skipped_count)

        except Exception as e:
            self._log(f"執行執行緒時發生致命錯誤：{e}", "error")
            if self.on_complete:
                self.on_complete(0, 0, 0)
