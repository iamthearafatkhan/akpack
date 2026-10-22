import sys
import os
import tempfile
import threading
import vlc
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QLabel, 
                             QSlider, QFrame, QStackedWidget, QProgressBar, 
                             QRadioButton, QButtonGroup, QLineEdit, QComboBox, QShortcut)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QKeyEvent, QKeySequence

# Import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.restorer import restore_file
from core.compressor import compress_file
from core.transcode import transcode_av1

# --- FIX FOR TASKBAR ICON IN EXE ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- THEME COLORS ---
BG_COLOR = "#0a1610"
SIDEBAR_COLOR = "#152219"
ACCENT_COLOR = "#a3e635" # Leaf color
BTN_COLOR = "#2d4a37"
BTN_HOVER = "#4d7c0f"
TEXT_COLOR = "#e5eedb"
TEXT_MUTED = "#8fa896"

class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)

class AKPackStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AKPack Studio")
        self.setGeometry(100, 100, 1100, 700)
        self.setStyleSheet(f"background-color: {BG_COLOR}; color: {TEXT_COLOR};")
        
        # Set App Icon
        icon_path = resource_path("logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # VLC Instance
        self.instance = vlc.Instance("--sub-autodetect-file", "--no-video-title-show", "--avcodec-hw=any")
        self.mediaplayer = self.instance.media_player_new()
        self.temp_dir = tempfile.mkdtemp()
        self.current_video_path = None

        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        root_layout = QVBoxLayout(main_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- TOP BAR ---
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(50)
        self.top_bar.setStyleSheet(f"background-color: {SIDEBAR_COLOR}; border-bottom: 1px solid #2d4a37;")
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(15, 0, 15, 0)
        
        self.logo_btn = QPushButton("🌿 AKPack Studio")
        self.logo_btn.setStyleSheet(f"background: transparent; color: {ACCENT_COLOR}; font-size: 18px; font-weight: bold; text-align: left;")
        self.logo_btn.clicked.connect(self.toggle_sidebar)
        top_layout.addWidget(self.logo_btn)
        top_layout.addStretch()
        root_layout.addWidget(self.top_bar)

        # --- MAIN BODY ---
        self.body_widget = QWidget()
        self.body_layout = QHBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet(f"background-color: {SIDEBAR_COLOR}; border-right: 1px solid #2d4a37;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(10)

        self.btn_nav_play = QPushButton("▶ Play Media")
        self.btn_nav_compress = QPushButton("📦 Compress / Transcode")
        self.btn_nav_restore = QPushButton("🔓 Restore File")
        
        for btn in [self.btn_nav_play, self.btn_nav_compress, self.btn_nav_restore]:
            btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_COLOR}; text-align: left; padding: 12px; font-size: 14px; border-radius: 8px; }} QPushButton:hover {{ background: {BTN_COLOR}; }}")
            sidebar_layout.addWidget(btn)

        self.btn_nav_play.clicked.connect(lambda: self.switch_page(0))
        self.btn_nav_compress.clicked.connect(lambda: self.switch_page(1))
        self.btn_nav_restore.clicked.connect(lambda: self.switch_page(2))

        sidebar_layout.addStretch()
        self.body_layout.addWidget(self.sidebar)

        self.stacked_widget = QStackedWidget()
        self.body_layout.addWidget(self.stacked_widget)

        root_layout.addWidget(self.body_widget)

        self.init_play_page()
        self.init_compress_page()
        self.init_restore_page()
        self.switch_page(0)

        # Global Shortcuts
        QShortcut(QKeySequence(Qt.Key_F), self, self.toggle_fullscreen)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.exit_fullscreen)

    def toggle_sidebar(self):
        if self.sidebar.isVisible():
            self.sidebar.hide()
        else:
            self.sidebar.show()

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        buttons = [self.btn_nav_play, self.btn_nav_compress, self.btn_nav_restore]
        for i, btn in enumerate(buttons):
            if i == index:
                btn.setStyleSheet(f"background: {BTN_COLOR}; color: {ACCENT_COLOR}; text-align: left; padding: 12px; font-size: 14px; border-radius: 8px; font-weight: bold;")
            else:
                btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_COLOR}; text-align: left; padding: 12px; font-size: 14px; border-radius: 8px; }} QPushButton:hover {{ background: {BTN_COLOR}; }}")

    # --- PAGE 1: PLAY MEDIA ---
    def init_play_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_frame, stretch=1)

        # Modern Controls Bar
        controls = QFrame()
        controls.setStyleSheet(f"background-color: {SIDEBAR_COLOR}; border-top: 1px solid #2d4a37;")
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(20, 15, 20, 15)

        # Seek Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height: 6px; background: {BG_COLOR}; border-radius: 3px; }}
            QSlider::sub-page:horizontal {{ background: {ACCENT_COLOR}; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: {ACCENT_COLOR}; width: 16px; margin: -5px 0; border-radius: 8px; }}
        """)
        
        self.slider.sliderPressed.connect(self.on_slider_press)
        self.slider.sliderReleased.connect(self.on_slider_release)
        self.slider.sliderMoved.connect(self.on_slider_move)
        self.is_slider_dragging = False
        controls_layout.addWidget(self.slider)

        # Button Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        # Play Button
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(45, 45)
        self.btn_play.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: {BG_COLOR}; border-radius: 22px; font-size: 18px; font-weight: bold;")
        self.btn_play.clicked.connect(self.toggle_play)

        # Time Label
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 13px; font-weight: bold; font-family: Arial;")
        self.time_label.setFixedWidth(110)
        self.time_label.setAlignment(Qt.AlignCenter)

        # Open Button
        self.btn_open = QPushButton("Open Media")
        self.btn_open.setStyleSheet(f"background-color: {BTN_COLOR}; color: white; padding: 10px 20px; border-radius: 8px; font-weight: bold;")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_file)

        # Fullscreen Button
        self.btn_full = QPushButton("⛶")
        self.btn_full.setStyleSheet(f"background-color: {BTN_COLOR}; color: white; padding: 10px 15px; border-radius: 8px; font-size: 16px; font-weight: bold;")
        self.btn_full.setCursor(Qt.PointingHandCursor)
        self.btn_full.setToolTip("Fullscreen (F)")
        self.btn_full.clicked.connect(self.toggle_fullscreen)

        # --- VERTICAL SEPARATOR 1 ---
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setStyleSheet("color: #2d4a37;")

        # --- SUBTITLE GROUP ---
        sub_frame = QFrame()
        sub_frame.setStyleSheet(f"background-color: {BG_COLOR}; border-radius: 8px; border: 1px solid {BTN_COLOR};")
        sub_layout = QHBoxLayout(sub_frame)
        sub_layout.setContentsMargins(5, 2, 5, 2)
        sub_layout.setSpacing(5)

        self.sub_combo = QComboBox()
        self.sub_combo.setMinimumWidth(180)
        self.sub_combo.setStyleSheet(f"""
            QComboBox {{ background-color: transparent; color: {TEXT_COLOR}; padding: 5px; border: none; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{ background-color: {SIDEBAR_COLOR}; color: {TEXT_COLOR}; selection-background-color: {BTN_HOVER}; selection-color: {BG_COLOR}; padding: 4px; outline: none; border: 1px solid {BTN_COLOR}; }}
        """)
        self.sub_combo.addItem("Subtitles: Off", -1)
        self.sub_combo.currentIndexChanged.connect(self.change_subtitle_track)

        self.btn_sub = QPushButton("+ Load")
        self.btn_sub.setStyleSheet(f"background-color: transparent; color: {ACCENT_COLOR}; padding: 5px 10px; font-size: 12px; font-weight: bold; border: none;")
        self.btn_sub.setCursor(Qt.PointingHandCursor)
        self.btn_sub.clicked.connect(self.load_subtitle)

        sub_layout.addWidget(self.sub_combo)
        sub_layout.addWidget(self.btn_sub)

        # --- VERTICAL SEPARATOR 2 ---
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("color: #2d4a37;")

        # Volume Controls
        self.vol_icon = QLabel("🔊")
        self.vol_icon.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 16px;")
        
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.setRange(0, 200) 
        self.vol_slider.setValue(100)
        self.vol_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height: 4px; background: {BG_COLOR}; border-radius: 2px; }}
            QSlider::sub-page:horizontal {{ background: {ACCENT_COLOR}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {TEXT_COLOR}; width: 12px; margin: -4px 0; border-radius: 6px; }}
        """)
        self.vol_slider.valueChanged.connect(self.set_volume)

        self.vol_label = QLabel("100%")
        self.vol_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.vol_label.setFixedWidth(35)

        # Assemble Button Row
        btn_row.addWidget(self.btn_play)
        btn_row.addWidget(self.time_label)
        btn_row.addSpacing(10)
        btn_row.addWidget(self.btn_open)
        btn_row.addWidget(self.btn_full)
        btn_row.addStretch()
        btn_row.addWidget(sep1)
        btn_row.addWidget(sub_frame)
        btn_row.addWidget(sep2)
        btn_row.addWidget(self.vol_icon)
        btn_row.addWidget(self.vol_slider)
        btn_row.addWidget(self.vol_label)

        controls_layout.addLayout(btn_row)
        layout.addWidget(controls)
        self.stacked_widget.addWidget(page)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

    def on_slider_press(self):
        self.is_slider_dragging = True

    def on_slider_move(self, position):
        if self.mediaplayer.get_length() > 0:
            length = self.mediaplayer.get_length() / 1000
            time = (position / 1000.0) * length
            m, s = divmod(int(time), 60)
            lm, ls = divmod(int(length), 60)
            self.time_label.setText(f"{m:02d}:{s:02d} / {lm:02d}:{ls:02d}")

    def on_slider_release(self):
        self.is_slider_dragging = False
        position = self.slider.value() / 1000.0
        self.mediaplayer.set_position(position)
        self.mediaplayer.play()

    # --- SUBTITLE LOGIC ---
    def update_subtitle_tracks(self):
        self.sub_combo.blockSignals(True)
        self.sub_combo.clear()
        self.sub_combo.addItem("Subtitles: Off", -1)
        
        spu_count = self.mediaplayer.video_get_spu_count()
        if spu_count > 0:
            descriptions = self.mediaplayer.video_get_spu_description()
            for track_id, track_name in descriptions:
                name_str = track_name.decode('utf-8', 'ignore') if isinstance(track_name, bytes) else track_name
                if not name_str.strip() or name_str == "Disable":
                    continue
                self.sub_combo.addItem(f"Sub: {name_str}", track_id)
        
        current_spu = self.mediaplayer.video_get_spu()
        index = self.sub_combo.findData(current_spu)
        if index >= 0:
            self.sub_combo.setCurrentIndex(index)
            
        self.sub_combo.blockSignals(False)

    def change_subtitle_track(self, index):
        spu_id = self.sub_combo.itemData(index)
        self.mediaplayer.video_set_spu(spu_id)

    # --- FULLSCREEN LOGIC ---
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.exit_fullscreen()
        else:
            self.showFullScreen()
            self.top_bar.hide()
            self.sidebar.hide()

    def exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.top_bar.show()
            self.sidebar.show()

    # --- PAGE 2: COMPRESS ---
    def init_compress_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignTop)
        title = QLabel("Compress & Transcode")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet(f"color: {ACCENT_COLOR};")
        layout.addWidget(title)
        layout.addSpacing(20)
        file_layout = QHBoxLayout()
        self.comp_file_input = QLineEdit()
        self.comp_file_input.setPlaceholderText("Select a file to compress...")
        self.comp_file_input.setStyleSheet(f"background: {SIDEBAR_COLOR}; border: 1px solid #2d4a37; padding: 10px; color: {TEXT_COLOR}; border-radius: 8px;")
        btn_browse = QPushButton("Browse")
        btn_browse.setStyleSheet(f"background-color: {BTN_COLOR}; color: white; padding: 10px 20px; border-radius: 8px;")
        btn_browse.clicked.connect(lambda: self.browse_file(self.comp_file_input))
        file_layout.addWidget(self.comp_file_input)
        file_layout.addWidget(btn_browse)
        layout.addLayout(file_layout)
        layout.addSpacing(20)
        mode_layout = QHBoxLayout()
        self.radio_lossless = QRadioButton("Lossless (.akp)")
        self.radio_lossless.setChecked(True)
        self.radio_lossless.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 14px;")
        self.radio_av1 = QRadioButton("AV1 Transcode (Smaller, Lossy)")
        self.radio_av1.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 14px;")
        mode_group = QButtonGroup(self)
        mode_group.addButton(self.radio_lossless)
        mode_group.addButton(self.radio_av1)
        mode_layout.addWidget(self.radio_lossless)
        mode_layout.addWidget(self.radio_av1)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        layout.addSpacing(30)
        self.btn_start_comp = QPushButton("Start Processing")
        self.btn_start_comp.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: {BG_COLOR}; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold;")
        self.btn_start_comp.clicked.connect(self.start_compress)
        layout.addWidget(self.btn_start_comp)
        self.comp_progress = QProgressBar()
        self.comp_progress.setStyleSheet(f"QProgressBar {{ border: 1px solid #2d4a37; border-radius: 8px; text-align: center; background: {SIDEBAR_COLOR}; color: white; }} QProgressBar::chunk {{ background-color: {ACCENT_COLOR}; border-radius: 8px; }}")
        self.comp_progress.setValue(0)
        layout.addWidget(self.comp_progress)
        self.stacked_widget.addWidget(page)

    # --- PAGE 3: RESTORE ---
    def init_restore_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignTop)
        title = QLabel("Restore Original File")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet(f"color: {ACCENT_COLOR};")
        layout.addWidget(title)
        layout.addSpacing(20)
        file_layout = QHBoxLayout()
        self.rest_file_input = QLineEdit()
        self.rest_file_input.setPlaceholderText("Select an .akp file...")
        self.rest_file_input.setStyleSheet(f"background: {SIDEBAR_COLOR}; border: 1px solid #2d4a37; padding: 10px; color: {TEXT_COLOR}; border-radius: 8px;")
        btn_browse = QPushButton("Browse")
        btn_browse.setStyleSheet(f"background-color: {BTN_COLOR}; color: white; padding: 10px 20px; border-radius: 8px;")
        btn_browse.clicked.connect(lambda: self.browse_file(self.rest_file_input, [("AKP Files", "*.akp")]))
        file_layout.addWidget(self.rest_file_input)
        file_layout.addWidget(btn_browse)
        layout.addLayout(file_layout)
        layout.addSpacing(30)
        self.btn_start_rest = QPushButton("Restore File")
        self.btn_start_rest.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: {BG_COLOR}; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold;")
        self.btn_start_rest.clicked.connect(self.start_restore)
        layout.addWidget(self.btn_start_rest)
        self.rest_progress = QProgressBar()
        self.rest_progress.setStyleSheet(f"QProgressBar {{ border: 1px solid #2d4a37; border-radius: 8px; text-align: center; background: {SIDEBAR_COLOR}; color: white; }} QProgressBar::chunk {{ background-color: {ACCENT_COLOR}; border-radius: 8px; }}")
        self.rest_progress.setValue(0)
        layout.addWidget(self.rest_progress)
        self.stacked_widget.addWidget(page)

    # --- UTILS ---
    def browse_file(self, line_edit, filetypes=None):
        if filetypes:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", "", ";".join([f"{k} ({v})" for k, v in filetypes]))
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            line_edit.setText(path)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Media", "", 
            "Media Files (*.akp *.mp4 *.mkv *.webm *.avi *.mov *.wmv);;AKP Files (*.akp);;All Files (*.*)"
        )
        if file_path:
            self.btn_open.setText("Loading...")
            self.btn_open.setEnabled(False)
            QApplication.processEvents()

            try:
                if file_path.lower().endswith(".akp"):
                    out_path = os.path.join(self.temp_dir, "video.mp4")
                    restore_file(file_path, out_path, verify=False)
                    self.current_video_path = out_path
                    self.play_video(out_path)
                else:
                    self.current_video_path = file_path
                    self.play_video(file_path)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                self.btn_open.setText("Open Media")
                self.btn_open.setEnabled(True)

    def play_video(self, path):
        media = self.instance.media_new(path)
        self.mediaplayer.set_media(media)
        
        if sys.platform.startswith('linux'):
            self.mediaplayer.set_xwindow(int(self.video_frame.winId()))
        elif sys.platform == "win32":
            self.mediaplayer.set_hwnd(int(self.video_frame.winId()))
        elif sys.platform == "darwin":
            self.mediaplayer.set_nsobject(int(self.video_frame.winId()))

        self.mediaplayer.play()
        self.mediaplayer.audio_set_volume(self.vol_slider.value())
        
        QTimer.singleShot(1000, self.update_subtitle_tracks)

    def load_subtitle(self):
        if not self.current_video_path: return
        sub_path, _ = QFileDialog.getOpenFileName(self, "Load Subtitle", "", "Subtitles (*.srt *.vtt)")
        if sub_path:
            abs_path = os.path.abspath(sub_path)
            self.mediaplayer.video_set_subtitle_file(abs_path)
            QTimer.singleShot(300, self.update_subtitle_tracks)
            QTimer.singleShot(400, lambda: self.mediaplayer.video_set_spu(1))

    def toggle_play(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.btn_play.setText("▶")
        else:
            self.mediaplayer.play()
            self.btn_play.setText("⏸")

    def set_volume(self, volume):
        self.mediaplayer.audio_set_volume(volume)
        self.vol_label.setText(f"{volume}%")

    def update_ui(self):
        if self.mediaplayer.is_playing():
            self.btn_play.setText("⏸")
            length = self.mediaplayer.get_length() / 1000
            time = self.mediaplayer.get_time() / 1000
            
            if length > 0 and not self.is_slider_dragging:
                self.slider.setValue(int((time / length) * 1000))
                m, s = divmod(int(time), 60)
                lm, ls = divmod(int(length), 60)
                self.time_label.setText(f"{m:02d}:{s:02d} / {lm:02d}:{ls:02d}")
        else:
            self.btn_play.setText("▶")

    def start_compress(self):
        file_path = self.comp_file_input.text()
        if not file_path or not os.path.exists(file_path): return
        is_lossless = self.radio_lossless.isChecked()
        self.btn_start_comp.setEnabled(False)
        self.comp_progress.setValue(0)
        self.comp_progress.setFormat("Processing... %p%")
        signals = WorkerSignals()
        signals.progress.connect(self.comp_progress.setValue)
        signals.finished.connect(self.on_task_finished)
        signals.error.connect(lambda e: self.on_task_error(e, self.btn_start_comp))

        def run():
            try:
                if is_lossless:
                    out_path = file_path + ".akp"
                    res = compress_file(file_path, out_path)
                    signals.finished.emit(f"Success! Saved to {out_path}", "Compress")
                else:
                    out_path = os.path.splitext(file_path)[0] + ".av1.mp4"
                    res = transcode_av1(file_path, out_path, job_id="local", crf=32, preset=8, on_progress=lambda p: signals.progress.emit(int(p)))
                    signals.finished.emit(f"AV1 Success! Saved to {out_path}", "Compress")
            except Exception as e:
                signals.error.emit(str(e))
        threading.Thread(target=run, daemon=True).start()

    def start_restore(self):
        file_path = self.rest_file_input.text()
        if not file_path or not os.path.exists(file_path): return
        self.btn_start_rest.setEnabled(False)
        self.rest_progress.setValue(10)
        signals = WorkerSignals()
        signals.finished.connect(self.on_task_finished)
        signals.error.connect(lambda e: self.on_task_error(e, self.btn_start_rest))

        def run():
            try:
                out_path = file_path[:-4] if file_path.endswith(".akp") else file_path + ".restored"
                restore_file(file_path, out_path)
                signals.finished.emit(f"Restored to {out_path}", "Restore")
            except Exception as e:
                signals.error.emit(str(e))
        threading.Thread(target=run, daemon=True).start()

    def on_task_finished(self, msg, task_type):
        if task_type == "Compress":
            self.btn_start_comp.setEnabled(True)
            self.comp_progress.setValue(100)
            self.comp_progress.setFormat(msg)
        else:
            self.btn_start_rest.setEnabled(True)
            self.rest_progress.setValue(100)
            self.rest_progress.setFormat(msg)

    def on_task_error(self, err, btn):
        btn.setEnabled(True)
        print(f"Error: {err}")

    def closeEvent(self, event):
        self.mediaplayer.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AKPackStudio()
    window.show()
    sys.exit(app.exec_())