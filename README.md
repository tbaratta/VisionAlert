# VisionAlert 👁️

A real-time drowsiness detection app that alerts you when your eyes have been closed for more than 3 seconds. Uses your webcam, MediaPipe face mesh, and Eye Aspect Ratio (EAR) to detect eye closure.

---

## Requirements

- Python 3.11
- Webcam
- An `alarm.mp3` file placed in the `sounds/` folder

> ⚠️ **Use `mediapipe==0.10.14` specifically.** Version 0.10.15+ removed the `mp.solutions` API this project uses and will throw `AttributeError: module 'mediapipe' has no attribute 'solutions'`.

---

## Setup

### macOS

```bash
# Clone the repo
git clone https://github.com/tbaratta/VisionAlert.git
cd VisionAlert/src

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install opencv-python mediapipe==0.10.14 numpy

# Run
python detect.py
```

### Windows

```bash
# Clone the repo
git clone https://github.com/tbaratta/VisionAlert.git
cd VisionAlert/src

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install opencv-python mediapipe==0.10.14 numpy plyer

# Run
python detect.py
```

> **Windows note:** The app uses `afplay` on macOS for sound. On Windows you need to change the sound playback in `detect.py`. Replace the `play_alarm()` function with:
>
> ```python
> def play_alarm():
>     global alarm_process
>     sound = ALARM_PATH if os.path.exists(ALARM_PATH) else None
>     if sound:
>         alarm_process = subprocess.Popen(["powershell", "-c", f"(New-Object Media.SoundPlayer '{sound}').PlaySync()"])
>         alarm_process.wait()
>         alarm_process = None
> ```
>
> And replace `stop_alarm()` with:
> ```python
> def stop_alarm():
>     global alarm_process
>     if alarm_process and alarm_process.poll() is None:
>         alarm_process.terminate()
>         alarm_process = None
> ```

---

## Configuration

All settings are at the top of `detect.py`:

| Variable | Default | Description |
|---|---|---|
| `EAR_THRESHOLD` | `0.25` | How closed eyes need to be to count. Lower = harder to trigger |
| `CLOSED_FRAME_LIMIT` | `90` | Frames before alert fires (~3s at 30fps). Increase for longer delay |
| `ALERT_COOLDOWN` | `3.0` | Seconds before alert can fire again after reset |

---

## Controls

| Key | Action |
|---|---|
| `ESC` | Quit |

---

## Project Structure

```
VisionAlert/
├── sounds/
│   └── alarm.mp3        # Add your own alarm sound here
├── src/
│   └── detect.py        # Main script
└── README.md
```
