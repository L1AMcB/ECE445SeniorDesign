import sys
import os
from PySide6 import QtWidgets, QtGui, QtCore
from bluetooth_handler import BluetoothHandler

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CTC Force Measurement System")
        self.resize(1200, 800)

        # Bluetooth handlers
        self.bt1 = BluetoothHandler("ESP32_1")
        self.bt2 = BluetoothHandler("ESP32_2")

        # Storage for force-screen widgets
        self.force_widgets = []  # will hold dicts: {handler, status, force, bar, btn}

        # Central stacked widget to switch screens
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        # Build UI screens
        self.splash_screen    = self._create_splash_screen()
        self.main_menu_screen = self._create_main_menu()
        self.force_screen     = self._create_force_screen()
        self.training_screen  = self._create_training_screen()
        self.games_screen     = self._create_games_screen()
        self.settings_screen  = self._create_settings_screen()

        # Add screens to stack
        for w in [self.splash_screen,
                  self.main_menu_screen,
                  self.force_screen,
                  self.training_screen,
                  self.games_screen,
                  self.settings_screen]:
            self.stack.addWidget(w)

        # Start on splash, then auto-switch to main menu
        self.stack.setCurrentWidget(self.splash_screen)
        QtCore.QTimer.singleShot(1500,
                                 lambda: self.stack.setCurrentWidget(self.main_menu_screen))

        # Timer to refresh force readings every 100ms
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self._update_readings)
        self.update_timer.start()

    def _create_splash_screen(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        # Logo
        logo_lbl = QtWidgets.QLabel()
        logo_path = os.path.join("assets", "ctc_logo.png")
        if os.path.isfile(logo_path):
            pix = QtGui.QPixmap(logo_path).scaled(300,300,
                                                 QtCore.Qt.KeepAspectRatio,
                                                 QtCore.Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        layout.addWidget(logo_lbl)
        # Text
        text_lbl = QtWidgets.QLabel("Produced by CTC")
        text_lbl.setAlignment(QtCore.Qt.AlignCenter)
        text_lbl.setFont(QtGui.QFont("Helvetica", 24, QtGui.QFont.Bold))
        layout.addWidget(text_lbl)
        return w

    def _create_main_menu(self):
        w = QtWidgets.QWidget()
        # Background
        bg_label = QtWidgets.QLabel(w)
        bg_path = os.path.join("assets", "homescreen.png")
        if os.path.isfile(bg_path):
            pix = QtGui.QPixmap(bg_path).scaled(self.size(),
                                                QtCore.Qt.KeepAspectRatioByExpanding)
            bg_label.setPixmap(pix)
        bg_label.setGeometry(0, 0, self.width(), self.height())
        # Transparent overlay for buttons
        overlay = QtWidgets.QWidget(bg_label)
        overlay.setStyleSheet("background: transparent;")
        overlay.setGeometry(bg_label.geometry())
        # Button styling
        btn_style = (
            "QPushButton { background-color: #1e3a5c; color: white;"
            " border-radius: 15px; padding: 12px 24px; font: bold 20px Impact; }"
            "QPushButton:hover { background-color: #155a75; }"
        )
        # Place buttons
        for idx, (text, method) in enumerate([
            ("Standard Force Measuring", self._show_force),
            ("Training Modes",             self._show_training),
            ("Mini Games",                self._show_games),
            ("Settings",                  self._show_settings),
        ]):
            btn = QtWidgets.QPushButton(text, overlay)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(method)
            y = int(self.height() * (0.3 + 0.15 * idx))
            btn.move(120, y)
        # Version label
        ver_lbl = QtWidgets.QLabel("CTC Force System v1.0", overlay)
        ver_lbl.setStyleSheet("color: white;")
        ver_lbl.move(self.width()//2 - 60, int(self.height()*0.95))
        return w

    def _create_force_screen(self):
        w = QtWidgets.QWidget()
        vlayout = QtWidgets.QVBoxLayout(w)
        # Header layout
        hlayout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Force Measurement")
        title.setFont(QtGui.QFont("Helvetica", 20, QtGui.QFont.Bold))
        title.setStyleSheet("color:white; background:#3498db; padding:10px;")
        hlayout.addWidget(title)
        back_btn = QtWidgets.QPushButton("← Back")
        back_btn.setStyleSheet("background:#2980b9; color:white; border:none; padding:5px 15px;")
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.main_menu_screen))
        hlayout.addStretch()
        hlayout.addWidget(back_btn)
        vlayout.addLayout(hlayout)
        # Create group boxes for each ESP32
        for label, handler in [("ESP32 #1", self.bt1), ("ESP32 #2", self.bt2)]:
            gb = QtWidgets.QGroupBox(label)
            gb.setFont(QtGui.QFont("Helvetica", 14, QtGui.QFont.Bold))
            glayout = QtWidgets.QVBoxLayout(gb)
            status_lbl = QtWidgets.QLabel("Status: Disconnected")
            status_lbl.setStyleSheet("color:red;")
            force_lbl  = QtWidgets.QLabel("Force: N/A")
            force_lbl.setFont(QtGui.QFont("Helvetica", 16, QtGui.QFont.Bold))
            bar = QtWidgets.QProgressBar()
            bar.setRange(0, 1500)
            btn = QtWidgets.QPushButton("Connect")
            btn.clicked.connect(lambda _: self._toggle_connection(handler,
                                  status_lbl, bar, force_lbl, btn))
            glayout.addWidget(status_lbl)
            glayout.addWidget(force_lbl)
            glayout.addWidget(bar)
            glayout.addWidget(btn)
            vlayout.addWidget(gb)
            # store references for updates
            self.force_widgets.append({
                'handler': handler,
                'status': status_lbl,
                'force': force_lbl,
                'bar': bar,
                'btn': btn
            })
        return w

    def _create_training_screen(self):
        w = QtWidgets.QWidget()
        vlayout = QtWidgets.QVBoxLayout(w)
        # Header
        hlayout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Training Modes")
        title.setFont(QtGui.QFont("Helvetica", 20, QtGui.QFont.Bold))
        title.setStyleSheet("background:#e74c3c; color:white; padding:10px;")
        hlayout.addWidget(title)
        back_btn = QtWidgets.QPushButton("← Back")
        back_btn.setStyleSheet("background:#c0392b; color:white; padding:5px 15px;")
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.main_menu_screen))
        hlayout.addStretch()
        hlayout.addWidget(back_btn)
        vlayout.addLayout(hlayout)
        msg = QtWidgets.QLabel("Training modes coming soon!")
        msg.setFont(QtGui.QFont("Helvetica", 18))
        msg.setAlignment(QtCore.Qt.AlignCenter)
        vlayout.addWidget(msg)
        return w

    def _create_games_screen(self):
        w = QtWidgets.QWidget()
        vlayout = QtWidgets.QVBoxLayout(w)
        hlayout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Mini Games")
        title.setFont(QtGui.QFont("Helvetica", 20, QtGui.QFont.Bold))
        title.setStyleSheet("background:#2ecc71; color:white; padding:10px;")
        hlayout.addWidget(title)
        back_btn = QtWidgets.QPushButton("← Back")
        back_btn.setStyleSheet("background:#27ae60; color:white; padding:5px 15px;")
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.main_menu_screen))
        hlayout.addStretch()
        hlayout.addWidget(back_btn)
        vlayout.addLayout(hlayout)
        msg = QtWidgets.QLabel("Mini games coming soon!")
        msg.setFont(QtGui.QFont("Helvetica", 18))
        msg.setAlignment(QtCore.Qt.AlignCenter)
        vlayout.addWidget(msg)
        return w

    def _create_settings_screen(self):
        w = QtWidgets.QWidget()
        vlayout = QtWidgets.QVBoxLayout(w)
        hlayout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Settings")
        title.setFont(QtGui.QFont("Helvetica", 20, QtGui.QFont.Bold))
        title.setStyleSheet("background:#9b59b6; color:white; padding:10px;")
        hlayout.addWidget(title)
        back_btn = QtWidgets.QPushButton("← Back")
        back_btn.setStyleSheet("background:#8e44ad; color:white; padding:5px 15px;")
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.main_menu_screen))
        hlayout.addStretch()
        hlayout.addWidget(back_btn)
        vlayout.addLayout(hlayout)
        form = QtWidgets.QFormLayout()
        theme_cb = QtWidgets.QComboBox()
        theme_cb.addItems(["Light", "Dark", "System"])
        form.addRow("Theme:", theme_cb)
        units_cb = QtWidgets.QComboBox()
        units_cb.addItems(["Newtons (N)", "Pounds (lbs)", "Kilograms (kg)"])
        form.addRow("Force Units:", units_cb)
        save_btn = QtWidgets.QPushButton("Save Settings")
        save_btn.setStyleSheet("background:#9b59b6; color:white; padding:10px;")
        vlayout.addLayout(form)
        vlayout.addWidget(save_btn)
        return w

    # Screen navigation methods
    def _show_force(self):       self.stack.setCurrentWidget(self.force_screen)
    def _show_training(self):    self.stack.setCurrentWidget(self.training_screen)
    def _show_games(self):       self.stack.setCurrentWidget(self.games_screen)
    def _show_settings(self):    self.stack.setCurrentWidget(self.settings_screen)

    # Connect/disconnect logic
    def _toggle_connection(self, handler, status_lbl, bar, force_lbl, btn):
        if not handler.is_connected:
            if handler.connect():
                status_lbl.setText("Status: Connected")
                status_lbl.setStyleSheet("color:green;")
                btn.setText("Disconnect")
            else:
                status_lbl.setText("Status: Connection Failed")
        else:
            handler.disconnect()
            status_lbl.setText("Status: Disconnected")
            status_lbl.setStyleSheet("color:red;")
            force_lbl.setText("Force: N/A")
            btn.setText("Connect")
            bar.setValue(0)

    # Periodic update for force readings
    def _update_readings(self):
        # First device: two sensors
        if self.bt1.is_connected:
            try:
                f1, f2 = self.bt1.get_both_force_readings()
                for idx, f in enumerate((f1, f2)):
                    widget = self.force_widgets[idx]
                    if isinstance(f, (int, float)):
                        widget['force'].setText(f"Force: {f} N")
                        widget['bar'].setValue(min(1500, max(0, int(f))))
                    else:
                        widget['force'].setText(str(f))
            except Exception as e:
                print(f"Error reading from ESP32_1: {e}")
                self.force_widgets[0]['force'].setText("Force: Error")
        # Second device (if separate)
        if self.bt2.is_connected:
            try:
                f = self.bt2.get_force_reading()
                widget = self.force_widgets[1]
                if isinstance(f, (int, float)):
                    widget['force'].setText(f"Force: {f} N")
                    widget['bar'].setValue(min(1500, max(0, int(f))))
                else:
                    widget['force'].setText(str(f))
            except Exception as e:
                print(f"Error reading from ESP32_2: {e}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
