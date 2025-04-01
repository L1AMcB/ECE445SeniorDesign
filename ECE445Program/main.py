import tkinter as tk
import threading
import time
from bluetooth_handler import BluetoothHandler

class ForceDisplayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Force Sensor Readings")
        self.root.geometry("1200x800")
        
        # Create frames for each ESP32
        self.frame1 = tk.LabelFrame(root, text="ESP32 #1", padx=10, pady=10)
        self.frame1.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.frame2 = tk.LabelFrame(root, text="ESP32 #2", padx=10, pady=10)
        self.frame2.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Status and readings for ESP32 #1
        self.status_label1 = tk.Label(self.frame1, text="Status: Disconnected", fg="red")
        self.status_label1.pack(anchor="w")
        
        self.force_label1 = tk.Label(self.frame1, text="Force: N/A")
        self.force_label1.pack(anchor="w")
        
        # Force bar for ESP32 #1
        self.force_bar_frame1 = tk.Frame(self.frame1, height=40, width=1000)
        self.force_bar_frame1.pack(pady=10, fill="x", expand=True)
        
        self.force_bar_bg1 = tk.Canvas(self.force_bar_frame1, height=40, width=1000, bg="lightgray")
        self.force_bar_bg1.pack(fill="both")
        
        self.force_bar1 = self.force_bar_bg1.create_rectangle(0, 0, 0, 40, fill="blue")
        
        # Status and readings for ESP32 #2
        self.status_label2 = tk.Label(self.frame2, text="Status: Disconnected", fg="red")
        self.status_label2.pack(anchor="w")
        
        self.force_label2 = tk.Label(self.frame2, text="Force: N/A")
        self.force_label2.pack(anchor="w")
        
        # Force bar for ESP32 #2
        self.force_bar_frame2 = tk.Frame(self.frame2, height=40, width=1000)
        self.force_bar_frame2.pack(pady=10, fill="x", expand=True)
        
        self.force_bar_bg2 = tk.Canvas(self.force_bar_frame2, height=40, width=1000, bg="lightgray")
        self.force_bar_bg2.pack(fill="both")
        
        self.force_bar2 = self.force_bar_bg2.create_rectangle(0, 0, 0, 40, fill="red")
        
        # Max force label
        tk.Label(self.frame1, text="0 N").pack(side="left")
        tk.Label(self.frame1, text="1000 N").pack(side="right")
        
        tk.Label(self.frame2, text="0 N").pack(side="left")
        tk.Label(self.frame2, text="1000 N").pack(side="right")
        
        # Bluetooth handlers
        self.bt_handler1 = BluetoothHandler("ESP32_1")
        self.bt_handler2 = BluetoothHandler("ESP32_2")
        
        # Start update thread
        self.running = True
        self.update_thread = threading.Thread(target=self.update_readings)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Connect buttons
        self.connect_button1 = tk.Button(self.frame1, text="Connect", command=lambda: self.connect_device(1))
        self.connect_button1.pack(pady=5)
        
        self.connect_button2 = tk.Button(self.frame2, text="Connect", command=lambda: self.connect_device(2))
        self.connect_button2.pack(pady=5)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
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
            # Update ESP32 #1 readings
            if self.bt_handler1.is_connected:
                try:
                    force1 = self.bt_handler1.get_force_reading()
                    if isinstance(force1, (int, float)):
                        self.force_label1.config(text=f"Force: {force1} N")
                        # Update force bar - scale from 0-1000 to 0-1000 pixels
                        bar_width = min(1000, max(0, force1))
                        self.force_bar_bg1.coords(self.force_bar1, 0, 0, bar_width, 40)
                    else:
                        self.force_label1.config(text=f"Force: {force1}")
                except Exception as e:
                    print(f"Error reading from ESP32_1: {e}")
                    self.force_label1.config(text="Force: Error reading")
            
            # Update ESP32 #2 readings
            if self.bt_handler2.is_connected:
                try:
                    force2 = self.bt_handler2.get_force_reading()
                    if isinstance(force2, (int, float)):
                        self.force_label2.config(text=f"Force: {force2} N")
                        # Update force bar - scale from 0-1000 to 0-1000 pixels
                        bar_width = min(1000, max(0, force2))
                        self.force_bar_bg2.coords(self.force_bar2, 0, 0, bar_width, 40)
                    else:
                        self.force_label2.config(text=f"Force: {force2}")
                except Exception as e:
                    print(f"Error reading from ESP32_2: {e}")
                    self.force_label2.config(text="Force: Error reading")
            
            time.sleep(0.1)  # Update more frequently
    
    def on_close(self):
        self.running = False
        if self.bt_handler1.is_connected:
            self.bt_handler1.disconnect()
        if self.bt_handler2.is_connected:
            self.bt_handler2.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ForceDisplayApp(root)
    root.mainloop() 