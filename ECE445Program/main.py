import sys
import os
import random
import time
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtMultimedia import QSoundEffect
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

        # Reaction drill state
        self.reaction_active = False
        self.reaction_start_time = 0.0
        self.reaction_threshold = 10.0  # Newtons threshold

        # Prepare beep sound
        self.beep = QSoundEffect()
        beep_path = os.path.join("assets", "beep.wav")
        self.beep.setSource(QtCore.QUrl.fromLocalFile(beep_path))

        # Speed combo drill state
        self.speed_active = False
        self.speed_start_time = 0.0
        self.speed_threshold = 300.0    # Newtons threshold for speed drill
        self.speed_time_limit = 2.0    # seconds to complete each kick
        self.speed_combo = 0
        self.kick_list = ["Front Kick", "Roundhouse Kick", "Back Kick", "Front Hook Kick", "Back Hook kick", "Axe Kick", "Tornado Kick"]

        # Central stacked widget to switch screens
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        # Build UI screens
        self.splash_screen      = self._create_splash_screen()
        self.main_menu_screen  = self._create_main_menu()
        self.force_screen      = self._create_force_screen()
        self.training_screen   = self._create_training_screen()
        self.reaction_screen   = self._create_reaction_screen()
        self.power_screen      = self._create_power_screen()
        self.speed_screen      = self._create_speed_screen()
        self.games_screen      = self._create_games_screen()
        self.settings_screen   = self._create_settings_screen()

        # Add screens to stack
        for w in [
            self.splash_screen,
            self.main_menu_screen,
            self.force_screen,
            self.training_screen,
            self.reaction_screen,
            self.power_screen,
            self.speed_screen,
            self.games_screen,
            self.settings_screen
        ]:
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
        
        # Storage for force-screen widgets (clearing any previous entries)
        self.force_widgets = []
        
        # Create group boxes for each ESP32
        for esp_idx, (label, handler) in enumerate([("ESP32 #1", self.bt1), ("ESP32 #2", self.bt2)]):
            gb = QtWidgets.QGroupBox(label)
            gb.setFont(QtGui.QFont("Helvetica", 14, QtGui.QFont.Bold))
            glayout = QtWidgets.QVBoxLayout(gb)
            
            # Status label and connect button
            status_lbl = QtWidgets.QLabel("Status: Disconnected")
            status_lbl.setStyleSheet("color:red;")
            btn = QtWidgets.QPushButton("Connect")
            hlayout = QtWidgets.QHBoxLayout()
            hlayout.addWidget(status_lbl)
            hlayout.addStretch()
            hlayout.addWidget(btn)
            glayout.addLayout(hlayout)
            
            esp_widgets = []  # Store widgets for this ESP32
            
            # Create two force displays for each ESP32
            for sensor_idx in range(2):
                sensor_gb = QtWidgets.QGroupBox(f"Force Sensor #{sensor_idx+1}")
                sensor_layout = QtWidgets.QVBoxLayout(sensor_gb)
                
                force_lbl = QtWidgets.QLabel(f"Force {sensor_idx+1}: N/A")
                force_lbl.setFont(QtGui.QFont("Helvetica", 16, QtGui.QFont.Bold))
                bar = QtWidgets.QProgressBar()
                bar.setRange(0, 1500)
                
                sensor_layout.addWidget(force_lbl)
                sensor_layout.addWidget(bar)
                glayout.addWidget(sensor_gb)
                
                # Store references for this ESP32 and sensor
                widget_data = {
                    'handler': handler,
                    'esp_idx': esp_idx,
                    'sensor_idx': sensor_idx,
                    'status': status_lbl,
                    'force': force_lbl,
                    'bar': bar,
                    'btn': btn
                }
                self.force_widgets.append(widget_data)
                esp_widgets.append(widget_data)
            
            # Connect button event handling with properly captured parameters
            btn.clicked.connect(lambda checked, h=handler, s=status_lbl, w=esp_widgets, b=btn: 
                                self._toggle_connection(h, s, w, b))
            
            vlayout.addWidget(gb)
            
        return w

    def _create_training_screen(self):
        w = QtWidgets.QWidget()
        vlayout = QtWidgets.QVBoxLayout(w)
        hlayout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Training Modes")
        title.setFont(QtGui.QFont("Helvetica",20,QtGui.QFont.Bold))
        title.setStyleSheet("background:#e74c3c;color:white;padding:10px;")
        hlayout.addWidget(title)
        back = QtWidgets.QPushButton("← Back")
        back.setStyleSheet("background:#c0392b;color:white;padding:5px 15px;")
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self.main_menu_screen))
        hlayout.addStretch()
        hlayout.addWidget(back)
        vlayout.addLayout(hlayout)
        # Drill buttons
        for txt,fn in [("Reaction Drills", self._show_reaction),
                       ("Power Drill",      self._show_power),
                       ("Speed Drill",      self._show_speed)]:
            btn = QtWidgets.QPushButton(txt)
            btn.setFont(QtGui.QFont("Helvetica",18))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22;
                    color: white;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #d35400;
                }
            """)
            btn.clicked.connect(fn)
            vlayout.addWidget(btn)
        return w
    
    def _create_reaction_screen(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        lbl = QtWidgets.QLabel("Reaction Drills Mode")
        lbl.setFont(QtGui.QFont("Helvetica",24,QtGui.QFont.Bold))
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(lbl)
        start_btn = QtWidgets.QPushButton("Start")
        start_btn.setFont(QtGui.QFont("Helvetica",18))
        start_btn.clicked.connect(self._start_reaction)
        v.addWidget(start_btn, alignment=QtCore.Qt.AlignCenter)
        self.reaction_time_lbl = QtWidgets.QLabel("Reaction Time: N/A")
        self.reaction_time_lbl.setFont(QtGui.QFont("Helvetica",18))
        v.addWidget(self.reaction_time_lbl, alignment=QtCore.Qt.AlignCenter)
        back = QtWidgets.QPushButton("← Back")
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self.training_screen))
        v.addWidget(back, alignment=QtCore.Qt.AlignCenter)
        return w

    def _create_power_screen(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        lbl = QtWidgets.QLabel("Power Drill Mode")
        lbl.setFont(QtGui.QFont("Helvetica",24,QtGui.QFont.Bold))
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(lbl)
        back = QtWidgets.QPushButton("← Back")
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self.training_screen))
        v.addWidget(back, alignment=QtCore.Qt.AlignCenter)
        return w

    def _create_speed_screen(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        lbl = QtWidgets.QLabel("Speed Drill Mode")
        lbl.setFont(QtGui.QFont("Helvetica",24,QtGui.QFont.Bold))
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(lbl)
        self.kick_lbl = QtWidgets.QLabel("")
        self.kick_lbl.setFont(QtGui.QFont("Helvetica",20,QtGui.QFont.Bold))
        self.kick_lbl.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(self.kick_lbl)
        start_btn = QtWidgets.QPushButton("Start Combo")
        start_btn.setFont(QtGui.QFont("Helvetica",18))
        start_btn.clicked.connect(self._start_speed)
        v.addWidget(start_btn, alignment=QtCore.Qt.AlignCenter)
        self.combo_lbl = QtWidgets.QLabel("Combo: 0")
        self.combo_lbl.setFont(QtGui.QFont("Helvetica",18))
        self.combo_lbl.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(self.combo_lbl)
        back = QtWidgets.QPushButton("← Back")
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self.training_screen))
        v.addWidget(back, alignment=QtCore.Qt.AlignCenter)
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
    def _show_reaction(self):    self.stack.setCurrentWidget(self.reaction_screen)
    def _show_power(self):       self.stack.setCurrentWidget(self.power_screen)
    def _show_speed(self):       self.stack.setCurrentWidget(self.speed_screen)
    def _show_games(self):       self.stack.setCurrentWidget(self.games_screen)
    def _show_settings(self):    self.stack.setCurrentWidget(self.settings_screen)

    def _start_reaction(self):
        # Clear previous result
        self.reaction_time_lbl.setText("Reaction Time: ---")
        # Schedule beep after random delay
        delay_ms = int(random.uniform(1.0, 3.0) * 1000)
        QtCore.QTimer.singleShot(delay_ms, self._trigger_beep)

    def _trigger_beep(self):
        # Play beep and start timing
        self.beep.play()
        self.reaction_start_time = time.perf_counter()
        self.reaction_active = True

    def _start_speed(self):
        # reset combo and begin first kick
        self.speed_combo = 0
        self.combo_lbl.setText("Combo: 0")
        self._next_kick()

    def _next_kick(self):
        kick = random.choice(self.kick_list)
        self.kick_lbl.setText(f"Perform: {kick}!")
        self.speed_start_time = time.perf_counter()
        self.speed_active = True

    # Connect/disconnect logic
    def _toggle_connection(self, handler, status_lbl, widgets, btn):
        if not handler.is_connected:
            if handler.connect():
                status_lbl.setText("Status: Connected")
                status_lbl.setStyleSheet("color:green;")
                btn.setText("Disconnect")
                for widget in widgets:
                    widget['force'].setText(f"Force {widget['sensor_idx']+1}: N/A")
                    widget['bar'].setValue(0)
            else:
                status_lbl.setText("Status: Connection Failed")
        else:
            handler.disconnect()
            status_lbl.setText("Status: Disconnected")
            status_lbl.setStyleSheet("color:red;")
            btn.setText("Connect")
            for widget in widgets:
                widget['force'].setText(f"Force {widget['sensor_idx']+1}: N/A")
                widget['bar'].setValue(0)

    # Periodic update for force readings
    def _update_readings(self):
        # Group widgets by ESP32
        widgets_by_esp = {}
        for widget in self.force_widgets:
            esp_idx = widget['esp_idx']
            if esp_idx not in widgets_by_esp:
                widgets_by_esp[esp_idx] = []
            widgets_by_esp[esp_idx].append(widget)
        
        # Update ESP32 #1
        if self.bt1.is_connected and 0 in widgets_by_esp:
            try:
                # Get both force readings from ESP32 #1
                force1, force2 = self.bt1.get_both_force_readings()
                forces = [force1, force2]
                
                # Update widgets for ESP32 #1
                for widget in widgets_by_esp[0]:
                    sensor_idx = widget['sensor_idx']
                    force = forces[sensor_idx]
                    
                    if isinstance(force, (int, float)):
                        widget['force'].setText(f"Force {sensor_idx+1}: {force} N")
                        widget['bar'].setValue(min(1500, max(0, int(force))))
                    else:
                        widget['force'].setText(f"Force {sensor_idx+1}: {force}")
            except Exception as e:
                print(f"Error reading from ESP32_1: {e}")
                for widget in widgets_by_esp[0]:
                    sensor_idx = widget['sensor_idx']
                    widget['force'].setText(f"Force {sensor_idx+1}: Error")
        
        # Update ESP32 #2
        if self.bt2.is_connected and 1 in widgets_by_esp:
            try:
                # Get both force readings from ESP32 #2
                force1, force2 = self.bt2.get_both_force_readings()
                forces = [force1, force2]
                
                # Update widgets for ESP32 #2
                for widget in widgets_by_esp[1]:
                    sensor_idx = widget['sensor_idx']
                    force = forces[sensor_idx]
                    
                    if isinstance(force, (int, float)):
                        widget['force'].setText(f"Force {sensor_idx+1}: {force} N")
                        widget['bar'].setValue(min(1500, max(0, int(force))))
                    else:
                        widget['force'].setText(f"Force {sensor_idx+1}: {force}")
            except Exception as e:
                print(f"Error reading from ESP32_2: {e}")
                for widget in widgets_by_esp[1]:
                    sensor_idx = widget['sensor_idx']
                    widget['force'].setText(f"Force {sensor_idx+1}: Error")

        # Reaction drill detection
        if self.stack.currentWidget() == self.reaction_screen and self.reaction_active:
            if self.force_widgets:
                val = self.force_widgets[0]['bar'].value()
                if val >= self.reaction_threshold:
                    rt_ms = (time.perf_counter() - self.reaction_start_time) * 1000
                    self.reaction_time_lbl.setText(f"Reaction Time: {rt_ms:.0f} ms")
                    self.reaction_active = False
                    
        # Speed combo drill detection
        if self.stack.currentWidget() == self.speed_screen and self.speed_active:
            if self.force_widgets:
                val = self.force_widgets[0]['bar'].value()
                elapsed = time.perf_counter() - self.speed_start_time
                if val >= self.speed_threshold:
                    self.speed_combo += 1
                    self.combo_lbl.setText(f"Combo: {self.speed_combo}")
                    self._next_kick()
                elif elapsed > self.speed_time_limit:
                    self.kick_lbl.setText("Drill ended!")
                    self.speed_active = False

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
