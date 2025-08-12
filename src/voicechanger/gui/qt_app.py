from PySide6 import QtWidgets, QtCore, QtGui
from voicechanger.audio_engine import AudioEngine, VC_SINK_NAME


DARK_QSS = """
* { font-family: Inter, Segoe UI, Ubuntu, Roboto, Cantarell, "Noto Sans", Arial; font-size: 13px; }
QWidget { background-color: #111418; color: #E6E6E6; }
QGroupBox {
    border: 1px solid #1E232A; border-radius: 10px; margin-top: 12px; padding: 8px 12px 12px 12px;
}
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 2px 6px; color: #9BB0C9; font-weight: 600; }
QComboBox, QLineEdit, QSpinBox {
    background: #0D1117; border: 1px solid #2B3440; border-radius: 8px; padding: 6px 8px; selection-background-color: #2E7DFF;
}
QComboBox::drop-down { border: 0px; }
QComboBox QAbstractItemView { background: #0D1117; border: 1px solid #2B3440; selection-background-color: #2E7DFF; }
QPushButton {
    background: #1A2332; border: 1px solid #2B3440; border-radius: 10px; padding: 10px 14px; font-weight: 600;
}
QPushButton:hover { background: #223049; }
QPushButton:pressed { background: #1A2740; }
QPushButton:disabled { color: #7C8798; background: #141A22; border-color: #1F2630; }
#PrimaryBtn { background: #2E7DFF; border: 1px solid #2E7DFF; color: white; }
#PrimaryBtn:hover { background: #3A86FF; }
#DangerBtn { background: #E45858; border: 1px solid #E45858; color: white; }
#DangerBtn:hover { background: #EF5E5E; }
QLabel#Header { font-size: 18px; font-weight: 700; color: #EAF2FF; }
QFrame#Divider { background: #1E232A; max-height: 1px; min-height: 1px; }
QStatusBar { background: #0D1117; border-top: 1px solid #1E232A; }
#Badge {
    background: #152238; border: 1px solid #2B3440; border-radius: 8px; padding: 6px 10px; color: #9BB0C9; font-weight: 600;
}
"""


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoiceChanger")
        self.engine = AudioEngine()
        self.setStyleSheet(DARK_QSS)
        self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

        self.header = QtWidgets.QLabel("VoiceChanger")
        self.header.setObjectName("Header")

        self.badge = QtWidgets.QLabel(f"Output: {VC_SINK_NAME}")
        self.badge.setObjectName("Badge")

        self.in_combo = QtWidgets.QComboBox()
        self.sr_combo = QtWidgets.QComboBox()
        self.block_combo = QtWidgets.QComboBox()
        self.refresh_btn = QtWidgets.QPushButton(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload), "Refresh")
        self.start_btn = QtWidgets.QPushButton(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay), "Start")
        self.stop_btn = QtWidgets.QPushButton(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop), "Stop")
        self.start_btn.setObjectName("PrimaryBtn")
        self.stop_btn.setObjectName("DangerBtn")

        self.status = QtWidgets.QStatusBar()
        self.status.showMessage("Ready")

        self.sr_combo.addItems(["48000", "44100"])
        self.block_combo.addItems(["256", "512", "1024"])
        self.block_combo.setCurrentText("512")
        self._populate_inputs()

        devices_box = QtWidgets.QGroupBox("Audio")
        f = QtWidgets.QFormLayout(devices_box)
        f.setHorizontalSpacing(14)
        f.setVerticalSpacing(10)
        f.addRow("Input", self._h(self.in_combo, self.refresh_btn))
        f.addRow("Sample rate", self.sr_combo)
        f.addRow("Block size", self.block_combo)

        controls = QtWidgets.QHBoxLayout()
        controls.addStretch(1)
        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.header)
        top.addStretch(1)
        top.addWidget(self.badge)

        divider = QtWidgets.QFrame()
        divider.setObjectName("Divider")
        divider.setFrameShape(QtWidgets.QFrame.HLine)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 10)
        root.addLayout(top)
        root.addWidget(divider)
        root.addSpacing(8)
        root.addWidget(devices_box)
        root.addSpacing(6)
        root.addLayout(controls)
        root.addWidget(self.status)

        self.stop_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)
        self.refresh_btn.clicked.connect(self._populate_inputs)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._poll_status)
        self.timer.start()

        self.resize(600, 300)

    def _h(self, *widgets):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        for x in widgets:
            lay.addWidget(x)
        return w

    def _populate_inputs(self):
        in_devs, _ = self.engine.list_devices()
        current = self.in_combo.currentData()
        self.in_combo.clear()
        for idx, name, host in in_devs:
            self.in_combo.addItem(f"{name} [{host}]  #{idx}", idx)
        if self.in_combo.count() > 0:
            if current is not None:
                i = self.in_combo.findData(current)
                if i >= 0:
                    self.in_combo.setCurrentIndex(i)
                else:
                    self.in_combo.setCurrentIndex(0)
            else:
                self.in_combo.setCurrentIndex(0)
        self.status.showMessage("Devices refreshed")

    def on_start(self):
        indev = self.in_combo.currentData()
        sr = int(self.sr_combo.currentText())
        block = int(self.block_combo.currentText())
        try:
            out_idx = self.engine.find_output_index()
            if out_idx is None:
                QtWidgets.QMessageBox.critical(self, "Audio error", f"No output device for {VC_SINK_NAME}")
                return
            self.engine.start(indev, out_idx, sr, block)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status.showMessage(f"Streaming → {VC_SINK_NAME}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Audio error", str(e))

    def on_stop(self):
        self.engine.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status.showMessage("Stopped")

    def _poll_status(self):
        try:
            while True:
                msg = self.engine.q_status.get_nowait()
                self.status.showMessage(msg)
        except Exception:
            pass


def run_gui():
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    app.exec()
