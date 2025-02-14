# Introduction

## Problem:

Taekwondo is a Korean martial art and combat sport involving primarily kicking techniques and punching. When athletes train, they utilize what are called "paddles," equipments that are analogous to mitts in boxing. Athletes repeatedly hit the paddles to train their kicks and various strikes, and it is usually up to the holder to determine whether it was a good kick, or the athletes themselves will decide whether the kick was "satisfactory" or not. Currently there is no good way to accurately quantify performance in Taekwondo training for drills such as speed and power. There exists electronic gear called "Daedo gear" for automatic scoring by tracking the power and the location of the martial artists’ kicks, but that gear is only used in competition and is prohibitively expensive, unrealistic both for everyday trianing and for accomodating every athlete. 

## Solution: 

To solve the issue of accessibility, cost, and overall quality of training for athletes, we are proposing electronic target paddles. Our prototype will include pressure sensors at different locations of the paddle to measure power and speed for kicking during training. The paddle must be lightweight and flexible, which necessitates minimal attachments to the paddle itself, encouraging the use of a wrist attachment to handle the majority of the functionality and connections. We will also facilitate reaction speed/timing drills via sound or blinking of the LEDs. Example paddle here:

We would have our main system (pcb) be a separate box that would handle the inputs from the paddles through a bluetooth connection. Then using the information received from the strikes of the athlete, our prototype will output the results and statistics to an external monitor or and LCD screen. 

## Visual Aid: 

![Alt text](Screenshot%202025-02-13%20131623.png)

## High-level requirements list: 

1. System must be able to accurately differentiate between different strength strikes to the paddle. 

2. Added weight to the paddle must not exceed 2 punds so that the kicker can safely strike the paddle, and so the holder doesn't have to work noticably harder than before to use the paddle.

3. Paddle must be able to last on it's own power for more than thirty minutes.



# Design
## Block Diagram:


# Paddle System

## 1. Power Subsystem (Paddle)
This subsystem provides a stable voltage to the paddle’s electronics using either small batteries (AA/AAA) or a Li-ion cell and a regulator. It ensures that the microcontroller, Bluetooth module, sensors, and LEDs receive a constant 3.3 V supply. Sufficient battery capacity must support at least 30 minutes of continuous operation for a typical training session.

---

## 2. Control Subsystem (Paddle)
A microcontroller and Bluetooth module gather sensor data and wirelessly transmit it to the main control box. This subsystem also processes immediate tasks—such as recognizing valid hits and managing LED signals on the paddle. 

---

## 3. Sensing Subsystem
Force sensors (and an optional accelerometer) measure the intensity (optionally location if we do an array of sensors in the paddle) of each kick on the paddle. They must be robust enough to survive repeated strikes while still delivering accurate, noise-free data to the microcontroller. Appropriate padding or mechanical dampening helps protect the sensors and ensures consistent measurements.

---

## 4. LED Subsystem
LEDs on the paddle provide immediate visual feedback to the athlete, indicating a valid strike or readiness for the next drill. These lights will be addressable RGB strips driven by a single data line from the microcontroller. Efficient control of brightness and timing is crucial to prevent excessive battery drain.

---

# Control Box & Display System

## 1. Power Subsystem (Control Box)
A wall power supply feeds the main PCB, which regulates voltage for the microcontroller, Bluetooth receiver, and any additional components (such as an audio amplifier). This ensures a stable operating environment and adequate current for the entire system. Safety-certified adapters (e.g., UL-listed) protect users from electrical hazards.

---

## 2. Control Subsystem (Control Box)
A more capable microcontroller on a custom PCB handles incoming Bluetooth data from the paddle, calculates force and timing metrics, and coordinates outputs like audio cues or display updates. It manages pairing, data integrity, and any higher-level logic (e.g., storing scores or compiling statistics). Real-time processing is essential to minimize latency and keep up with fast-paced training drills.

---

## 3. User Interface Subsystem
Connected via HDMI or a dedicated display driver, this subsystem visually presents performance metrics and scoring to the athlete or coach. An optional speaker or audio amplifier produces audible cues for reaction drills and hit confirmations. Physical buttons or other input mechanisms allow users to start/stop sessions, reset counters, or navigate settings quickly and intuitively.



# Paddle System

## 1. Power Subsystem

### Battery Source
- **Option**: One or two AA/AAA batteries in series (2–3 V), or a small Li-ion cell.

### Voltage Regulation
- **Choice**: A 3.3 V LDO or switching regulator capable of supplying enough current for the microcontroller, Bluetooth module, sensors, and LEDs.
  - **Example**: MCP1700

### Requirements
- Must supply stable 3.3 V (±5%) across the operating range of the battery/batteries.
- Must provide sufficient current for MCU, Bluetooth, sensors, and LEDs (e.g., 100–200 mA depending on design).
- Should support at least 30 minutes of operation per charge/set of batteries under typical use.

---

## 2. Control Subsystem (Paddle)

### Microcontroller
- **Choice**: ARM Cortex-M0/M4/M7–based MCU
- **Clock/Memory**: Enough flash/RAM to handle sensor reading, wireless communication, and LED control logic.

### Bluetooth Module
- **Choice**:
  - A discrete module (e.g., RN4871 for BLE), **or**
  - Integrated into the MCU (e.g., nRF52 series)
- **Responsibilities**:
  - Continuously poll force sensors (via ADC) and/or accelerometer (via I²C/SPI).
  - Process sensor data, detect valid strikes, and handle timing logic.
  - Communicate wirelessly (via Bluetooth) with the main Control Box (send data, receive LED control commands).
  - Manage LED states (on/off, color changes) in sync with hits or drills.

### Requirements
- Must reliably detect hits at a sampling rate sufficient to capture fast strikes (e.g., 100 Hz or higher).
- Must maintain a stable, low-latency Bluetooth connection (e.g., <50 ms packet round-trip).
- Must operate at low power to maximize battery life; consider sleep modes when idle.

---

## 3. Sensing Subsystem

### Force/Pressure Sensors
- **Choice**: Resistive force sensors (e.g., Interlink FSR) or piezoelectric sensors.
- **Mounting**: Must be robustly affixed to the paddle to survive repeated impacts.

### (Optional) Accelerometer
- **Choice**: MPU6050, ADXL345, or similar.
- **Purpose**: Differentiate between partial hits and real hits, or detect motion for advanced metrics.

### Requirements
- Must accurately measure forces in the relevant range (e.g., up to a few hundred newtons, or scaled by mechanical dampening).
- Must survive repeated strikes without sensor damage.
- Data must be stable enough for the MCU to distinguish real hits from noise/vibration.

---

## 4. LED Subsystem

### LED Strip
- **Choice**: Addressable LEDs (e.g., WS2812B) requiring only one MCU data line, but a 5 V rail.
- **Power & Drive**:
  - If using multiple bright LEDs, a small MOSFET or transistor driver may be needed to handle current from the 3.3 V line.
  - Addressable strips can draw up to 60 mA per RGB LED at full white brightness.

### Requirements
- Must provide visual feedback within ~100 ms of a detected hit.
- Current draw should be manageable to avoid excessive battery drain.
- Must be visible under typical training lighting conditions.

---

# Control Box & Display System

## 1. Power Subsystem (Control Box)

### Wall Power Supply
- **Choice**: A standard 5 V or 12 V DC adapter (UL-listed, 1–2 A capacity).

### Regulators
- Regulate down to 5 V (if needed) and 3.3 V for the main MCU, Bluetooth module, amplifier, etc.

### Requirements
- Must supply enough current for the entire control board, any attached display driver, and audio amplifier.
- Provide stable 5 V and/or 3.3 V rails.

---

## 2. Control Subsystem (Control Box)

### Microcontroller
- **Choice**: A higher-performance ARM Cortex-M4/M7 that can handle:
  - Real-time data processing from the paddle.
  - Generating or buffering a video signal or controlling an external HDMI driver.
  - Audio signal generation.
- **Example**: PIC32CZ or STM32H7

### External Memory / Storage (Optional)
- Potentially for bigger buffers or storing logs/scores, include an external SPI Flash or SD card slot.

### Bluetooth Transceiver
- Could be the same type of module as in the paddle, or a complementary BLE module integrated on the board.
- If the MCU includes BLE, use that.

### (Optional) External Video Driver
- For generating HDMI signal, we might use:
  - An FPGA-based or dedicated HDMI encoder chip (e.g., TFP410/TFP401 for DVI/HDMI).

### Requirements
- Must receive sensor data at an acceptable rate (e.g., at least 10–50 packets/sec) and update the user display quickly (<200 ms latency).
- Must handle calculations (strike force, average speed, reaction times) in real time.
- Provide a robust wireless link—lost packets should be detected, and the system should handle re-connections smoothly.

---

## 3. User Interface Subsystem

### Display
- Include an HDMI encoder chip and route the necessary signals from the MCU to generate timing.
- **External Display**: Any external display with an HDMI input.

### (Optional) Speaker / Audio
- **Audio Amplifier**: e.g., a small Class D amp (PAM8403 or similar).
- **Connection**:
  - MCU generates audio signals via PWM or I²S → Amp → Speaker.
- **Audio Cues**: Reaction drills, notifications, etc.

### (Optional) Input Buttons or Controls
- Let you start/stop drills, reset counters, etc.
- Connect to MCU GPIO with basic debouncing.

### Requirements
- Display must show real-time stats (hit count, force, reaction time) within 200 ms.
- If using a speaker, volume must be sufficient for a noisy training environment.
- If using physical buttons, they must be straightforward for an athlete or coach to press mid-training.


## Tolerance Analysis:
The biggest hurdle we must overcome is the robustness of the paddle system. Repeated strikes from trained martial artists will require a system able to handle it accordingly. Part of how we aim to solve this is having some of the more fragile components on the wrist of the holder, rather than in the paddle itself. The force sensors themselves are designed for taking blows. If we go with the Force Sensing Resistors like planned, they are flexible enough that we won't need to worry about them breaking. We also plan to pad the sensors to both dampen the strikes as well as help protect the sensors. 

# Ethics and Safety

We see no ethics concern with this type of technology. We will follow all policies outlined by the IEEE and the ACM Code of Ethics. To avoid ethical breaches we will consistently check that our work always follows best practice. In terms of safety, no one should attempt the Taekwondo techniques if they are not already experienced, or are being guided by someone who is. Both Liam and Alex have 10+ years of experience with Taekwondo and are thus well suited to handle this project safely. 

