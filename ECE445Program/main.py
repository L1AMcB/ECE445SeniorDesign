import tkinter as tk
import threading
import time
import os
from bluetooth_handler import BluetoothHandler

# Try to import PIL, but provide a fallback if it's not available
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available. Using fallback display methods.")

class TransparentFrame(tk.Frame):
    """A frame with adjustable transparency"""
    def __init__(self, parent, bg_color, transparency=0.7, **kwargs):
        super().__init__(parent, **kwargs)
        self.bg_color = bg_color
        self.transparency = transparency
        
        # Configure the frame
        self.configure(bg=self.bg_color)
        
class CTCForceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CTC Force Measurement System")
        self.root.geometry("1200x800")
        self.root.configure(bg="black")
        
        # Set up splash screen and main menu first
        self.setup_splash_screen()
        
        # Bluetooth handlers - initialize but don't connect yet
        self.bt_handler1 = BluetoothHandler("ESP32_1")
        self.bt_handler2 = BluetoothHandler("ESP32_2")
        
        # Set up main thread flag
        self.running = True
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_splash_screen(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Configure black background
        self.root.configure(bg="black")
        
        # Load CTC logo or just display text if no logo
        if PIL_AVAILABLE:
            try:
                logo_path = os.path.join("assets", "ctc_logo.png")
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((300, 300), Image.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                
                self.logo_label = tk.Label(self.root, image=self.logo_photo, bg="black")
                self.logo_label.place(relx=0.5, rely=0.4, anchor="center")
                
                # Create text label below logo
                self.splash_label = tk.Label(self.root, text="Produced by CTC", 
                                            font=("Helvetica", 24, "bold"), 
                                            fg="#000000", bg="black")
                self.splash_label.place(relx=0.5, rely=0.6, anchor="center")
            except Exception as e:
                # Just show the text if no logo
                print(f"Could not load logo: {e}")
                self.splash_label = tk.Label(self.root, text="Produced by CTC", 
                                           font=("Helvetica", 36, "bold"), 
                                           fg="#000000", bg="black")
                self.splash_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            # Fallback to text-only if PIL is not available
            self.splash_label = tk.Label(self.root, text="Produced by CTC", 
                                       font=("Helvetica", 36, "bold"), 
                                       fg="#000000", bg="black")
            self.splash_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Schedule the splash sequence
        self.root.after(500, self.fade_in_splash)
    
    def fade_in_splash(self):
        # Fade in the splash text over 0.5 seconds
        for i in range(11):  # 0 to 1.0 in 10 steps
            alpha = i / 10
            # Set color using hex format with alpha
            color_value = int(255 * alpha)
            hex_color = f"#{color_value:02x}{color_value:02x}{color_value:02x}"
            self.splash_label.configure(fg=hex_color)
            self.root.update()
            time.sleep(0.05)
        
        # Show fully visible for 1 second
        self.splash_label.configure(fg="white")  # Ensure it's fully white
        self.root.update()
        time.sleep(1)
        
        # Start fade out
        self.fade_out_splash()
    
    def fade_out_splash(self):
        # Fade out the splash text over 0.5 seconds
        for i in range(10, -1, -1):  # 1.0 to 0 in 10 steps
            alpha = i / 10
            # Set color using hex format with alpha
            color_value = int(255 * alpha)
            hex_color = f"#{color_value:02x}{color_value:02x}{color_value:02x}"
            self.splash_label.configure(fg=hex_color)
            self.root.update()
            time.sleep(0.05)
            
        # After fade out, show main menu
        self.setup_main_menu()
    
    def setup_main_menu(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Try to load the background image if PIL is available
        bg_loaded = False
        if PIL_AVAILABLE:
            try:
                # Load the background image
                image_path = os.path.join("assets", "homescreen.png")
                # Open the image
                bg_image = Image.open(image_path)
                # Resize image to fit window
                bg_image = bg_image.resize((1200, 800), Image.LANCZOS)
                # Convert to PhotoImage
                self.bg_photo = ImageTk.PhotoImage(bg_image)
                
                # Create a label with the image
                bg_label = tk.Label(self.root, image=self.bg_photo)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                bg_loaded = True
            except Exception as e:
                print(f"Error loading background image with PIL: {e}")
                bg_loaded = False
                
        # Try native Tkinter approach if PIL failed
        if not bg_loaded:
            try:
                # Use Tkinter's built-in PhotoImage
                image_path = os.path.join("assets", "homescreen.png")
                self.bg_photo = tk.PhotoImage(file=image_path)
                
                # Create a label with the image
                bg_label = tk.Label(self.root, image=self.bg_photo)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                bg_loaded = True
                print("Successfully loaded image with Tkinter's PhotoImage")
            except Exception as e:
                print(f"Error loading background image with Tkinter: {e}")
                bg_loaded = False
        
        # Fallback to a gradient background if image couldn't be loaded
        if not bg_loaded:
            self.root.configure(bg="#1e3a5c")  # Dark blue background
            
        # Create title with a modern font - apply a dark background just to the text for readability
        title_label = tk.Label(self.root, 
                              text="CTC Force Measurement System", 
                              font=("Helvetica", 28, "bold"), 
                              fg="white",
                              bg="#1e3a5c",
                              padx=20, pady=10)
        title_label.place(relx=0.5, rely=0.15, anchor="center")
        
        # Button style - using labels instead of buttons for a completely invisible button effect
        button_font = ("Impact", 22, "underline")
        button_fg = "white"
        pady_between = 70  # More space between buttons
        
        # Create menu buttons as labels with binding for click events
        standard_button = tk.Label(self.root, 
                                  text="Standard Force Measuring", 
                                  font=button_font,
                                  bg="#1e3a5c",  # Match the background
                                  fg=button_fg,
                                  cursor="hand2")  # Change cursor to hand when hovering
        standard_button.place(relx=0.1, rely=0.3, anchor="w")
        
        # Bind click and hover events
        standard_button.bind("<Button-1>", lambda e: self.open_force_measurement())
        standard_button.bind("<Enter>", lambda e: standard_button.config(fg="#3498db"))
        standard_button.bind("<Leave>", lambda e: standard_button.config(fg="white"))
        
        training_button = tk.Label(self.root, 
                                  text="Training Modes", 
                                  font=button_font,
                                  bg="#1e3a5c",  # Match the background
                                  fg=button_fg,
                                  cursor="hand2")
        training_button.place(relx=0.1, rely=0.45, anchor="w")
        
        # Bind click and hover events
        training_button.bind("<Button-1>", lambda e: self.open_training_modes())
        training_button.bind("<Enter>", lambda e: training_button.config(fg="#e74c3c"))
        training_button.bind("<Leave>", lambda e: training_button.config(fg="white"))
        
        games_button = tk.Label(self.root, 
                               text="Mini Games", 
                               font=button_font,
                               bg="#1e3a5c",  # Match the background
                               fg=button_fg,
                               cursor="hand2")
        games_button.place(relx=0.1, rely=0.6, anchor="w")
        
        # Bind click and hover events
        games_button.bind("<Button-1>", lambda e: self.open_mini_games())
        games_button.bind("<Enter>", lambda e: games_button.config(fg="#2ecc71"))
        games_button.bind("<Leave>", lambda e: games_button.config(fg="white"))
        
        settings_button = tk.Label(self.root, 
                                  text="Settings", 
                                  font=button_font,
                                  bg="#1e3a5c",  # Match the background
                                  fg=button_fg,
                                  cursor="hand2")
        settings_button.place(relx=0.1, rely=0.75, anchor="w")
        
        # Bind click and hover events
        settings_button.bind("<Button-1>", lambda e: self.open_settings())
        settings_button.bind("<Enter>", lambda e: settings_button.config(fg="#9b59b6"))
        settings_button.bind("<Leave>", lambda e: settings_button.config(fg="white"))
        
        # Add version info at the bottom
        version_label = tk.Label(self.root,
                               text="CTC Force System v1.0",
                               font=("Helvetica", 10),
                               fg="white",
                               bg="#1e3a5c")
        version_label.place(relx=0.5, rely=0.95, anchor="center")
    
    def open_force_measurement(self):
        # Clear current widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Create the force measurement interface
        self.setup_force_measurement()
    
    def setup_force_measurement(self):
        # Configure the window
        self.root.title("Force Sensor Readings")
        self.root.configure(bg="#f0f3f6")  # Light blue-gray background
        
        # Create header frame
        header_frame = tk.Frame(self.root, bg="#3498db", height=60)
        header_frame.pack(fill=tk.X)
        
        # Add a title to the header
        header_label = tk.Label(header_frame, text="Force Measurement", 
                               font=("Helvetica", 20, "bold"),
                               fg="white", bg="#3498db")
        header_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Add a back button
        back_button = tk.Button(header_frame, text="← Back", 
                               command=self.setup_main_menu,
                               font=("Helvetica", 12),
                               bg="#2980b9", fg="white",
                               relief=tk.FLAT, borderwidth=0,
                               padx=15, pady=5)
        back_button.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Create frames for each ESP32
        self.frame1 = tk.LabelFrame(self.root, text="ESP32 #1", 
                                  padx=15, pady=15, 
                                  font=("Helvetica", 14, "bold"),
                                  bg="#ffffff",
                                  fg="#333333")
        self.frame1.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.frame2 = tk.LabelFrame(self.root, text="ESP32 #2", 
                                  padx=15, pady=15, 
                                  font=("Helvetica", 14, "bold"),
                                  bg="#ffffff",
                                  fg="#333333")
        self.frame2.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Status and readings for ESP32 #1
        self.status_label1 = tk.Label(self.frame1, text="Status: Disconnected", 
                                    fg="#e74c3c", bg="#ffffff",
                                    font=("Helvetica", 12))
        self.status_label1.pack(anchor="w")
        
        self.force_label1 = tk.Label(self.frame1, text="Force: N/A", 
                                   font=("Helvetica", 16, "bold"),
                                   bg="#ffffff")
        self.force_label1.pack(anchor="w", pady=(5, 15))
        
        # Force bar for ESP32 #1
        self.force_bar_frame1 = tk.Frame(self.frame1, height=40, bg="#ffffff")
        self.force_bar_frame1.pack(fill="x", expand=True)
        
        self.force_bar_bg1 = tk.Canvas(self.force_bar_frame1, height=40, bg="#ecf0f1")
        self.force_bar_bg1.pack(fill="both")
        
        self.force_bar1 = self.force_bar_bg1.create_rectangle(0, 0, 0, 40, fill="#3498db", outline="")
        
        # Status and readings for ESP32 #2
        self.status_label2 = tk.Label(self.frame2, text="Status: Disconnected", 
                                    fg="#e74c3c", bg="#ffffff",
                                    font=("Helvetica", 12))
        self.status_label2.pack(anchor="w")
        
        self.force_label2 = tk.Label(self.frame2, text="Force: N/A", 
                                   font=("Helvetica", 16, "bold"),
                                   bg="#ffffff")
        self.force_label2.pack(anchor="w", pady=(5, 15))
        
        # Force bar for ESP32 #2
        self.force_bar_frame2 = tk.Frame(self.frame2, height=40, bg="#ffffff")
        self.force_bar_frame2.pack(fill="x", expand=True)
        
        self.force_bar_bg2 = tk.Canvas(self.force_bar_frame2, height=40, bg="#ecf0f1")
        self.force_bar_bg2.pack(fill="both")
        
        self.force_bar2 = self.force_bar_bg2.create_rectangle(0, 0, 0, 40, fill="#e74c3c", outline="")
        
        # Force labels
        # Force labels
        force_scale_frame1 = tk.Frame(self.frame1, bg="#ffffff")
        force_scale_frame1.pack(fill="x")
        tk.Label(force_scale_frame1, text="0 N", 
            font=("Helvetica", 10), bg="#ffffff").pack(side="left")
        tk.Label(force_scale_frame1, text="1500 N",  # Changed from 1000 N to 1500 N
            font=("Helvetica", 10), bg="#ffffff").pack(side="right")

        force_scale_frame2 = tk.Frame(self.frame2, bg="#ffffff")
        force_scale_frame2.pack(fill="x")
        tk.Label(force_scale_frame2, text="0 N", 
            font=("Helvetica", 10), bg="#ffffff").pack(side="left")
        tk.Label(force_scale_frame2, text="1500 N",  # Changed from 1000 N to 1500 N
            font=("Helvetica", 10), bg="#ffffff").pack(side="right")
        
        # Connect buttons with modern styling
        button_frame1 = tk.Frame(self.frame1, bg="#ffffff")
        button_frame1.pack(pady=10)
        self.connect_button1 = tk.Button(button_frame1, text="Connect", 
                                       command=lambda: self.connect_device(1),
                                       bg="#3498db", fg="white", 
                                       font=("Helvetica", 12),
                                       relief=tk.FLAT, borderwidth=0,
                                       padx=20, pady=8)
        self.connect_button1.pack()
        
        button_frame2 = tk.Frame(self.frame2, bg="#ffffff")
        button_frame2.pack(pady=10)
        self.connect_button2 = tk.Button(button_frame2, text="Connect", 
                                       command=lambda: self.connect_device(2),
                                       bg="#e74c3c", fg="white", 
                                       font=("Helvetica", 12),
                                       relief=tk.FLAT, borderwidth=0,
                                       padx=20, pady=8)
        self.connect_button2.pack()
        
        # Start update thread if not already running
        if not hasattr(self, 'update_thread') or not self.update_thread.is_alive():
            self.update_thread = threading.Thread(target=self.update_readings)
            self.update_thread.daemon = True
            self.update_thread.start()
    
    def open_training_modes(self):
        # Placeholder for training modes screen
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.root.configure(bg="#f0f3f6")  # Light blue-gray background
        
        # Create header frame
        header_frame = tk.Frame(self.root, bg="#e74c3c", height=60)
        header_frame.pack(fill=tk.X)
        
        # Add a title to the header
        header_label = tk.Label(header_frame, text="Training Modes", 
                               font=("Helvetica", 20, "bold"),
                               fg="white", bg="#e74c3c")
        header_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Add a back button
        back_button = tk.Button(header_frame, text="← Back", 
                               command=self.setup_main_menu,
                               font=("Helvetica", 12),
                               bg="#c0392b", fg="white",
                               relief=tk.FLAT, borderwidth=0,
                               padx=15, pady=5)
        back_button.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Create main content frame
        content_frame = tk.Frame(self.root, bg="#ffffff")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Placeholder message
        message = tk.Label(content_frame, 
                          text="Training modes coming soon!", 
                          font=("Helvetica", 18),
                          bg="#ffffff")
        message.pack(expand=True, pady=50)
        
        # Add some placeholder buttons for future training modes
        modes_frame = tk.Frame(content_frame, bg="#ffffff")
        modes_frame.pack(pady=50)
        
        endurance_button = tk.Button(modes_frame, 
                                    text="Endurance Training", 
                                    font=("Helvetica", 14),
                                    bg="#e74c3c", fg="white",
                                    relief=tk.FLAT, borderwidth=0,
                                    padx=20, pady=10,
                                    width=20)
        endurance_button.pack(pady=10)
        
        strength_button = tk.Button(modes_frame, 
                                   text="Strength Training", 
                                   font=("Helvetica", 14),
                                   bg="#e74c3c", fg="white",
                                   relief=tk.FLAT, borderwidth=0,
                                   padx=20, pady=10,
                                   width=20)
        strength_button.pack(pady=10)
    
    def open_mini_games(self):
        # Placeholder for mini games screen
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.root.configure(bg="#f0f3f6")  # Light blue-gray background
        
        # Create header frame
        header_frame = tk.Frame(self.root, bg="#2ecc71", height=60)
        header_frame.pack(fill=tk.X)
        
        # Add a title to the header
        header_label = tk.Label(header_frame, text="Mini Games", 
                               font=("Helvetica", 20, "bold"),
                               fg="white", bg="#2ecc71")
        header_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Add a back button
        back_button = tk.Button(header_frame, text="← Back", 
                               command=self.setup_main_menu,
                               font=("Helvetica", 12),
                               bg="#27ae60", fg="white",
                               relief=tk.FLAT, borderwidth=0,
                               padx=15, pady=5)
        back_button.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Create main content frame
        content_frame = tk.Frame(self.root, bg="#ffffff")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Placeholder message
        message = tk.Label(content_frame, 
                          text="Mini games coming soon!", 
                          font=("Helvetica", 18),
                          bg="#ffffff")
        message.pack(expand=True, pady=50)
        
        # Add some placeholder buttons for future games
        games_frame = tk.Frame(content_frame, bg="#ffffff")
        games_frame.pack(pady=50)
        
        balloon_button = tk.Button(games_frame, 
                                  text="Balloon Pop", 
                                  font=("Helvetica", 14),
                                  bg="#2ecc71", fg="white",
                                  relief=tk.FLAT, borderwidth=0,
                                  padx=20, pady=10,
                                  width=20)
        balloon_button.pack(pady=10)
        
        race_button = tk.Button(games_frame, 
                               text="Force Race", 
                               font=("Helvetica", 14),
                               bg="#2ecc71", fg="white",
                               relief=tk.FLAT, borderwidth=0,
                               padx=20, pady=10,
                               width=20)
        race_button.pack(pady=10)
    
    def open_settings(self):
        # Placeholder for settings screen
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.root.configure(bg="#f0f3f6")  # Light blue-gray background
        
        # Create header frame
        header_frame = tk.Frame(self.root, bg="#9b59b6", height=60)
        header_frame.pack(fill=tk.X)
        
        # Add a title to the header
        header_label = tk.Label(header_frame, text="Settings", 
                               font=("Helvetica", 20, "bold"),
                               fg="white", bg="#9b59b6")
        header_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Add a back button
        back_button = tk.Button(header_frame, text="← Back", 
                               command=self.setup_main_menu,
                               font=("Helvetica", 12),
                               bg="#8e44ad", fg="white",
                               relief=tk.FLAT, borderwidth=0,
                               padx=15, pady=5)
        back_button.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Create main content frame
        content_frame = tk.Frame(self.root, bg="#ffffff")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Settings options
        settings_title = tk.Label(content_frame,
                                 text="Application Settings",
                                 font=("Helvetica", 16, "bold"),
                                 bg="#ffffff")
        settings_title.pack(anchor="w", padx=20, pady=(20, 30))
        
        # Example settings
        settings_frame = tk.Frame(content_frame, bg="#ffffff")
        settings_frame.pack(fill="x", padx=20)
        
        # Theme setting
        theme_frame = tk.Frame(settings_frame, bg="#ffffff")
        theme_frame.pack(fill="x", pady=10)
        
        theme_label = tk.Label(theme_frame, text="Theme:", 
                              font=("Helvetica", 12),
                              bg="#ffffff", width=15, anchor="w")
        theme_label.pack(side=tk.LEFT)
        
        theme_var = tk.StringVar(value="Light")
        theme_menu = tk.OptionMenu(theme_frame, theme_var, "Light", "Dark", "System")
        theme_menu.configure(font=("Helvetica", 12), bg="#ffffff")
        theme_menu.pack(side=tk.LEFT, fill="x", expand=True)
        
        # Units setting
        units_frame = tk.Frame(settings_frame, bg="#ffffff")
        units_frame.pack(fill="x", pady=10)
        
        units_label = tk.Label(units_frame, text="Force Units:", 
                              font=("Helvetica", 12),
                              bg="#ffffff", width=15, anchor="w")
        units_label.pack(side=tk.LEFT)
        
        units_var = tk.StringVar(value="Newtons (N)")
        units_menu = tk.OptionMenu(units_frame, units_var, "Newtons (N)", "Pounds (lbs)", "Kilograms (kg)")
        units_menu.configure(font=("Helvetica", 12), bg="#ffffff")
        units_menu.pack(side=tk.LEFT, fill="x", expand=True)
        
        # Save button
        save_button = tk.Button(content_frame, text="Save Settings",
                               font=("Helvetica", 12),
                               bg="#9b59b6", fg="white",
                               relief=tk.FLAT, borderwidth=0,
                               padx=20, pady=10)
        save_button.pack(pady=30)
    
    def connect_device(self, device_num):
        if device_num == 1:
            if not self.bt_handler1.is_connected:
                success = self.bt_handler1.connect()
                if success:
                    self.status_label1.config(text="Status: Connected", fg="green")
                    self.connect_button1.config(text="Disconnect")
                else:
                    self.status_label1.config(text="Status: Connection Failed", fg="red")
            else:
                self.bt_handler1.disconnect()
                self.status_label1.config(text="Status: Disconnected", fg="red")
                self.force_label1.config(text="Force: N/A")
                self.connect_button1.config(text="Connect")
                self.force_bar_bg1.coords(self.force_bar1, 0, 0, 0, 40)
        else:
            if not self.bt_handler2.is_connected:
                success = self.bt_handler2.connect()
                if success:
                    self.status_label2.config(text="Status: Connected", fg="green")
                    self.connect_button2.config(text="Disconnect")
                else:
                    self.status_label2.config(text="Status: Connection Failed", fg="red")
            else:
                self.bt_handler2.disconnect()
                self.status_label2.config(text="Status: Disconnected", fg="red")
                self.force_label2.config(text="Force: N/A")
                self.connect_button2.config(text="Connect")
                self.force_bar_bg2.coords(self.force_bar2, 0, 0, 0, 40)
    
    def update_readings(self):
        while self.running:
            # Only update if we're in the force measurement screen
            if hasattr(self, 'force_label1') and self.force_label1.winfo_exists():
                # Update ESP32 #1 readings - now get both values at once
                if self.bt_handler1.is_connected:
                    try:
                        force1, force2 = self.bt_handler1.get_both_force_readings()
                        
                        # Update first force reading display
                        if isinstance(force1, (int, float)):
                            self.force_label1.config(text=f"Force: {force1} N")
                            # Update force bar - scale from 0-1500 to 0-width of bar
                            bar_width = min(self.force_bar_bg1.winfo_width(), max(0, force1/1500 * self.force_bar_bg1.winfo_width()))
                            self.force_bar_bg1.coords(self.force_bar1, 0, 0, bar_width, 40)
                        else:
                            self.force_label1.config(text=f"Force: {force1}")
                        
                        # Update second force reading if we're using a single ESP32 for both sensors
                        if isinstance(force2, (int, float)):
                            self.force_label2.config(text=f"Force: {force2} N")
                            # Update force bar - scale from 0-1500 to 0-width of bar
                            bar_width = min(self.force_bar_bg2.winfo_width(), max(0, force2/1500 * self.force_bar_bg2.winfo_width()))
                            self.force_bar_bg2.coords(self.force_bar2, 0, 0, bar_width, 40)
                        
                    except Exception as e:
                        print(f"Error reading from ESP32_1: {e}")
                        self.force_label1.config(text="Force: Error reading")
                
                # If you're using a separate ESP32 for the second sensor, keep this code
                # Otherwise, you can remove it if both sensors are connected to ESP32_1
                if self.bt_handler2.is_connected:
                    try:
                        force2 = self.bt_handler2.get_force_reading()
                        if isinstance(force2, (int, float)):
                            self.force_label2.config(text=f"Force: {force2} N")
                            # Update force bar - scale from 0-1500 to 0-width of bar
                            bar_width = min(self.force_bar_bg2.winfo_width(), max(0, force2/1500 * self.force_bar_bg2.winfo_width()))
                            self.force_bar_bg2.coords(self.force_bar2, 0, 0, bar_width, 40)
                        else:
                            self.force_label2.config(text=f"Force: {force2}")
                    except Exception as e:
                        print(f"Error reading from ESP32_2: {e}")
                        self.force_label2.config(text="Force: Error reading")
                
                time.sleep(0.1)  # Update frequently
    
    def on_close(self):
        self.running = False
        if self.bt_handler1.is_connected:
            self.bt_handler1.disconnect()
        if self.bt_handler2.is_connected:
            self.bt_handler2.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CTCForceApp(root)
    root.mainloop() 