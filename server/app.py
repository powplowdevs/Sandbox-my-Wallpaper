from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import time, json, threading, os
import numpy as np

WIDTH = 480
HEIGHT = 270
TICK_RATE = 60

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

grid = [0] * (WIDTH * HEIGHT)
tick = 0
action_queue = []
lock = threading.Lock()

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "data", "config.json")
EVENTS_PATH = os.path.join(os.path.dirname(__file__), "data", "events.jsonl")
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)


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

@app.route("/events", methods=["GET"])
def get_events():
    since_tick = request.args.get("since_tick", type=int)

    if since_tick is None:
        return jsonify({"error": "since_tick is required"}), 400

    events = []

    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            event = json.loads(line)
            if event["tick"] > since_tick:
                events.append(event)

    return jsonify(events)

# WebSocket routes
# @app.route("/event", methods=["POST"])
# def event():
#     with lock:
#         action_queue.append(request.json)
#     return jsonify(ok=True)


# @app.route("/snapshot")
# def snapshot():
#     with lock:
#         return jsonify(latest_snapshot)


@socketio.on("event")
def event(event):
    with lock:
        action_queue.append(event)



def serverLoop():
    global tick

    dt = 1 / TICK_RATE
    while True:
        start = time.time()

        with lock:
            for evt in action_queue:
                evt["tick"] = tick
                applyBrush(evt)
                with open(EVENTS_PATH, "a") as f:
                    f.write(json.dumps(evt) + "\n")
            action_queue.clear()

            step(grid)
            tick += 1

            arr = np.array(grid, dtype=np.uint8)
            data = arr.flatten().tobytes()
            socketio.emit("snapshot", data, to=None)

            # latest_snapshot = {
            #     "tick": tick,
            #     "grid": grid[:]  # copy
            # }

        time.sleep(max(0, dt - (time.time() - start)))


threading.Thread(target=serverLoop, daemon=True).start()

if __name__ == "__main__":
    app.run(threaded=True)
