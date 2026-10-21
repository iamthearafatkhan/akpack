import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys
import uuid

# Add project root to path so we can import core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.compressor import compress_file
from core.restorer import restore_file
from core.transcode import transcode_av1

# --- Forest Theme Colors ---
BG_COLOR = "#0a1610"
CARD_COLOR = "#152219"
TEXT_COLOR = "#e5eedb"
ACCENT_COLOR = "#a3e635"
BTN_COLOR = "#4d7c0f"
BTN_HOVER = "#65a30d"

class AKPackGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AKPack - Desktop Tool")
        self.root.geometry("520x480")
        self.root.configure(bg=BG_COLOR)

        # Header
        header = tk.Label(root, text="🌿 AKPack", font=("Helvetica", 24, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        header.pack(pady=(20, 5))
        
        sub = tk.Label(root, text="Lossless Compression & AV1 Transcoding", font=("Helvetica", 10), bg=BG_COLOR, fg="#8fa896")
        sub.pack(pady=(0, 15))

        # Main Card Frame
        card = tk.Frame(root, bg=CARD_COLOR, padx=20, pady=20)
        card.pack(fill="both", expand=True, padx=30, pady=10)

        # --- MODE SELECTION ---
        tk.Label(card, text="1. Choose Compression Mode", bg=CARD_COLOR, fg=TEXT_COLOR, font=("Helvetica", 11, "bold")).pack(anchor="w")
        
        self.mode_var = tk.StringVar(value="lossless")
        
        mode_frame = tk.Frame(card, bg=CARD_COLOR)
        mode_frame.pack(fill="x", pady=(5, 15))

        tk.Radiobutton(mode_frame, text="Lossless (Exact Byte Restore -> .akp)", variable=self.mode_var, value="lossless", 
                       bg=CARD_COLOR, fg=TEXT_COLOR, selectcolor=BG_COLOR, activebackground=CARD_COLOR, activeforeground=ACCENT_COLOR, font=("Helvetica", 10)).pack(anchor="w", pady=2)
        
        tk.Radiobutton(mode_frame, text="AV1 Video (50% Smaller -> .mp4)", variable=self.mode_var, value="transcode", 
                       bg=CARD_COLOR, fg=TEXT_COLOR, selectcolor=BG_COLOR, activebackground=CARD_COLOR, activeforeground=ACCENT_COLOR, font=("Helvetica", 10)).pack(anchor="w", pady=2)

        # --- COMPRESS ACTION ---
        tk.Label(card, text="2. Select File to Compress", bg=CARD_COLOR, fg=TEXT_COLOR, font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(10, 0))
        self.btn_compress = tk.Button(card, text="Browse & Compress", bg=BTN_COLOR, fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=self.compress_action)
        self.btn_compress.pack(fill="x", pady=(5, 20))

        # Divider
        tk.Frame(card, bg="#2d4a37", height=1).pack(fill="x", pady=10)

        # --- RESTORE ACTION ---
        tk.Label(card, text="3. Restore an .akp File", bg=CARD_COLOR, fg=TEXT_COLOR, font=("Helvetica", 11, "bold")).pack(anchor="w")
        self.btn_restore = tk.Button(card, text="Select .akp File to Restore", bg="#2d4a37", fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=self.restore_action)
        self.btn_restore.pack(fill="x", pady=(5, 10))

        # Status Label
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = tk.Label(root, textvariable=self.status_var, bg=BG_COLOR, fg="#8fa896", font=("Helvetica", 10, "bold"))
        self.status_label.pack(pady=10)

    def set_status(self, text, color="#8fa896"):
        self.status_var.set(text)
        self.status_label.config(fg=color)
        self.root.update()

    def compress_action(self):
        file_path = filedialog.askopenfilename(title="Select File to Compress")
        if not file_path: return
        
        mode = self.mode_var.get()
        
        if mode == "lossless":
            out_path = file_path + ".akp"
        else:
            # Strip original extension and add .av1.mp4
            base = os.path.splitext(file_path)[0]
            out_path = base + ".av1.mp4"
        
        self.btn_compress.config(state="disabled")
        self.btn_restore.config(state="disabled")
        self.set_status("Processing... Please wait.", ACCENT_COLOR)
        
        def run():
            try:
                if mode == "lossless":
                    result = compress_file(file_path, out_path)
                    saved = 100 * (1 - result["compressed_size"] / result["orig_size"]) if result["orig_size"] else 0
                    self.set_status(f"✅ Success! Saved {saved:.1f}% smaller.", ACCENT_COLOR)
                    messagebox.showinfo("Success", f"File compressed successfully!\n\nSaved to:\n{out_path}\n\nOriginal: {result['orig_size']:,} bytes\nCompressed: {result['compressed_size']:,} bytes")
                else:
                    # AV1 Transcode
                    job_id = uuid.uuid4().hex
                    
                    def on_progress(pct):
                        self.set_status(f"Encoding AV1: {pct:.1f}%", ACCENT_COLOR)
                        
                    result = transcode_av1(file_path, out_path, job_id=job_id, crf=32, preset=8, on_progress=on_progress)
                    self.set_status(f"✅ AV1 Success! Saved {result['savings_pct']:.1f}%.", ACCENT_COLOR)
                    messagebox.showinfo("Success", f"Video transcoded to AV1 successfully!\n\nSaved to:\n{out_path}\n\nOriginal: {result['orig_size']:,} bytes\nOutput: {result['new_size']:,} bytes")
            except Exception as e:
                self.set_status("❌ Processing failed.", "#fca5a5")
                messagebox.showerror("Error", str(e))
            finally:
                self.btn_compress.config(state="normal")
                self.btn_restore.config(state="normal")
                self.set_status("Ready")
                
        threading.Thread(target=run, daemon=True).start()

    def restore_action(self):
        file_path = filedialog.askopenfilename(title="Select .akp File", filetypes=[("AKP Files", "*.akp")])
        if not file_path: return
        
        out_path = file_path[:-4] if file_path.endswith(".akp") else file_path + ".restored"
        out_path = filedialog.asksaveasfilename(title="Save Restored File As", initialfile=os.path.basename(out_path))
        if not out_path: return

        self.btn_compress.config(state="disabled")
        self.btn_restore.config(state="disabled")
        self.set_status("Restoring... Please wait.", ACCENT_COLOR)

        def run():
            try:
                result = restore_file(file_path, out_path)
                self.set_status("✅ Restored perfectly!", ACCENT_COLOR)
                messagebox.showinfo("Success", f"File restored and verified successfully!\n\nSaved to:\n{out_path}\n\nSHA-256 Verified.")
            except Exception as e:
                self.set_status("❌ Restoration failed.", "#fca5a5")
                messagebox.showerror("Error", str(e))
            finally:
                self.btn_compress.config(state="normal")
                self.btn_restore.config(state="normal")
                self.set_status("Ready")

        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AKPackGUI(root)
    root.mainloop()