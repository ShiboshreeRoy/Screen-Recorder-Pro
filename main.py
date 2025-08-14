import sys, cv2, numpy as np, pyautogui, threading, time, os, sounddevice as sd, scipy.io.wavfile as wav, keyboard, subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QSpinBox, QMessageBox, QHBoxLayout, QProgressBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor

# --------------------------
# Area Selector
# --------------------------
class AreaSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Recording Area")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setGeometry(0, 0, pyautogui.size().width, pyautogui.size().height)
        self.start_point = None
        self.end_point = None
        self.rect = None
        self.captured = False

    def mousePressEvent(self, event):
        self.start_point = (event.x(), event.y())
        self.end_point = self.start_point
        self.update()

    def mouseMoveEvent(self, event):
        if self.start_point:
            self.end_point = (event.x(), event.y())
            self.update()

    def mouseReleaseEvent(self, event):
        self.end_point = (event.x(), event.y())
        self.rect = (min(self.start_point[0], self.end_point[0]),
                     min(self.start_point[1], self.end_point[1]),
                     abs(self.start_point[0]-self.end_point[0]),
                     abs(self.start_point[1]-self.end_point[1]))
        self.captured = True
        self.close()

    def paintEvent(self, event):
        if self.start_point and self.end_point:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(0, 180, 255), 3, Qt.SolidLine))
            painter.drawRect(min(self.start_point[0], self.end_point[0]),
                             min(self.start_point[1], self.end_point[1]),
                             abs(self.start_point[0]-self.end_point[0]),
                             abs(self.start_point[1]-self.end_point[1]))

# --------------------------
# Main Recorder
# --------------------------
class ScreenRecorderPro(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro Screen & Audio Recorder")
        self.setGeometry(400, 200, 600, 450)

        # State variables
        self.recording = False
        self.paused = False
        self.folder = ""
        self.area = None
        self.audio_data = []
        self.audio_fs = 44100
        self.duration_limit = 0  # 0 = unlimited
        self.video_file = ""
        self.audio_file = ""
        self.final_file = ""

        # --------------------------
        # GUI Layout
        # --------------------------
        layout = QVBoxLayout()

        # Folder selection
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Save Folder:"))
        self.select_folder_btn = QPushButton("Select")
        self.select_folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.select_folder_btn)
        layout.addLayout(folder_layout)

        # FPS
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.fps_input = QSpinBox()
        self.fps_input.setValue(15)
        self.fps_input.setRange(1, 60)
        fps_layout.addWidget(self.fps_input)
        layout.addLayout(fps_layout)

        # Duration limit
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (sec, 0=unlimited):"))
        self.duration_input = QSpinBox()
        self.duration_input.setRange(0, 36000)
        duration_layout.addWidget(self.duration_input)
        layout.addLayout(duration_layout)

        # Progress bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Area selection
        self.select_area_btn = QPushButton("Select Recording Area")
        self.select_area_btn.clicked.connect(self.select_area)
        layout.addWidget(self.select_area_btn)

        # Buttons
        self.start_btn = QPushButton("Start Recording")
        self.start_btn.clicked.connect(self.start_recording)
        layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_recording)
        layout.addWidget(self.pause_btn)

        self.resume_btn = QPushButton("Resume")
        self.resume_btn.clicked.connect(self.resume_recording)
        layout.addWidget(self.resume_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_recording)
        layout.addWidget(self.stop_btn)

        self.screenshot_btn = QPushButton("Screenshot")
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        layout.addWidget(self.screenshot_btn)

        layout.addWidget(QLabel("Hotkeys: F9 Screenshot | F8 Pause/Resume | F10 Stop"))

        self.setLayout(layout)

        # Hotkeys
        keyboard.add_hotkey('F9', lambda: self.take_screenshot())
        keyboard.add_hotkey('F8', lambda: self.toggle_pause())
        keyboard.add_hotkey('F10', lambda: self.stop_recording())

    # --------------------------
    # GUI Functions
    # --------------------------
    def select_folder(self):
        self.folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not self.folder:
            QMessageBox.warning(self, "Warning", "Please select a folder!")

    def select_area(self):
        selector = AreaSelector()
        selector.show()
        selector.exec_() if hasattr(selector, 'exec_') else None
        if selector.captured:
            self.area = selector.rect
            QMessageBox.information(self, "Area Selected", f"Recording area set: {self.area}")

    # --------------------------
    # Recording Controls
    # --------------------------
    def start_recording(self):
        if not self.folder:
            QMessageBox.warning(self, "Warning", "Select a folder first!")
            return
        if self.recording:
            QMessageBox.warning(self, "Warning", "Recording already in progress!")
            return

        self.duration_limit = self.duration_input.value()
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self.video_file = os.path.join(self.folder, f"video_{timestamp}.mp4")
        self.audio_file = os.path.join(self.folder, f"audio_{timestamp}.wav")
        self.final_file = os.path.join(self.folder, f"recording_{timestamp}.mp4")

        for i in range(3,0,-1):
            print(f"Recording starts in {i}...")
            time.sleep(1)

        self.recording = True
        self.paused = False
        self.audio_data = []

        threading.Thread(target=self.record_screen).start()
        threading.Thread(target=self.record_audio).start()
        threading.Thread(target=self.update_progress).start()

        QMessageBox.information(self, "Recording", "Screen & audio recording started!")

    def pause_recording(self):
        if self.recording and not self.paused:
            self.paused = True
            QMessageBox.information(self, "Paused", "Recording paused!")

    def resume_recording(self):
        if self.recording and self.paused:
            self.paused = False
            QMessageBox.information(self, "Resumed", "Recording resumed!")

    def toggle_pause(self):
        if self.recording:
            self.paused = not self.paused
            print("Paused" if self.paused else "Resumed")

    def stop_recording(self):
        if self.recording:
            self.recording = False
            QMessageBox.information(self, "Stopped", f"Recording saved!\n{self.final_file}")
        else:
            QMessageBox.warning(self, "Warning", "No recording in progress!")

    # --------------------------
    # Screen Recording
    # --------------------------
    def record_screen(self):
        fps = self.fps_input.value()
        screen_size = (self.area[2], self.area[3]) if self.area else pyautogui.size()
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.video_file, fourcc, fps, screen_size)

        start_time = time.time()
        while self.recording:
            if not self.paused:
                img = pyautogui.screenshot(region=self.area) if self.area else pyautogui.screenshot()
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                out.write(frame)
            time.sleep(1/fps)
            if self.duration_limit > 0 and (time.time()-start_time) >= self.duration_limit:
                self.recording = False

        out.release()

        # Merge audio & video using ffmpeg
        if os.path.exists(self.audio_file):
            cmd = f'ffmpeg -y -i "{self.video_file}" -i "{self.audio_file}" -c:v copy -c:a aac "{self.final_file}"'
            subprocess.call(cmd, shell=True)
            os.remove(self.video_file)
            os.remove(self.audio_file)
        os.startfile(self.folder)

    # --------------------------
    # Audio Recording
    # --------------------------
    def record_audio(self):
        def callback(indata, frames, time_info, status):
            if self.recording and not self.paused:
                self.audio_data.append(indata.copy())

        with sd.InputStream(samplerate=self.audio_fs, channels=2, callback=callback):
            while self.recording:
                time.sleep(0.1)

        if self.audio_data:
            audio_np = np.concatenate(self.audio_data, axis=0)
            wav.write(self.audio_file, self.audio_fs, audio_np)

    # --------------------------
    # Progress bar
    # --------------------------
    def update_progress(self):
        if self.duration_limit <= 0:
            self.progress.setValue(0)
            return
        start_time = time.time()
        while self.recording:
            if not self.paused:
                elapsed = time.time() - start_time
                self.progress.setValue(int((elapsed/self.duration_limit)*100))
            time.sleep(0.1)
        self.progress.setValue(100)

    # --------------------------
    # Screenshot
    # --------------------------
    def take_screenshot(self):
        if not self.folder:
            QMessageBox.warning(self, "Warning", "Select a folder first!")
            return
        img = pyautogui.screenshot(region=self.area) if self.area else pyautogui.screenshot()
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.folder, f"screenshot_{timestamp}.png")
        img.save(filename)
        print(f"Screenshot saved: {filename}")
        QMessageBox.information(self, "Success", f"Screenshot saved as {filename}")

# --------------------------
# Run Application
# --------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScreenRecorderPro()
    window.show()
    sys.exit(app.exec_())
