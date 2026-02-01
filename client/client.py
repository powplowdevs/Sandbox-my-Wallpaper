import os
import json
import pygame
import time

# --- Simulation settings ---
WIDTH = 480
HEIGHT = 270
TICK_RATE = 60  # 60 Hz
TICK_DURATION = 1.0 / TICK_RATE  # seconds per tick

grid = [0] * (WIDTH * HEIGHT)
tick = 0

EVENT_PATH = os.path.join(os.path.dirname(__file__), "data", "events.jsonl")

# --- Helper functions ---
def idx(x, y):
    """Convert 2D coords to 1D index."""
    return y * WIDTH + x

def step(grid):
    """Perform one simulation step (sand falling)."""
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
    """Apply a brush event to the grid."""
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

# --- Load events from JSONL file ---
def loadEvents():
    events = []
    if os.path.exists(EVENT_PATH):
        with open(EVENT_PATH, "r") as f:
            for line in f:
                evt = json.loads(line)
                events.append(evt)
    return events

events = loadEvents()
event_index = 0  # which event to process next

# --- Pygame setup ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sand Simulation")
clock = pygame.time.Clock()

# Optional: map numeric values to RGB colors
COLOR_MAP = {
    0: (0, 0, 0),       # empty
    1: (194, 178, 128), # sand-like color
    2: (255, 0, 0),     # example for other materials
}

running = True
last_time = time.time()
accumulator = 0.0

# --- Main loop ---
while running:
    now = time.time()
    delta = now - last_time
    last_time = now
    accumulator += delta

    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Simulation steps at fixed 60Hz ---
    while accumulator >= TICK_DURATION:
        tick += 1

        # Step the simulation
        step(grid)

        # Apply any events that match this tick
        while event_index < len(events) and events[event_index]["tick"] == tick:
            applyBrush(events[event_index])
            event_index += 1

        accumulator -= TICK_DURATION

    # --- Draw the grid ---
    for y in range(HEIGHT):
        for x in range(WIDTH):
            color = COLOR_MAP.get(grid[idx(x, y)], (255, 255, 255))
            screen.set_at((x, y), color)

    pygame.display.flip()
    clock.tick(120)  # limit max FPS to 120 (simulation is decoupled)

pygame.quit()
