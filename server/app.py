from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import time, json, threading, os
import numpy as np

WIDTH = 480
HEIGHT = 270
TICK_RATE = 60
SNAPSHOT_RATE = 75

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

grid = bytearray(WIDTH * HEIGHT)
tick = 0
action_queue = []
lock = threading.Lock()


# Sand simulation functions
def idx(x, y):
    return y * WIDTH + x

def step(grid):
    for y in range(HEIGHT - 2, -1, -1):
        for x in range(WIDTH):
            i = idx(x, y)
            v = grid[i]
            if not v:
                continue

            below = idx(x, y + 1)
            if not grid[below]:
                grid[below] = v
                grid[i] = 0
            else:
                d = -1 if ((x + y) & 1) else 1
                nx = x + d
                if 0 <= nx < WIDTH:
                    diag = idx(nx, y + 1)
                    if not grid[diag]:
                        grid[diag] = v
                        grid[i] = 0

def applyBrush(evt):
    x, y, r = evt["x"], evt["y"], evt["radius"]
    action = evt["action"]
    color = evt.get("color", 1)

    for cy in range(-r, r + 1):
        for cx in range(-r, r + 1):
            if cx * cx + cy * cy > r * r:
                continue
            px, py = x + cx, y + cy
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                i = idx(px, py)
                if action == 1 and grid[i] == 0:
                    grid[i] = color
                elif action == 2:
                    grid[i] = 0


# Flask routes
@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("event")
def event(event):
    with lock:
        action_queue.append(event)

def serverLoop():
    global tick

    dt = 1 / TICK_RATE
    emit_every = max(1, TICK_RATE // SNAPSHOT_RATE)

    while True:
        start = time.time()

        with lock:
            for evt in action_queue:
                evt["tick"] = tick
                applyBrush(evt)
            action_queue.clear()

            step(grid)
            tick += 1

            if tick % emit_every == 0:
                socketio.emit("snapshot", bytes(grid), to=None)

        socketio.sleep(max(0, dt - (time.time() - start)))


socketio.start_background_task(serverLoop)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)

