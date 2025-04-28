import os, wave, struct, math

assets = os.path.join(os.path.dirname(__file__), '..', 'assets')
os.makedirs(assets, exist_ok=True)
fname = os.path.join(assets, 'beep.wav')

framerate = 44100
duration  = 0.2    # seconds
freq      = 440.0  # Hz

with wave.open(fname, 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(framerate)
    for i in range(int(framerate * duration)):
        sample = int(32767 * math.sin(2 * math.pi * freq * (i / framerate)))
        w.writeframes(struct.pack('<h', sample))

print(f'beep.wav generated at {fname}')
