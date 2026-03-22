import asyncio
import json
import random
import time
from collections import deque
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict

app = FastAPI(title="Smartwatch Simulator API")

# Mount static folder (index.html + CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Simulation state & settings ---
state = {
    "running": True,
    # Actual numeric state that will be updated
    "steps": 0,
    "distance_m": 0.0,
    "calories": 0.0,
    "bpm": 70,
    "last_update": time.time()
}

# Default user-configurable limits:
settings = {
    "steps_per_tick_min": 0,    # steps added per tick
    "steps_per_tick_max": 3,
    "bpm_min": 55,
    "bpm_max": 120,
    "calories_per_step": 0.04,  # calories per step (approx)
    "meters_per_step": 0.78,    # average stride length in meters
    "tick_interval": 1.0,       # seconds between updates
    # randomness intensity for bpm jumps
    "bpm_jitter": 2.5
}

# store up to this many recent payloads (can be updated via /api/settings)
settings.setdefault("history_max", 1000)

# history deque for recent generated payloads
history = deque(maxlen=settings["history_max"])

# simple helper to clamp values
def clamp(v, a, b):
    return max(a, min(b, v))

# SSE generator: yields JSON payloads every tick_interval seconds
async def event_generator():
    while True:
        if state["running"]:
            # steps: random between min and max
            step_add = random.randint(settings["steps_per_tick_min"], settings["steps_per_tick_max"])
            state["steps"] += step_add

            # distance and calories based on steps
            state["distance_m"] += step_add * settings["meters_per_step"]
            state["calories"] += step_add * settings["calories_per_step"]

            # bpm: wander toward a random target within bpm range, with jitter
            target_bpm = random.uniform(settings["bpm_min"], settings["bpm_max"])
            current = state["bpm"]
            # move current a bit toward target with jitter
            delta = (target_bpm - current) * 0.08 + random.uniform(-settings["bpm_jitter"], settings["bpm_jitter"])
            new_bpm = clamp(round(current + delta), settings["bpm_min"], settings["bpm_max"])
            state["bpm"] = int(new_bpm)

            state["last_update"] = time.time()

        # prepare payload
        payload = {
            "timestamp": time.time(),
            "running": state["running"],
            "steps": state["steps"],
            "distance_m": round(state["distance_m"], 2),
            "distance_km": round(state["distance_m"] / 1000.0, 3),
            "calories": round(state["calories"], 2),
            "bpm": state["bpm"]
        }
        # append a copy to history (non-blocking)
        try:
            history.append(payload.copy())
        except Exception:
            pass

        yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(settings["tick_interval"])

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def homepage():
    # serve index.html from static folder
    return FileResponse("static/index.html")

@app.get("/api/stream")
async def stream():
    # SSE stream of simulated data
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/state")
async def get_state():
    return JSONResponse({
        "state": state,
        "settings": settings
    })


@app.get("/api/history")
async def get_history(n: int = 10):
    """Return the last `n` generated payloads (most recent last)."""
    try:
        n = max(1, int(n))
    except Exception:
        n = 10
    items = list(history)
    if n < len(items):
        items = items[-n:]
    return JSONResponse({"history": items})

@app.post("/api/settings")
async def set_settings(payload: Dict):
    # Accepts JSON with any of the keys in settings to update them.
    # Basic validation/clamping for numeric values
    for k, v in payload.items():
        if k in settings:
            try:
                # keep types sensible
                if isinstance(settings[k], float):
                    settings[k] = float(v)
                elif isinstance(settings[k], int):
                    settings[k] = int(v)
                else:
                    settings[k] = v
            except Exception:
                pass

    # ensure logical sanity for min/max bounds
    if settings["steps_per_tick_min"] > settings["steps_per_tick_max"]:
        settings["steps_per_tick_min"], settings["steps_per_tick_max"] = settings["steps_per_tick_max"], settings["steps_per_tick_min"]
    if settings["bpm_min"] > settings["bpm_max"]:
        settings["bpm_min"], settings["bpm_max"] = settings["bpm_max"], settings["bpm_min"]

    # if history_max changed, recreate the history deque preserving recent items
    if "history_max" in payload:
        try:
            new_max = int(settings.get("history_max", 1000))
        except Exception:
            new_max = 1000
        try:
            global history
            if getattr(history, "maxlen", None) != new_max:
                history = deque(history, maxlen=new_max)
        except Exception:
            pass

    return JSONResponse({"ok": True, "settings": settings})

@app.post("/api/control")
async def control(action: Dict):
    # actions: {"cmd":"start"} or {"cmd":"stop"} or {"cmd":"reset"}
    cmd = action.get("cmd", "").lower()
    if cmd == "start":
        state["running"] = True
    elif cmd == "stop":
        state["running"] = False
    elif cmd == "reset":
        state.update({
            "steps": 0,
            "distance_m": 0.0,
            "calories": 0.0,
            "bpm": 70,
            "last_update": time.time()
        })
    else:
        return JSONResponse({"ok": False, "error": "unknown cmd"}, status_code=400)
    return JSONResponse({"ok": True, "state": state})

# convenience: run uvicorn by `python -m uvicorn main:app --reload` or similar.
