import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from typing import List, Callable, Optional, Dict

class MainWindow:
    def __init__(
        self,
        root: ctk.CTk,
        on_start_decryption: Callable[[str, str, List[str], bool, bool], None],
        on_cancel_decryption: Callable[[], None]
    ):
        self.root = root
        self.on_start_decryption = on_start_decryption
        self.on_cancel_decryption = on_cancel_decryption
        
        # Configure window
        self.root.title("🔓 PDF Decrypter Pro")
        self.root.geometry("820x680")
        self.root.minsize(800, 620)
        
        # Grid layout (1 row, 2 columns)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Initialize UI components
        self._setup_sidebar()
        self._setup_main_frame()
        self._setup_styles()
        
        # Set default values
        self.input_dir_entry.insert(0, "")
        self.output_dir_entry.insert(0, "")

    def _setup_styles(self) -> None:
        """Configures colored log tags on the text terminal."""
        # CustomTkinter CTkTextbox supports tags via the underlying tk.Text widget
        text_widget = self.log_terminal._textbox
        text_widget.tag_config("success", foreground="#2ecc71")  # Beautiful flat green
        text_widget.tag_config("error", foreground="#e74c3c")    # Beautiful flat red
        text_widget.tag_config("warning", foreground="#f39c12")  # Beautiful flat orange
        text_widget.tag_config("info", foreground="#3498db")     # Beautiful flat blue
        text_widget.tag_config("timestamp", foreground="#7f8c8d")# Cool gray

    def _setup_sidebar(self) -> None:
        """Sets up the left sidebar for logo, settings and instructions."""
        self.sidebar_frame = ctk.CTkFrame(self.root, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)  # Spacer push help to bottom

        # Logo and Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="🔓 PDF DECRYPTER", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.sub_logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="批次安全解密工具", 
            font=ctk.CTkFont(size=12, weight="normal"),
            text_color="gray"
        )
        self.sub_logo_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Configurations Area
        self.config_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="系統設定 Options", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.config_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        # Copy unencrypted checkbox
        self.copy_unencrypted_var = tk.BooleanVar(value=True)
        self.copy_checkbox = ctk.CTkCheckBox(
            self.sidebar_frame, 
            text="複製未加密檔案", 
            variable=self.copy_unencrypted_var,
            font=ctk.CTkFont(size=12)
        )
        self.copy_checkbox.grid(row=3, column=0, padx=20, pady=8, sticky="w")

        # Overwrite existing checkbox
        self.overwrite_var = tk.BooleanVar(value=False)
        self.overwrite_checkbox = ctk.CTkCheckBox(
            self.sidebar_frame, 
            text="直接覆寫現有檔案", 
            variable=self.overwrite_var,
            font=ctk.CTkFont(size=12)
        )
        self.overwrite_checkbox.grid(row=4, column=0, padx=20, pady=8, sticky="nw")

        # Theme controller dropdown
        self.appearance_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="介面主題 UI Theme", 
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.appearance_label.grid(row=5, column=0, padx=20, pady=(20, 5), sticky="sw")
        
        self.appearance_optionemenu = ctk.CTkOptionMenu(
            self.sidebar_frame, 
            values=["Dark", "Light", "System"],
            command=self._change_appearance_mode
        )
        self.appearance_optionemenu.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="sw")

    def _setup_main_frame(self) -> None:
        """Sets up the main workspace on the right side."""
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)  # Logs terminal stretches

        # ---------------- INPUT & OUTPUT PATHS ----------------
        self.paths_frame = ctk.CTkFrame(self.main_frame)
        self.paths_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15), padx=2)
        self.paths_frame.grid_columnconfigure(1, weight=1)

        # Input Path Selector
        self.input_label = ctk.CTkLabel(self.paths_frame, text="輸入資料夾：", font=ctk.CTkFont(weight="bold"))
        self.input_label.grid(row=0, column=0, padx=(15, 5), pady=12, sticky="e")
        
        self.input_dir_entry = ctk.CTkEntry(self.paths_frame, placeholder_text="請選取包含加密 PDF 的資料夾...")
        self.input_dir_entry.grid(row=0, column=1, padx=5, pady=12, sticky="ew")
        
        self.input_browse_btn = ctk.CTkButton(self.paths_frame, text="瀏覽...", width=80, command=self._browse_input_dir)
        self.input_browse_btn.grid(row=0, column=2, padx=(5, 15), pady=12)

        # Output Path Selector
        self.output_label = ctk.CTkLabel(self.paths_frame, text="輸出資料夾：", font=ctk.CTkFont(weight="bold"))
        self.output_label.grid(row=1, column=0, padx=(15, 5), pady=(0, 12), sticky="e")
        
        self.output_dir_entry = ctk.CTkEntry(self.paths_frame, placeholder_text="請選取解密後檔案的儲存位置...")
        self.output_dir_entry.grid(row=1, column=1, padx=5, pady=(0, 12), sticky="ew")
        
        self.output_browse_btn = ctk.CTkButton(self.paths_frame, text="瀏覽...", width=80, command=self._browse_output_dir)
        self.output_browse_btn.grid(row=1, column=2, padx=(5, 15), pady=(0, 12))

        # ---------------- PASSWORDS MANAGEMENT ----------------
        self.pass_frame = ctk.CTkFrame(self.main_frame)
        self.pass_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15), padx=2)
        self.pass_frame.grid_columnconfigure(0, weight=1)

        self.pass_header_frame = ctk.CTkFrame(self.pass_frame, fg_color="transparent")
        self.pass_header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        self.pass_header_frame.grid_columnconfigure(0, weight=1)

        self.pass_title = ctk.CTkLabel(
            self.pass_header_frame, 
            text="候選密碼輸入 (一列一組，將依序嘗試)：", 
            font=ctk.CTkFont(weight="bold")
        )
        self.pass_title.grid(row=0, column=0, sticky="w")

        self.load_pass_file_btn = ctk.CTkButton(
            self.pass_header_frame, 
            text="載入密碼檔 (.txt)", 
            width=130, 
            command=self._load_password_file,
            font=ctk.CTkFont(size=11)
        )
        self.load_pass_file_btn.grid(row=0, column=1, sticky="e")

        self.password_textbox = ctk.CTkTextbox(self.pass_frame, height=100)
        self.password_textbox.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))
        self.password_textbox.insert("1.0", "# 提示：在此輸入密碼候選清單（每行一組）\n123456\npassword\nadmin123")

        # ---------------- LOGS CONSOLE ----------------
        self.logs_frame = ctk.CTkFrame(self.main_frame)
        self.logs_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 15), padx=2)
        self.logs_frame.grid_columnconfigure(0, weight=1)
        self.logs_frame.grid_rowconfigure(1, weight=1)

        self.logs_title = ctk.CTkLabel(self.logs_frame, text="執行紀錄 Log Output：", font=ctk.CTkFont(weight="bold"))
        self.logs_title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 2))

        self.log_terminal = ctk.CTkTextbox(self.logs_frame, fg_color="#1e1e1e", font=ctk.CTkFont(family="Consolas", size=11))
        self.log_terminal.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 12))
        self.log_terminal.insert("1.0", "系統已準備就緒，請設定輸入與輸出資料夾後按下「開始解密」。\n")
        self.log_terminal.configure(state="disabled")

        # ---------------- CONTROLS & PROGRESS ----------------
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.grid(row=3, column=0, sticky="ew", padx=2)
        self.controls_frame.grid_columnconfigure(0, weight=1)

        # Progress bar elements
        self.progress_info_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.progress_info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.progress_info_frame.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(self.progress_info_frame, text="等待操作...", font=ctk.CTkFont(size=12))
        self.progress_label.grid(row=0, column=0, sticky="w")

        self.percent_label = ctk.CTkLabel(self.progress_info_frame, text="0%", font=ctk.CTkFont(size=12, weight="bold"))
        self.percent_label.grid(row=0, column=1, sticky="e")

        self.progress_bar = ctk.CTkProgressBar(self.controls_frame, orientation="horizontal")
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.progress_bar.set(0)

        # Main Action Buttons
        self.actions_btn_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.actions_btn_frame.grid(row=2, column=0, sticky="ew")
        self.actions_btn_frame.grid_columnconfigure(0, weight=1)
        self.actions_btn_frame.grid_columnconfigure(1, weight=1)

        self.start_btn = ctk.CTkButton(
            self.actions_btn_frame, 
            text="🔓 開始解密 Start Decrypting", 
            height=40, 
            command=self._on_start_btn_click,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.start_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.cancel_btn = ctk.CTkButton(
            self.actions_btn_frame, 
            text="🛑 取消執行 Cancel", 
            fg_color="#c0392b", 
            hover_color="#e74c3c",
            height=40, 
            command=self._on_cancel_btn_click,
            state="disabled",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.cancel_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")

    # ---------------- BROWSE AND LOAD ACTIONS ----------------
    def _browse_input_dir(self) -> None:
        selected = filedialog.askdirectory(title="選擇加密 PDF 來源資料夾")
        if selected:
            # Standardize path slashes for cross-platform presentation
            std_path = os.path.normpath(selected)
            self.input_dir_entry.delete(0, "end")
            self.input_dir_entry.insert(0, std_path)

    def _browse_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="選擇解密後 PDF 輸出資料夾")
        if selected:
            std_path = os.path.normpath(selected)
            self.output_dir_entry.delete(0, "end")
            self.output_dir_entry.insert(0, std_path)

    def _load_password_file(self) -> None:
        """Loads lines from a user-selected text file as candidate passwords."""
        selected_file = filedialog.askopenfilename(
            title="選取密碼檔", 
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if selected_file:
            try:
                with open(selected_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                # Strip and filter empty lines
                pw_list = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
                
                # Replace password box content
                self.password_textbox.delete("1.0", "end")
                self.password_textbox.insert("1.0", "\n".join(pw_list))
                
                self.log(f"成功從密碼檔載入 {len(pw_list)} 組密碼！", "success")
                messagebox.showinfo("成功", f"已成功載入 {len(pw_list)} 組候選密碼！")
            except Exception as e:
                self.log(f"載入密碼檔失敗：{e}", "error")
                messagebox.showerror("錯誤", f"無法讀取密碼檔：{e}")

    # ---------------- INTERFACE STATE CONTROLS ----------------
    def _change_appearance_mode(self, new_appearance_mode: str) -> None:
        ctk.set_appearance_mode(new_appearance_mode)

    def set_processing_state(self, is_processing: bool) -> None:
        """Toggles GUI elements status to prevent editing during execution."""
        if is_processing:
            self.start_btn.configure(state="disabled", text="⚡ 正在解密檔案...")
            self.cancel_btn.configure(state="normal")
            self.input_browse_btn.configure(state="disabled")
            self.output_browse_btn.configure(state="disabled")
            self.load_pass_file_btn.configure(state="disabled")
            self.input_dir_entry.configure(state="disabled")
            self.output_dir_entry.configure(state="disabled")
            self.copy_checkbox.configure(state="disabled")
            self.overwrite_checkbox.configure(state="disabled")
        else:
            self.start_btn.configure(state="normal", text="🔓 開始解密 Start Decrypting")
            self.cancel_btn.configure(state="disabled")
            self.input_browse_btn.configure(state="normal")
            self.output_browse_btn.configure(state="normal")
            self.load_pass_file_btn.configure(state="normal")
            self.input_dir_entry.configure(state="normal")
            self.output_dir_entry.configure(state="normal")
            self.copy_checkbox.configure(state="normal")
            self.overwrite_checkbox.configure(state="normal")

    # ---------------- BUTTON CLICKS (CONTROLLER BINDINGS) ----------------
    def _on_start_btn_click(self) -> None:
        input_dir = self.input_dir_entry.get().strip()
        output_dir = self.output_dir_entry.get().strip()
        
        # Parse passwords textbox
        raw_pw_text = self.password_textbox.get("1.0", "end").strip()
        passwords = []
        for line in raw_pw_text.split("\n"):
            line_str = line.strip()
            # Skip comments or empty lines
            if line_str and not line_str.startswith("#"):
                passwords.append(line_str)

        # Validations
        if not input_dir:
            messagebox.showerror("欄位錯誤", "請指定輸入資料夾。")
            return
        if not output_dir:
            messagebox.showerror("欄位錯誤", "請指定輸出資料夾。")
            return
        if not os.path.exists(input_dir):
            messagebox.showerror("資料夾不存在", f"找不到指定的輸入資料夾：\n{input_dir}")
            return
            
        # Standardize paths
        input_dir = os.path.normpath(input_dir)
        output_dir = os.path.normpath(output_dir)

        if input_dir == output_dir and not self.overwrite_var.get():
            messagebox.showwarning(
                "路徑警示", 
                "輸入與輸出資料夾路徑相同！\n若未開啟『直接覆寫』，解密成功的檔案名稱將會自動加上 '_decrypted' 綴字。"
            )

        copy_unencrypted = self.copy_unencrypted_var.get()
        overwrite = self.overwrite_var.get()

        self.set_processing_state(True)
        self.on_start_decryption(input_dir, output_dir, passwords, copy_unencrypted, overwrite)

    def _on_cancel_btn_click(self) -> None:
        self.cancel_btn.configure(state="disabled", text="🛑 正在取消中...")
        self.on_cancel_decryption()

    # ---------------- THREAD-SAFE UI LOG & PROGRESS UPDATERS ----------------
    def thread_safe(self, func: Callable, *args) -> None:
        """Schedules execution of a UI update on the main Tkinter thread."""
        self.root.after(0, func, *args)

    def clear_logs(self) -> None:
        self.log_terminal.configure(state="normal")
        self.log_terminal.delete("1.0", "end")
        self.log_terminal.configure(state="disabled")

    def log(self, message: str, level: str = "info") -> None:
        """Appends a timestamped colored log line to the log terminal (main thread)."""
        self.log_terminal.configure(state="normal")
        
        timestamp = f"[{time.strftime('%H:%M:%S')}] "
        self.log_terminal.insert("end", timestamp, "timestamp")
        
        # Color match standard:success, error, warning, info
        if level in ["success", "error", "warning", "info"]:
            self.log_terminal.insert("end", f"{message}\n", level)
        else:
            self.log_terminal.insert("end", f"{message}\n")
            
        self.log_terminal.see("end")
        self.log_terminal.configure(state="disabled")

    def update_progress(self, current: int, total: int, filename: str) -> None:
        """Updates the progress bar and labels (main thread)."""
        if total <= 0:
            percentage = 0
            text = "進度：0 / 0"
        else:
            percentage = current / total
            text = f"處理中 ({current}/{total})：{filename}"
            
        self.progress_bar.set(percentage)
        self.progress_label.configure(text=text)
        self.percent_label.configure(text=f"{int(percentage * 100)}%")
