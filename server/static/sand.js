const socket = io("");

const WIDTH = 480;
const HEIGHT = 270;
const SCALE = 4;

const canvas = document.getElementById("sand");
canvas.width = WIDTH;
canvas.height = HEIGHT;
// canvas.style.width = WIDTH * SCALE + "px";
// canvas.style.height = HEIGHT * SCALE + "px";

function resizeCanvas() {
    const wrapper = canvas.parentElement; // canvas-wrapper
    const wrapperWidth = wrapper.clientWidth;
    const wrapperHeight = wrapper.clientHeight;

    if (wrapperWidth === 0 || wrapperHeight === 0) {
        requestAnimationFrame(resizeCanvas);
        return;
    }

    const scaleX = wrapperWidth / WIDTH;
    const scaleY = wrapperHeight / HEIGHT;

    // Keep aspect ratio
    const scale = Math.min(scaleX, scaleY);

    canvas.style.width = WIDTH * scale + "px";
    canvas.style.height = HEIGHT * scale + "px";
}

window.addEventListener("resize", resizeCanvas);
resizeCanvas();


const ctx = canvas.getContext("2d");
ctx.imageSmoothingEnabled = false;
const grid = new Uint8Array(WIDTH * HEIGHT);

const COLORS = {
  1: "#ff0000",
  2: "#ff7f00",
  3: "#ffff00",
  4: "#00ff00",
  5: "#0000ff",
  6: "#4b0082",
  7: "#9400d3",
};

let currentColor = 1;
let mode = "spawn";
let radius = 4;

// UI 
const sizeSlider = document.getElementById("size-slider");
sizeSlider.oninput = () => {
    radius = Number(sizeSlider.value);
};

const palette = document.getElementById("palette"); 
for (const c in COLORS) { 
    const b = document.createElement("button"); 
    b.style.background = COLORS[c]; 
    b.onclick = () => currentColor = Number (c); 
    palette.appendChild(b); 
}

// spawn and delte button
document.getElementById("mode-spawn").onclick = () => mode = "spawn";
document.getElementById("mode-delete").onclick = () => mode = "delete";

const idx = (x, y) => y * WIDTH + x;


function sendEvent(evt) {
    socket.emit("event", evt);
}


// LOCAL PREDICTION
function applyBrushLocal(x, y, r, mode, color) {
    for (let cy = -r; cy <= r; cy++) {
        for (let cx = -r; cx <= r; cx++) {
            if (cx*cx + cy*cy > r*r) continue;
            const px = x + cx, py = y + cy;
            if (px < 0 || py < 0 || px >= WIDTH || py >= HEIGHT) continue;
            const i = idx(px, py);
            if (mode === "spawn" && grid[i] === 0) grid[i] = color;
            if (mode === "delete") grid[i] = 0;
        }
    }
}


canvas.addEventListener("mousemove", e => {
    if (!(e.buttons & 1)) return;

    const r = canvas.getBoundingClientRect();
    const x = Math.floor((e.clientX - r.left) * WIDTH / r.width);
    const y = Math.floor((e.clientY - r.top) * HEIGHT / r.height);
    if (x < 0 || y < 0 || x >= WIDTH || y >= HEIGHT) return;

    applyBrushLocal(x, y, radius, mode, currentColor);

    sendEvent({
        action: mode === "spawn" ? 1 : 2,
        x, y,
        radius,
        color: currentColor
    });
});


socket.on("snapshot", msg => {
    const byteArray = new Uint8Array(msg);
    grid.set(byteArray);
});

async function syncFromServer() {
    socket.once("snapshot", msg => {
        const byteArray = new Uint8Array(msg);
        grid.set(byteArray);
    });
}


function draw() {
    const img = ctx.getImageData(0, 0, WIDTH, HEIGHT);
    const d = img.data;

    for (let i = 0; i < grid.length; i++) {
        const v = grid[i];
        const o = i * 4;
        if (v) {
            const c = COLORS[v];
            d[o]   = parseInt(c.slice(1,3),16);
            d[o+1] = parseInt(c.slice(3,5),16);
            d[o+2] = parseInt(c.slice(5,7),16);
            d[o+3] = 255;
        } else {
            d[o+3] = 0;
        }
    }

    ctx.putImageData(img, 0, 0);
}


function loop(t) {
    draw();
    requestAnimationFrame(loop);
}

requestAnimationFrame(loop);
