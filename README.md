# ECE445SeniorDesign

Senior design project for ECE 445, build by Liam McBride and Alexander Lee. 

# Title: Electronic Martial Arts Paddles

Team Members:
- Liam McBride (liamjm2)
- Alexander Lee (asl9)

# Problem

Currently there is no good way to accurately quantify performance in Taekwondo training for drills such as speed and power drills. There exists electronic gear for automatic scoring by tracking the power and the location of the martial artists’ kicks, but that gear is only used in competition and is prohibitively expensive. 

# Solution

We are proposing electronic target paddles with pressure sensors at different locations of the paddle and LED’s to measure power and speed for kicking during training. We will also facilitate reaction speed/timing drills via sound or blinking of the LEDs. Example paddle here:

We would have our main system (pcb) be a separate box that would handle the inputs from the paddles, and connect to a display to show scores and statistics.

# Background


Both Liam and Alex are executives for the university’s RSO Competitive Taekwondo Club, and have practiced Taekwondo for 10+ years, competing at local to international levels. 

# Solution Components

## Subsystem 1: Control Box and Display

Explain what the subsystem does.  Explicitly list what sensors/components you will use in this subsystem.  Include part numbers.

Custom PCB




Bluetooth receiver for connecting with the paddle and sending/receiving data and instructions
The target paddles will be difficult to maintain if there were wires coming out of it to the PCB, so we will utilize bluetooth connection for the LED and sensors

HDMI Out to regular display or LCD screen
Have an HDMI connection to a monitor or LCD screen directly from the PCB to display our scores using a health bar mechanism as commonly seen in video games.
We will also display statistic for our drills 


Wall power/power supply
We would need a constant source of power, which we would use a power supply. The power supply will be connected to a wall outlet. 

Sound system/speaker
We will use speakers that play a sound when the target paddle is hit, along with the LED. 
We will also use the speakers to give a sound cue for reaction drills 
different sounds for different kicks or choosing right or left leg

## Subsystem 2: Electronic Paddle

pressure/force sensor
three of these sensors each placed at the front, middle, and rear side of the paddle to distinguish the location of the hits. Each of these sensors will measure how strong the hits were, and crossing a certain force threshold will indicate a valid hit. Since force sensors that handle high forces can be fairly expensive, we would need to come up with a way to dampen the impact or distribute the force, and then scale the measurement so we can use cheaper, lower threshold sensors. We are also considering the use of an accelerometer. 

LEDs or LED strip 
These led strips will be an indicator for a valid hit
or maybe for reaction drills
or each led with different colors will indicate which part of the paddle was hit
different colors for different kicks or choosing right or left leg

Bluetooth transmitter for connecting with control box


Battery power 
Since the components on the target paddles will be physically separate from the PCB box, we will need battery power to keep the LED and sensors operating without a direct power supply from the wall. 



# Criterion For Success

System is able to accurately track response times
System is able to accurately measure force of strikes
Bluetooth is working so we don’t resort to using wires
Paddle and auxiliary machinery is able to withstand repeated strong blows without breaking. (> 10 strikes min)
LED, speaker, and sensors are working in cohesion
Display is accurately reflecting desired results.
