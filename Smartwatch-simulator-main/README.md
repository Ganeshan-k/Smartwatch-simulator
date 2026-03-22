# Smartwatch Simulator

A real-time smartwatch data simulator built with FastAPI. Streams simulated health metrics (heart rate, steps, distance, calories) via Server-Sent Events (SSE).

## Features

- **Live Data Streaming** – Real-time SSE stream of simulated smartwatch metrics
- **Configurable Settings** – Adjust steps per tick, BPM range, stride length, and more
- **Event History** – Retrieve the last *n* data events via API
- **Interactive UI** – Browser-based dashboard to visualize and control the simulation

## Requirements

- Python 3.8+
- pip

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/QuincyThawne/Smartwatch-simulator.git
   cd Smartwatch-simulator
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the server with Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```

Then open your browser and navigate to:

```
http://127.0.0.1:8000
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves the web UI |
| `/api/stream` | GET | SSE stream of real-time data |
| `/api/state` | GET | Current simulation state and settings |
| `/api/history?n=10` | GET | Last *n* generated data events |
| `/api/settings` | POST | Update simulation settings (JSON body) |
| `/api/control` | POST | Control simulation: `{"cmd": "start"}`, `{"cmd": "stop"}`, `{"cmd": "reset"}` |

## Configuration Options

You can adjust these settings via the UI or by POSTing to `/api/settings`:

| Setting | Default | Description |
|---------|---------|-------------|
| `steps_per_tick_min` | 0 | Minimum steps added per tick |
| `steps_per_tick_max` | 3 | Maximum steps added per tick |
| `bpm_min` | 55 | Minimum heart rate |
| `bpm_max` | 120 | Maximum heart rate |
| `calories_per_step` | 0.04 | Calories burned per step |
| `meters_per_step` | 0.78 | Average stride length (meters) |
| `tick_interval` | 1.0 | Seconds between data updates |
| `history_max` | 1000 | Maximum events stored in history |

## Project Structure

```
Smartwatch Simulation/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment config
├── README.md            # This file
└── static/
    ├── index.html       # Web UI
    └── styles.css       # Styling
```

## License

MIT
