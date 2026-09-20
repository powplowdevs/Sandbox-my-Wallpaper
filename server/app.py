from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import time, json, threading, os, random
import numpy as np

WIDTH = 480
HEIGHT = 270
TICK_RATE = 30
SNAPSHOT_RATE = 30

# Input limits
MIN_RADIUS = 1
MAX_RADIUS = 10
MIN_COLOR = 1
MAX_COLOR = 7

STALL_CHANCE = 0.08      # chance a falling grain hesitates for a tick
DRIFT_CHANCE = 0.20      # chance a falling grain drifts diagonally instead of straight down
SPAWN_DENSITY = 0.55     # fraction of brush cells that actually get a grain
BRUSH_JITTER = 1         # brush centre is nudged by up to +/- this many cells

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

grid = bytearray(WIDTH * HEIGHT)
tick = 0
pending = {}   # sid -> latest validated action (max one per client per tick)
lock = threading.Lock()


# Sand simulation functions
def idx(x, y):
    return y * WIDTH + x

def step(grid):
    rnd = random.random
    W = WIDTH
    for y in range(HEIGHT - 2, -1, -1):
        row = y * W
        below_row = row + W
        # random scan direction per row so there's no left/right bias
        xs = range(W) if rnd() < 0.5 else range(W - 1, -1, -1)
        for x in xs:
            i = row + x
            v = grid[i]
            if not v:
                continue

            r = rnd()
            b = below_row + x

            if not grid[b]:
                # free fall, but grains hesitate / wander a bit so shapes smear
                if r < STALL_CHANCE:
                    continue
                if r < STALL_CHANCE + DRIFT_CHANCE:
                    nx = x + (1 if r < STALL_CHANCE + DRIFT_CHANCE / 2 else -1)
                    if 0 <= nx < W and not grid[below_row + nx]:
                        grid[below_row + nx] = v
                        grid[i] = 0
                        continue
                grid[b] = v
                grid[i] = 0
            else:
                # blocked: slide down a random diagonal, try the other side if that's full
                d = 1 if r < 0.5 else -1
                for nx in (x + d, x - d):
                    if 0 <= nx < W and not grid[below_row + nx]:
                        grid[below_row + nx] = v
                        grid[i] = 0
                        break

def applyBrush(evt):
    r = evt["radius"]
    action = evt["action"]
    color = evt["color"]
    # nudge the centre so nobody can place grains pixel-perfectly
    x = evt["x"] + random.randint(-BRUSH_JITTER, BRUSH_JITTER)
    y = evt["y"] + random.randint(-BRUSH_JITTER, BRUSH_JITTER)
    rnd = random.random

    for cy in range(-r, r + 1):
        for cx in range(-r, r + 1):
            if cx * cx + cy * cy > r * r:
                continue
            px, py = x + cx, y + cy
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                i = idx(px, py)
                if action == 1:
                    if grid[i] == 0 and rnd() < SPAWN_DENSITY:
                        grid[i] = color
                else:
                    grid[i] = 0


def _int_in(v, lo, hi):
    # type() check rejects bools, floats, strings, None, etc.
    return type(v) is int and lo <= v <= hi

def validateEvent(evt):
    """Return a clean action dict, or None if anything is off."""
    if not isinstance(evt, dict):
        return None
    action = evt.get("action")
    x, y = evt.get("x"), evt.get("y")
    radius = evt.get("radius")
    color = evt.get("color", MIN_COLOR)
    if not (_int_in(action, 1, 2)
            and _int_in(x, 0, WIDTH - 1)
            and _int_in(y, 0, HEIGHT - 1)
            and _int_in(radius, MIN_RADIUS, MAX_RADIUS)
            and _int_in(color, MIN_COLOR, MAX_COLOR)):
        return None
    # rebuild instead of trusting the incoming dict (drops any extra junk keys)
    return {"action": action, "x": x, "y": y, "radius": radius, "color": color}


# Flask routes
@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("event")
def event(evt):
    clean = validateEvent(evt)
    if clean is None:
        return
    with lock:
        # one brush per client per tick: a newer event just replaces the old one
        pending[request.sid] = clean

@socketio.on("disconnect")
def handle_disconnect(*args):
    with lock:
        pending.pop(request.sid, None)

def serverLoop():
    global tick

    dt = 1 / TICK_RATE
    emit_every = max(1, TICK_RATE // SNAPSHOT_RATE)

    while True:
        start = time.time()

        with lock:
            try:
                for evt in pending.values():
                    applyBrush(evt)
                pending.clear()

                step(grid)
                tick += 1

                if tick % emit_every == 0:
                    socketio.emit("snapshot", bytes(grid), to=None)
            except Exception as e:
                # never let one bad tick kill the sim thread
                pending.clear()
                print("tick error:", repr(e))

        socketio.sleep(max(0, dt - (time.time() - start)))


backgroundThread = None
threadLock = threading.Lock()

@socketio.on('connect')
def handle_connect():
    global backgroundThread
    with threadLock:
        if backgroundThread is None:
            backgroundThread = socketio.start_background_task(serverLoop)
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
