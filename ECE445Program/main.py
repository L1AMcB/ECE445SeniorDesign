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
        
        # Last valid force readings (above 200N)
        self.last_valid_forces = {
            0: {'force1': None, 'force2': None, 'max_force': None, 'accuracy': None},  # ESP32 #1
            1: {'force1': None, 'force2': None, 'max_force': None, 'accuracy': None}   # ESP32 #2
        }
        
        # Kick detection and timing
        self.kick_timing = {
            0: {'active': False, 'start_time': None, 'best_force': 0, 'best_accuracy': 0},  # ESP32 #1
            1: {'active': False, 'start_time': None, 'best_force': 0, 'best_accuracy': 0}   # ESP32 #2
        }
        self.kick_timeout = 1000  # 1000 milliseconds timeout for a kick sequence

        # Reaction drill state
        self.reaction_active = False
        self.reaction_start_time = 0.0
        self.reaction_threshold = 300.0  # Newtons threshold

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
            self.speed_screen,
            self.games_screen,
            self.settings_screen
        ]:
            self.stack.addWidget(w)

        # Start on splash, then auto-switch to main menu
        self.stack.setCurrentWidget(self.splash_screen)
        
        # Animation setup for splash screen
        self.splash_logo = self.splash_screen.logo_label
        opacity_effect = QtWidgets.QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0)
        self.splash_logo.setGraphicsEffect(opacity_effect)
        
        # Fade in animation
        self.fade_in = QtCore.QPropertyAnimation(self.splash_logo.graphicsEffect(), b"opacity")
        self.fade_in.setDuration(1000)  # 1 second
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.start()
        
        # Wait for fade-in, then start fade-out
        QtCore.QTimer.singleShot(2500, self._start_fade_out)
        
        # Timer to refresh force readings more frequently (10ms for 100Hz polling)
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.setInterval(10)
        self.update_timer.timeout.connect(self._update_readings)
        self.update_timer.start()

    def _create_splash_screen(self):
        w = QtWidgets.QWidget()
        w.setStyleSheet("background-color: black;")
        layout = QtWidgets.QVBoxLayout(w)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        # Logo
        logo_lbl = QtWidgets.QLabel()
        logo_path = os.path.join("assets", "ctc_logo.png")
        if os.path.isfile(logo_path):
            pix = QtGui.QPixmap(logo_path).scaled(600,600,
                                                 QtCore.Qt.KeepAspectRatio,
                                                 QtCore.Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        layout.addWidget(logo_lbl)
        # Remove text label - we just want the logo
        
        # Store reference to the logo label
        w.logo_label = logo_lbl
        
        return w

    def _create_main_menu(self):
        w = QtWidgets.QWidget()
        w.setMinimumSize(100, 100)
        main_layout = QtWidgets.QGridLayout(w)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Background Label setup
        bg_label = QtWidgets.QLabel()
        bg_path = os.path.join("assets", "homescreen.png")
        if os.path.isfile(bg_path):
            pix = QtGui.QPixmap(bg_path)
            bg_label.setPixmap(pix)
            bg_label.setScaledContents(True)
        main_layout.addWidget(bg_label, 0, 0)

        # Container for buttons and version label
        content_container = QtWidgets.QWidget()
        content_container.setStyleSheet("background: transparent;")
        content_layout = QtWidgets.QVBoxLayout(content_container)
        content_layout.setContentsMargins(120, 50, 120, 30)

        # — New title label inserted here —
        title_lbl = QtWidgets.QLabel("Electronic Martial Arts Force Sensor")
        title_lbl.setFont(QtGui.QFont("Helvetica", 28, QtGui.QFont.Bold))
        title_lbl.setStyleSheet("color: white;")
        title_lbl.setAlignment(QtCore.Qt.AlignCenter)
        content_layout.addWidget(title_lbl)
        content_layout.addSpacing(40)
        # — end title —

        # Button styling
        btn_style = (
            "QPushButton { background-color: #1e3a5c; color: white;"
            " border-radius: 15px; padding: 12px 24px; font: bold 20px Impact; }"
            "QPushButton:hover { background-color: #155a75; }"
        )

        content_layout.addStretch(2)

        for idx, (text, method) in enumerate([
            ("Standard Force Measuring", self._show_force),
            ("Training Modes",           self._show_training),
            ("Mini Games",              self._show_games),
            ("Settings",                self._show_settings),
        ]):
            btn = QtWidgets.QPushButton(text)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(method)
            content_layout.addWidget(btn, alignment=QtCore.Qt.AlignLeft)
            if idx < 3:
                content_layout.addSpacing(20)

        content_layout.addStretch(3)

        # Version label
        ver_lbl = QtWidgets.QLabel("CTC Force System v1.0")
        ver_lbl.setStyleSheet("color: white; background: rgba(0,0,0,0.5); padding: 2px;")
        content_layout.addWidget(ver_lbl, alignment=QtCore.Qt.AlignCenter)

        main_layout.addWidget(content_container, 0, 0)
        return w


    # def _create_main_menu(self):
    #     w = QtWidgets.QWidget()
    #     w.setMinimumSize(100, 100) # Allow the widget to shrink more
    #     # Create a main layout that will hold everything
    #     main_layout = QtWidgets.QGridLayout(w) # Use GridLayout for overlaying
    #     main_layout.setContentsMargins(0, 0, 0, 0)
    #     main_layout.setSpacing(0)


    #     # Background Label setup
    #     bg_label = QtWidgets.QLabel()
    #     bg_path = os.path.join("assets", "homescreen.png")
    #     if os.path.isfile(bg_path):
    #         pix = QtGui.QPixmap(bg_path) # Load pixmap without initial scaling
    #         bg_label.setPixmap(pix)
    #         bg_label.setScaledContents(True) # Allow pixmap to scale with label size

    #     # Add bg_label to cover the whole grid cell (0,0)
    #     main_layout.addWidget(bg_label, 0, 0)

    #     # Container for buttons and version label (will be placed on top of bg_label)
    #     content_container = QtWidgets.QWidget()
    #     content_container.setStyleSheet("background: transparent;") # Make it transparent
    #     content_layout = QtWidgets.QVBoxLayout(content_container)
    #     content_layout.setContentsMargins(120, 50, 120, 30) # Adjust margins as needed

    #     # Button styling
    #     btn_style = (
    #         "QPushButton { background-color: #1e3a5c; color: white;"
    #         " border-radius: 15px; padding: 12px 24px; font: bold 20px Impact; }"
    #         "QPushButton:hover { background-color: #155a75; }"
    #     )

    #     content_layout.addStretch(2) # Add stretch above buttons

    #     # Place buttons using the content layout
    #     for idx, (text, method) in enumerate([
    #         ("Standard Force Measuring", self._show_force),
    #         ("Training Modes",             self._show_training),
    #         ("Mini Games",                self._show_games),
    #         ("Settings",                  self._show_settings),
    #     ]):
    #         btn = QtWidgets.QPushButton(text)
    #         btn.setStyleSheet(btn_style)
    #         btn.clicked.connect(method)
    #         content_layout.addWidget(btn, alignment=QtCore.Qt.AlignLeft)
    #         if idx < 3: # Add spacing between buttons
    #             content_layout.addSpacing(20)

    #     content_layout.addStretch(3) # Add stretch below buttons

    #     # Version label
    #     ver_lbl = QtWidgets.QLabel("CTC Force System v1.0")
    #     ver_lbl.setStyleSheet("color: white; background: rgba(0,0,0,0.5); padding: 2px;") # Semi-transparent background for visibility
    #     content_layout.addWidget(ver_lbl, alignment=QtCore.Qt.AlignCenter)

    #     # Add the content container on top of the background label in the grid
    #     main_layout.addWidget(content_container, 0, 0)

    #     return w

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
            
            # Container for force and accuracy display (right side of ESP32 group)
            metrics_container = QtWidgets.QWidget()
            metrics_layout = QtWidgets.QHBoxLayout(metrics_container)
            
            # Force value display
            force_value_container = QtWidgets.QWidget()
            force_value_layout = QtWidgets.QVBoxLayout(force_value_container)
            
            force_value_title = QtWidgets.QLabel("Force:")
            force_value_title.setFont(QtGui.QFont("Helvetica", 12, QtGui.QFont.Bold))
            force_value = QtWidgets.QLabel("N/A")
            force_value.setFont(QtGui.QFont("Helvetica", 16, QtGui.QFont.Bold))
            force_value.setAlignment(QtCore.Qt.AlignCenter)
            
            force_value_layout.addWidget(force_value_title, alignment=QtCore.Qt.AlignCenter)
            force_value_layout.addWidget(force_value, alignment=QtCore.Qt.AlignCenter)
            force_value_layout.setContentsMargins(20, 0, 20, 0)
            
            # Accuracy display
            accuracy_container = QtWidgets.QWidget()
            accuracy_layout = QtWidgets.QVBoxLayout(accuracy_container)
            
            accuracy_title = QtWidgets.QLabel("Accuracy:")
            accuracy_title.setFont(QtGui.QFont("Helvetica", 12, QtGui.QFont.Bold))
            accuracy_value = QtWidgets.QLabel("N/A")
            accuracy_value.setFont(QtGui.QFont("Helvetica", 16, QtGui.QFont.Bold))
            accuracy_value.setAlignment(QtCore.Qt.AlignCenter)
            
            accuracy_layout.addWidget(accuracy_title, alignment=QtCore.Qt.AlignCenter)
            accuracy_layout.addWidget(accuracy_value, alignment=QtCore.Qt.AlignCenter)
            accuracy_layout.setContentsMargins(20, 0, 20, 0)
            
            # Add force and accuracy to metrics layout
            metrics_layout.addWidget(force_value_container)
            metrics_layout.addWidget(accuracy_container)
            
            # Main layout for ESP sensors and metrics
            main_layout = QtWidgets.QHBoxLayout()
            
            # Left side: Sensors container (50% of space)
            sensors_container = QtWidgets.QWidget()
            sensors_layout = QtWidgets.QVBoxLayout(sensors_container)
            
            esp_widgets = []  # Store widgets for this ESP32
            
            # Create two force displays for each ESP32
            for sensor_idx in range(2):
                sensor_gb = QtWidgets.QGroupBox(f"Force Sensor #{sensor_idx+1}")
                sensor_layout = QtWidgets.QVBoxLayout(sensor_gb)
                
                force_lbl = QtWidgets.QLabel(f"Force {sensor_idx+1}:")
                force_lbl.setFont(QtGui.QFont("Helvetica", 12))
                bar = QtWidgets.QProgressBar()
                bar.setRange(0, 1500)
                bar.setFixedHeight(30)  # Make bar twice as thick
                
                sensor_layout.addWidget(force_lbl)
                sensor_layout.addWidget(bar)
                
                sensors_layout.addWidget(sensor_gb)
                
                # Store references for this ESP32 and sensor
                widget_data = {
                    'handler': handler,
                    'esp_idx': esp_idx,
                    'sensor_idx': sensor_idx,
                    'status': status_lbl,
                    'force': force_lbl,
                    'force_value': force_value,  # Same for both sensors on this ESP
                    'accuracy_value': accuracy_value,  # Same for both sensors on this ESP
                    'bar': bar,
                    'btn': btn
                }
                self.force_widgets.append(widget_data)
                esp_widgets.append(widget_data)
            
            # Add sensors and metrics to main layout with stretching
            main_layout.addWidget(sensors_container, 5)  # 50%
            main_layout.addWidget(metrics_container, 4)  # 50% (split between force and accuracy)
            
            glayout.addLayout(main_layout)
            
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
        
        # Games container
        games_layout = QtWidgets.QVBoxLayout()
        games_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        # Kicking School button
        kicking_btn = QtWidgets.QPushButton("Kicking School")
        kicking_btn.setFont(QtGui.QFont("Helvetica", 16))
        kicking_btn.setStyleSheet("background:#27ae60; color:white; padding:15px 30px;")
        kicking_btn.setMinimumWidth(300)
        kicking_btn.clicked.connect(self._show_kicking_school)
        games_layout.addWidget(kicking_btn)
        
        # More game options will go here
        
        vlayout.addLayout(games_layout)
        vlayout.addStretch()
        return w
        
    def _create_kicking_school_screen(self):
        w = QtWidgets.QWidget()
        vlayout = QtWidgets.QVBoxLayout(w)
        
        # Header
        hlayout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Kicking School")
        title.setFont(QtGui.QFont("Helvetica", 20, QtGui.QFont.Bold))
        title.setStyleSheet("background:#2ecc71; color:white; padding:10px;")
        hlayout.addWidget(title)
        back_btn = QtWidgets.QPushButton("← Back")
        back_btn.setStyleSheet("background:#27ae60; color:white; padding:5px 15px;")
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.games_screen))
        hlayout.addStretch()
        hlayout.addWidget(back_btn)
        vlayout.addLayout(hlayout)
        
        # Grade display (top middle)
        grade_container = QtWidgets.QWidget()
        grade_layout = QtWidgets.QVBoxLayout(grade_container)
        
        grade_title = QtWidgets.QLabel("Grade")
        grade_title.setFont(QtGui.QFont("Helvetica", 18, QtGui.QFont.Bold))
        grade_title.setAlignment(QtCore.Qt.AlignCenter)
        
        self.grade_value = QtWidgets.QLabel("--")
        self.grade_value.setFont(QtGui.QFont("Impact", 72, QtGui.QFont.Bold))
        self.grade_value.setAlignment(QtCore.Qt.AlignCenter)
        self.grade_value.setStyleSheet("color:#27ae60;")
        
        grade_layout.addWidget(grade_title)
        grade_layout.addWidget(self.grade_value)
        
        # Instructions
        instructions = QtWidgets.QLabel("Kick the force paddle to get a grade.\nThe grade is based on force and accuracy.")
        instructions.setFont(QtGui.QFont("Helvetica", 14))
        instructions.setAlignment(QtCore.Qt.AlignCenter)
        
        # Container for force and accuracy (bottom row)
        metrics_container = QtWidgets.QWidget()
        metrics_layout = QtWidgets.QHBoxLayout(metrics_container)
        
        # Force display (bottom left)
        force_container = QtWidgets.QGroupBox("Force")
        force_container.setFont(QtGui.QFont("Helvetica", 14, QtGui.QFont.Bold))
        force_layout = QtWidgets.QVBoxLayout(force_container)
        
        self.force_label = QtWidgets.QLabel("0 N")
        self.force_label.setFont(QtGui.QFont("Helvetica", 24, QtGui.QFont.Bold))
        self.force_label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.force_percent = QtWidgets.QLabel("0%")
        self.force_percent.setFont(QtGui.QFont("Helvetica", 18))
        self.force_percent.setAlignment(QtCore.Qt.AlignCenter)
        
        force_layout.addWidget(self.force_label)
        force_layout.addWidget(self.force_percent)
        
        # Accuracy display (bottom right)
        accuracy_container = QtWidgets.QGroupBox("Accuracy")
        accuracy_container.setFont(QtGui.QFont("Helvetica", 14, QtGui.QFont.Bold))
        accuracy_layout = QtWidgets.QVBoxLayout(accuracy_container)
        
        self.accuracy_label = QtWidgets.QLabel("0%")
        self.accuracy_label.setFont(QtGui.QFont("Helvetica", 24, QtGui.QFont.Bold))
        self.accuracy_label.setAlignment(QtCore.Qt.AlignCenter)
        
        accuracy_layout.addWidget(self.accuracy_label)
        
        # Add containers to metrics layout
        metrics_layout.addWidget(force_container)
        metrics_layout.addWidget(accuracy_container)
        
        # Device selection
        device_container = QtWidgets.QWidget()
        device_layout = QtWidgets.QHBoxLayout(device_container)
        
        device_label = QtWidgets.QLabel("Select Device:")
        device_label.setFont(QtGui.QFont("Helvetica", 14))
        
        self.device_combo = QtWidgets.QComboBox()
        self.device_combo.addItems(["ESP32 #1", "ESP32 #2"])
        self.device_combo.setFont(QtGui.QFont("Helvetica", 14))
        
        device_layout.addWidget(device_label)
        device_layout.addWidget(self.device_combo)
        
        # Add all elements to main layout
        vlayout.addWidget(grade_container)
        vlayout.addWidget(instructions)
        vlayout.addStretch()
        vlayout.addWidget(device_container)
        vlayout.addWidget(metrics_container)
        
        return w

    # Screen navigation methods
    def _show_force(self):       self.stack.setCurrentWidget(self.force_screen)
    def _show_training(self):    self.stack.setCurrentWidget(self.training_screen)
    def _show_reaction(self):    self.stack.setCurrentWidget(self.reaction_screen)
    def _show_speed(self):       self.stack.setCurrentWidget(self.speed_screen)
    def _show_games(self):       self.stack.setCurrentWidget(self.games_screen)
    def _show_settings(self):    self.stack.setCurrentWidget(self.settings_screen)

    def _start_reaction(self):
        # Reset last force so old values don't trigger immediately
        self.last_valid_forces[0]['max_force'] = None
        self.last_valid_forces[0]['accuracy'] = None

        self.reaction_time_lbl.setText("Reaction Time: ---")
        delay_ms = int(random.uniform(1.0, 3.0) * 1000)
        QtCore.QTimer.singleShot(delay_ms, self._trigger_beep)

    def _trigger_beep(self):
        # Play beep and start timing
        self.beep.play()
        self.reaction_start_time = time.perf_counter()
        self.reaction_active = True

    def _start_speed(self):
            # Clear any old force reading so it won't immediately trigger
        self.last_valid_forces[0]['max_force'] = None
        self.last_valid_forces[0]['accuracy']  = None

        # Reset combo count and restore the default time limit
        self.speed_combo       = 0
        self.speed_time_limit  = 2.0
        self.combo_lbl.setText("Combo: 0")

        # Kick off the first prompt
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
        
    def _show_kicking_school(self):
        # Create kicking school screen if it doesn't exist
        if not hasattr(self, 'kicking_school_screen'):
            self.kicking_school_screen = self._create_kicking_school_screen()
            self.stack.addWidget(self.kicking_school_screen)
            
        # Set initial display values based on last valid force if available
        esp_idx = 0  # Default to first ESP32
        if self.last_valid_forces[esp_idx]['max_force'] is not None and self.last_valid_forces[esp_idx]['max_force'] >= 220:
            max_force = self.last_valid_forces[esp_idx]['max_force']
            raw_accuracy = self.last_valid_forces[esp_idx]['accuracy'] # Get raw accuracy

            # Apply the curve
            adjusted_accuracy = round(100 * (raw_accuracy / 100) ** 1.7)

            # Calculate force percentage (200N = 20%, 1000N = 100%, >1000N can exceed 100%)
            force_percent = min(120, max(0, (max_force / 1000) * 100))

            # Calculate grade as average of force percent and ADJUSTED accuracy
            grade_percent = (force_percent + adjusted_accuracy) / 2

            # Determine letter grade with new thresholds
            letter_grade = "F"
            if grade_percent >= 80:
                letter_grade = "A"
            elif grade_percent >= 65:
                letter_grade = "B"
            elif grade_percent >= 55:
                letter_grade = "C"
            elif grade_percent >= 40:
                letter_grade = "D"
                
            self.grade_value.setText(letter_grade)
            self.force_label.setText(f"{max_force} N")
            self.force_percent.setText(f"{force_percent:.1f}%")
            self.accuracy_label.setText(f"{adjusted_accuracy}%")
            
            # Set grade color
            grade_colors = {
                "A": "#27ae60",  # Green
                "B": "#2980b9",  # Blue
                "C": "#f39c12",  # Orange
                "D": "#e67e22",  # Dark Orange
                "F": "#e74c3c",  # Red
            }
            self.grade_value.setStyleSheet(f"color:{grade_colors[letter_grade]};")

        else:
            # No valid readings yet
            self.grade_value.setText("--")
            self.force_label.setText("0 N")
            self.force_percent.setText("0%")
            self.accuracy_label.setText("0%")
            
        # Show the screen
        self.stack.setCurrentWidget(self.kicking_school_screen)
        
        # Connect device selection change event
        self.device_combo.currentIndexChanged.connect(self._update_kicking_device)
        
        # Start monitoring for kicks
        self._update_kicking_device(self.device_combo.currentIndex())
    
    def _update_kicking_device(self, index):
        # Select the appropriate Bluetooth handler based on combo box selection
        self.active_kicking_device = self.bt1 if index == 0 else self.bt2
        self.active_kicking_esp_idx = index
        
        # Check if selected device is connected
        if not self.active_kicking_device.is_connected:
            self.grade_value.setText("--")
            self.force_label.setText("Not Connected")
            self.force_percent.setText("--")
            self.accuracy_label.setText("--")
        else:
            # If we have valid readings for this device, show them
            esp_idx = self.active_kicking_esp_idx
            if self.last_valid_forces[esp_idx]['max_force'] is not None and self.last_valid_forces[esp_idx]['max_force'] >= 220:
                # Use existing values
                max_force = self.last_valid_forces[esp_idx]['max_force']
                raw_accuracy = self.last_valid_forces[esp_idx]['accuracy'] # Get raw accuracy

                # Apply the curve
                adjusted_accuracy = round(100 * (raw_accuracy / 100) ** 1.7)

                # Calculate force percentage (200N = 20%, 1000N = 100%, >1000N can exceed 100%)
                force_percent = min(120, max(0, (max_force / 1000) * 100))

                # Calculate grade as average of force percent and ADJUSTED accuracy
                grade_percent = (force_percent + adjusted_accuracy) / 2

                # Determine letter grade with new thresholds
                letter_grade = "F"
                if grade_percent >= 80:
                    letter_grade = "A"
                elif grade_percent >= 65:
                    letter_grade = "B"
                elif grade_percent >= 55:
                    letter_grade = "C"
                elif grade_percent >= 40:
                    letter_grade = "D"
                    
                self.grade_value.setText(letter_grade)
                self.force_label.setText(f"{max_force} N")
                self.force_percent.setText(f"{force_percent:.1f}%")
                self.accuracy_label.setText(f"{adjusted_accuracy}%")
                
                # Set grade color
                grade_colors = {
                    "A": "#27ae60",  # Green
                    "B": "#2980b9",  # Blue
                    "C": "#f39c12",  # Orange
                    "D": "#e67e22",  # Dark Orange
                    "F": "#e74c3c",  # Red
                }
                self.grade_value.setStyleSheet(f"color:{grade_colors[letter_grade]};")
            else:
                # No valid readings yet for this device
                self.grade_value.setText("Ready")
                self.force_label.setText("0 N")
                self.force_percent.setText("0%")
                self.accuracy_label.setText("0%")
    
    def _update_readings(self):
        # Group widgets by ESP32
        widgets_by_esp = {}
        for widget in self.force_widgets:
            esp_idx = widget['esp_idx']
            if esp_idx not in widgets_by_esp:
                widgets_by_esp[esp_idx] = []
            widgets_by_esp[esp_idx].append(widget)
        
        # Current time for kick timing
        current_time = QtCore.QTime.currentTime().msecsSinceStartOfDay()
        
        # Update ESP32 #1
        if self.bt1.is_connected and 0 in widgets_by_esp:
            try:
                # Get both force readings and time since last detection from ESP32 #1
                force1, force2, time_since_last, time_since_hit = self.bt1.get_both_force_readings()
                
                # Check if readings are valid numbers
                if isinstance(force1, (int, float)) and isinstance(force2, (int, float)):
                    # Apply calibration factor to force1 which reads consistently lower
                    # This ensures compatibility even if the ESP32 firmware hasn't been updated
                    force2 *= 1.35
                    
                    # Calculate current max force
                    max_force = max(force1, force2)
                    
                    # Calculate accuracy if at least one reading is above threshold
                    if max_force >= 220:
                        accuracy = round((min(force1, force2) / max_force * 100))
                    else:
                        # If we have valid past readings, keep using that accuracy
                        accuracy = self.last_valid_forces[0]['accuracy'] if self.last_valid_forces[0]['accuracy'] is not None else 100
                    
                    # Only update display and tracking if we have a real hit (above threshold)
                    if max_force >= 220:
                        # Update last valid forces with current readings for any hit above 200N
                        self.last_valid_forces[0]['force1'] = force1
                        self.last_valid_forces[0]['force2'] = force2
                        self.last_valid_forces[0]['max_force'] = max_force
                        self.last_valid_forces[0]['accuracy'] = accuracy
                        # Store the time since last message for this hit
                        self.last_valid_forces[0]['time_since_last'] = time_since_last
                        # Store the time since hit detection for this hit
                        self.last_valid_forces[0]['time_since_hit'] = time_since_hit
                    
                    # Always use last valid max force for display force
                    if self.last_valid_forces[0]['max_force'] is not None:
                        display_force = self.last_valid_forces[0]['max_force']
                        display_force1 = self.last_valid_forces[0]['force1']
                        display_force2 = self.last_valid_forces[0]['force2']
                        # Get raw accuracy and apply the curve for display
                        raw_accuracy = self.last_valid_forces[0]['accuracy']
                        display_accuracy = round(100 * (raw_accuracy / 100) ** 1.7) if raw_accuracy is not None else 0 # Apply curve here
                    else:
                        display_force = 0
                        display_force1 = 0
                        display_force2 = 0
                        display_accuracy = 0
                    
                    # Update widgets for ESP32 #1 with individual sensor readings
                    for widget in widgets_by_esp[0]:
                        sensor_idx = widget['sensor_idx']
                        widget['force'].setText(f"Force {sensor_idx+1}:")
                        
                        # Set correct force value for each sensor's bar
                        if sensor_idx == 0:
                            widget['bar'].setValue(min(1500, max(0, int(display_force1))))
                        else:
                            widget['bar'].setValue(min(1500, max(0, int(display_force2))))
                            
                        # Both widgets show the same max force value and accuracy
                        widget['force_value'].setText(f"{display_force} N")
                        widget['accuracy_value'].setText(f"{display_accuracy}%")
                else:
                    # Invalid readings - but don't reset display
                    # Keep displaying last valid reading
                    if self.last_valid_forces[0]['max_force'] is not None:
                        display_force = self.last_valid_forces[0]['max_force']
                        display_force1 = self.last_valid_forces[0]['force1']
                        display_force2 = self.last_valid_forces[0]['force2']
                        # Get raw accuracy and apply the curve for display
                        raw_accuracy = self.last_valid_forces[0]['accuracy']
                        display_accuracy = round(100 * (raw_accuracy / 100) ** 1.7) if raw_accuracy is not None else 0 # Apply curve here
                        
                        for widget in widgets_by_esp[0]:
                            sensor_idx = widget['sensor_idx']
                            widget['force'].setText(f"Force {sensor_idx+1}:")
                            
                            # Set correct force value for each sensor's bar
                            if sensor_idx == 0:
                                widget['bar'].setValue(min(1500, max(0, int(display_force1))))
                            else:
                                widget['bar'].setValue(min(1500, max(0, int(display_force2))))
                            
                            # Both widgets show the same max force value and accuracy
                            widget['force_value'].setText(f"{display_force} N")
                            widget['accuracy_value'].setText(f"{display_accuracy}%")
                    else:
                        for widget in widgets_by_esp[0]:
                            sensor_idx = widget['sensor_idx']
                            widget['force'].setText(f"Force {sensor_idx+1}:")
                            widget['force_value'].setText("N/A")
                            widget['accuracy_value'].setText("N/A")
            except Exception as e:
                print(f"Error reading from ESP32_1: {e}")
                for widget in widgets_by_esp[0]:
                    sensor_idx = widget['sensor_idx']
                    widget['force'].setText(f"Force {sensor_idx+1}:")
                    widget['force_value'].setText("Error")
                    widget['accuracy_value'].setText("N/A")
        
        # Update ESP32 #2
        if self.bt2.is_connected and 1 in widgets_by_esp:
            try:
                # Get both force readings and time since last detection from ESP32 #2
                force1, force2, time_since_last, time_since_hit = self.bt2.get_both_force_readings()
                
                # Check if readings are valid numbers
                if isinstance(force1, (int, float)) and isinstance(force2, (int, float)):
                    # Apply calibration factor to force1 which reads consistently lower
                    # This ensures compatibility even if the ESP32 firmware hasn't been updated
                    force2 *= 1.35
                    
                    # Calculate current max force
                    max_force = max(force1, force2)
                    
                    # Calculate accuracy if at least one reading is above threshold
                    if max_force >= 220:
                        accuracy = round((min(force1, force2) / max_force * 100))
                    else:
                        # If we have valid past readings, keep using that accuracy
                        accuracy = self.last_valid_forces[1]['accuracy'] if self.last_valid_forces[1]['accuracy'] is not None else 100
                    
                    # Only update display and tracking if we have a real hit (above threshold)
                    if max_force >= 220:
                        # Update last valid forces with current readings for any hit above 200N
                        self.last_valid_forces[1]['force1'] = force1
                        self.last_valid_forces[1]['force2'] = force2
                        self.last_valid_forces[1]['max_force'] = max_force
                        self.last_valid_forces[1]['accuracy'] = accuracy
                        # Store the time since last message for this hit
                        self.last_valid_forces[1]['time_since_last'] = time_since_last
                        # Store the time since hit detection for this hit
                        self.last_valid_forces[1]['time_since_hit'] = time_since_hit
                    
                    # Always use last valid max force for display
                    if self.last_valid_forces[1]['max_force'] is not None:
                        display_force = self.last_valid_forces[1]['max_force']
                        display_force1 = self.last_valid_forces[1]['force1']
                        display_force2 = self.last_valid_forces[1]['force2']
                        # Get raw accuracy and apply the curve for display
                        raw_accuracy = self.last_valid_forces[1]['accuracy']
                        display_accuracy = round(100 * (raw_accuracy / 100) ** 1.7) if raw_accuracy is not None else 0 # Apply curve here
                    else:
                        display_force = 0
                        display_force1 = 0
                        display_force2 = 0
                        display_accuracy = 0
                    
                    # Update widgets for ESP32 #2 with individual sensor readings
                    for widget in widgets_by_esp[1]:
                        sensor_idx = widget['sensor_idx']
                        widget['force'].setText(f"Force {sensor_idx+1}:")
                        
                        # Set correct force value for each sensor's bar
                        if sensor_idx == 0:
                            widget['bar'].setValue(min(1500, max(0, int(display_force1))))
                        else:
                            widget['bar'].setValue(min(1500, max(0, int(display_force2))))
                            
                        # Both widgets show the same max force value and accuracy
                        widget['force_value'].setText(f"{display_force} N")
                        widget['accuracy_value'].setText(f"{display_accuracy}%")
                else:
                    # Invalid readings - but don't reset display
                    # Keep displaying last valid reading
                    if self.last_valid_forces[1]['max_force'] is not None:
                        display_force = self.last_valid_forces[1]['max_force']
                        display_force1 = self.last_valid_forces[1]['force1']
                        display_force2 = self.last_valid_forces[1]['force2']
                        # Get raw accuracy and apply the curve for display
                        raw_accuracy = self.last_valid_forces[1]['accuracy']
                        display_accuracy = round(100 * (raw_accuracy / 100) ** 1.7) if raw_accuracy is not None else 0 # Apply curve here
                        
                        for widget in widgets_by_esp[1]:
                            sensor_idx = widget['sensor_idx']
                            widget['force'].setText(f"Force {sensor_idx+1}:")
                            
                            # Set correct force value for each sensor's bar
                            if sensor_idx == 0:
                                widget['bar'].setValue(min(1500, max(0, int(display_force1))))
                            else:
                                widget['bar'].setValue(min(1500, max(0, int(display_force2))))
                            
                            # Both widgets show the same max force value and accuracy
                            widget['force_value'].setText(f"{display_force} N")
                            widget['accuracy_value'].setText(f"{display_accuracy}%")
                    else:
                        for widget in widgets_by_esp[1]:
                            sensor_idx = widget['sensor_idx']
                            widget['force'].setText(f"Force {sensor_idx+1}:")
                            widget['force_value'].setText("N/A")
                            widget['accuracy_value'].setText("N/A")
            except Exception as e:
                print(f"Error reading from ESP32_2: {e}")
                for widget in widgets_by_esp[1]:
                    sensor_idx = widget['sensor_idx']
                    widget['force'].setText(f"Force {sensor_idx+1}:")
                    widget['force_value'].setText("Error")
                    widget['accuracy_value'].setText("N/A")
                    
        # Update Kicking School screen if visible
        if hasattr(self, 'kicking_school_screen') and self.stack.currentWidget() == self.kicking_school_screen:
            self._update_kicking_grade()

        if self.stack.currentWidget() == self.reaction_screen and self.reaction_active:
            lv = self.last_valid_forces[0]
            if lv['max_force'] is not None and lv['max_force'] >= self.reaction_threshold:
                rt_ms = ((time.perf_counter() - self.reaction_start_time)*1000)
                # Get processing delay - the time between hit detection and data transmission
                time_since_hit_ms = lv.get('time_since_hit', 0)
                # Subtract the processing delay to get the true reaction time
                true_rt_ms = rt_ms - time_since_hit_ms
                
                print(f"[DEBUG] Reaction time: {rt_ms:.0f}ms, Processing delay: {time_since_hit_ms}ms, True reaction time: {true_rt_ms:.0f}ms")
                
                # Show the corrected reaction time or "Invalid time" if it's too fast
                if true_rt_ms < 50:
                    self.reaction_time_lbl.setText("Reaction Time: Invalid time")
                else:
                    self.reaction_time_lbl.setText(f"Reaction Time: {true_rt_ms:.0f} ms")
                self.reaction_active = False

        # Speed combo drill detection using last_valid_forces[0]
        if self.stack.currentWidget() == self.speed_screen and self.speed_active:
            lv = self.last_valid_forces[0]
            elapsed = time.perf_counter() - self.speed_start_time
            
            # Get the processing delay - time between hit detection and data transmission
            time_since_hit_ms = lv.get('time_since_hit', 0) if lv.get('max_force') is not None else 0
            
            # Calculate the true elapsed time by subtracting the processing delay
            true_elapsed = elapsed - (time_since_hit_ms / 1000.0)
            
            if lv['max_force'] is not None and lv['max_force'] >= self.speed_threshold:
                # For debug, show all timing information
                print(f"[DEBUG] Speed drill hit detected - Raw elapsed: {elapsed:.3f}s, Processing delay: {time_since_hit_ms}ms, True elapsed: {true_elapsed:.3f}s")
                
                # Update UI with the combo count
                self.speed_combo += 1
                self.combo_lbl.setText(f"Combo: {self.speed_combo}")
                
                # Make it harder every 5 kicks
                if self.speed_combo % 5 == 0:
                    self.speed_time_limit = max(0.1, self.speed_time_limit - 0.1)
                    print(f"[DEBUG] Speed limit decreased to {self.speed_time_limit:.1f}s")
                    
                # Start the next kick
                self._next_kick()
            elif true_elapsed > self.speed_time_limit:
                print(f"[DEBUG] Speed drill timeout - Raw elapsed: {elapsed:.3f}s, Processing delay: {time_since_hit_ms}ms, True elapsed: {true_elapsed:.3f}s, Limit: {self.speed_time_limit:.1f}s")
                self.kick_lbl.setText("Drill ended!")
                self.speed_active = False
            
    def _update_kicking_grade(self):
        # Check if selected device is connected
        if not hasattr(self, 'active_kicking_device') or not self.active_kicking_device.is_connected:
            return
            
        esp_idx = self.active_kicking_esp_idx
        
        # Check if we have valid force readings
        if self.last_valid_forces[esp_idx]['max_force'] is not None and self.last_valid_forces[esp_idx]['max_force'] >= 220:
            # Get values from the best readings
            max_force = self.last_valid_forces[esp_idx]['max_force']
            raw_accuracy = self.last_valid_forces[esp_idx]['accuracy'] # Get raw accuracy

            # Apply the curve
            adjusted_accuracy = round(100 * (raw_accuracy / 100) ** 1.7)

            # Calculate force percentage (200N = 20%, 1000N = 100%, >1000N can exceed 100%)
            force_percent = min(120, max(0, (max_force / 1000) * 100))

            # Calculate grade as average of force percent and ADJUSTED accuracy
            grade_percent = (force_percent + adjusted_accuracy) / 2

            # Determine letter grade with new thresholds
            letter_grade = "F"
            if grade_percent >= 80:
                letter_grade = "A"
            elif grade_percent >= 65:
                letter_grade = "B"
            elif grade_percent >= 55:
                letter_grade = "C"
            elif grade_percent >= 40:
                letter_grade = "D"
                
            # Update UI
            self.grade_value.setText(letter_grade)
            self.force_label.setText(f"{max_force} N")
            self.force_percent.setText(f"{force_percent:.1f}%")
            self.accuracy_label.setText(f"{adjusted_accuracy}%")
            
            # Set grade color based on letter
            grade_colors = {
                "A": "#27ae60",  # Green
                "B": "#2980b9",  # Blue
                "C": "#f39c12",  # Orange
                "D": "#e67e22",  # Dark Orange
                "F": "#e74c3c",  # Red
            }
            self.grade_value.setStyleSheet(f"color:{grade_colors[letter_grade]};")

    def _show_force(self):       self.stack.setCurrentWidget(self.force_screen)
    def _show_training(self):    self.stack.setCurrentWidget(self.training_screen)
    def _show_games(self):       self.stack.setCurrentWidget(self.games_screen)
    def _show_settings(self):    self.stack.setCurrentWidget(self.settings_screen)


    # Connect/disconnect logic
    def _toggle_connection(self, handler, status_lbl, widgets, btn):
        if not handler.is_connected:
            if handler.connect():
                status_lbl.setText("Status: Connected")
                status_lbl.setStyleSheet("color:green;")
                btn.setText("Disconnect")
                for widget in widgets:
                    widget['force'].setText(f"Force {widget['sensor_idx']+1}:")
                    widget['force_value'].setText("N/A")
                    widget['accuracy_value'].setText("N/A")
                    widget['bar'].setValue(0)
            else:
                status_lbl.setText("Status: Connection Failed")
        else:
            handler.disconnect()
            status_lbl.setText("Status: Disconnected")
            status_lbl.setStyleSheet("color:red;")
            btn.setText("Connect")
            for widget in widgets:
                widget['force'].setText(f"Force {widget['sensor_idx']+1}:")
                widget['force_value'].setText("N/A")
                widget['accuracy_value'].setText("N/A")
                widget['bar'].setValue(0)

    def _start_fade_out(self):
        # Fade out animation
        self.fade_out = QtCore.QPropertyAnimation(self.splash_logo.graphicsEffect(), b"opacity")
        self.fade_out.setDuration(1000)  # 1 second
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.finished.connect(lambda: self.stack.setCurrentWidget(self.main_menu_screen))
        self.fade_out.start()

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

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
