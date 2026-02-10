import pygame, time, ctypes
from pygame.locals import *
from ctypes import windll
import socketio
import numpy as np

pygame.init()

# Sand SIM vars
WIDTH = 480
HEIGHT = 270
TICK_RATE = 30
grid = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
clock = pygame.time.Clock()
lastTime = time.time()

COLORS = {
    1: (255, 0, 0),
    2: (255, 127, 0),
    3: (255, 255, 0),
    4: (0, 255, 0),
    5: (0, 0, 255),
    6: (75, 0, 130),
    7: (148, 0, 211),
}
colorLut = np.zeros((256, 3), dtype=np.uint8)
for k, v in COLORS.items():
    colorLut[k] = v


# Win32 extended window styles and layered window attributes
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
LWA_COLORKEY = 0x1

# SocketIO
socket = socketio.Client()
socket.connect('https://sandbox-my-desktop.onrender.com')


# Set up fullscreen transparent window
monitorsize = ctypes.windll.user32
resolution_X = monitorsize.GetSystemMetrics(0)
resolution_Y = monitorsize.GetSystemMetrics(1)
screen = pygame.display.set_mode((resolution_X, resolution_Y), pygame.NOFRAME)
logicalSurface = pygame.Surface((WIDTH, HEIGHT))
hwnd = pygame.display.get_wm_info()['window']
GetWindowLong = windll.user32.GetWindowLongW
SetWindowLong = windll.user32.SetWindowLongW
SetLayeredWindowAttributes = windll.user32.SetLayeredWindowAttributes
set_window_pos = windll.user32.SetWindowPos
old_style = GetWindowLong(hwnd, GWL_EXSTYLE)
new_style = old_style | WS_EX_LAYERED
new_style |= WS_EX_TRANSPARENT
SetWindowLong(hwnd, GWL_EXSTYLE, new_style)
colorkey = 0x000000
SetLayeredWindowAttributes(hwnd, colorkey, 0, LWA_COLORKEY)

# Sand simulation functions
def idx(x, y):
    return y * WIDTH + x   

#SocketIO event handlers
@socket.on("snapshot")
def onSnapshot(data):
    global grid
    gridBytes = data
    arr = np.frombuffer(gridBytes, dtype=np.uint8)
    grid = arr.reshape((270, 480)).tolist()



 


# Main loop
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()

    # loop gird and grab each cells color
    rgb = colorLut[grid]

    # display to logical surface
    pygame.surfarray.blit_array(logicalSurface, rgb.swapaxes(0, 1))

    # Scale and display
    scaled = pygame.transform.scale(logicalSurface, (resolution_X, resolution_Y))
    screen.blit(scaled, (0, 0))

    # Keep on top
    set_window_pos(hwnd, 1, 0, 0, 0, 0, 0x0002 | 0x0001)

    pygame.display.update()
    clock.tick(TICK_RATE)
