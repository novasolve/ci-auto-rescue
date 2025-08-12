// Plumber Platformer — single-file, dependency-free HTML5 Canvas platformer
// Opens directly via file://

// Constants and setup
export const TILE_SIZE = 32;
const COLORS = {
  sky: '#8ecae6',
  ground: '#8b5a2b',
  groundTop: '#b07c3c',
  hazard: '#d00000',
  coin: '#ffd166',
  flagPole: '#2a9d8f',
  flagCap: '#52b788',
  player: '#2563eb',
  enemy: '#f59e0b',
  hud: '#0b1526',
  hudText: '#ffffff'
};

const GRAVITY = 1800;
const MAX_FALL_SPEED = 2000;
const MOVE_ACCEL = 2600;
const AIR_ACCEL = 1800;
const FRICTION = 2200;
const MAX_RUN_SPEED = 240;
const JUMP_VELOCITY = 700;

export let canvas, ctx;
function setupCanvas() {
  canvas = document.getElementById('game');
  ctx = canvas.getContext('2d');
  const dpr = Math.max(1, Math.floor(window.devicePixelRatio || 1));
  const w = canvas.width;
  const h = canvas.height;
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { dpr, w, h };
}

// Input handler
class Input {
  constructor() {
    this.down = new Set();
    this.just = new Set();
    window.addEventListener('keydown', (e) => {
      const code = e.code;
      if (!this.down.has(code)) this.just.add(code);
      this.down.add(code);
    });
    window.addEventListener('keyup', (e) => {
      this.down.delete(e.code);
    });
  }
  pressed(code) { return this.down.has(code); }
  wasPressed(code) { return this.just.has(code); }
  consumePressed(codes) {
    for (const c of (Array.isArray(codes) ? codes : [codes])) {
      if (this.just.has(c)) { this.just.delete(c); return true; }
    }
    return false;
  }
  endFrame() { this.just.clear(); }
}

// Math/AABB helpers
class Rect {
  constructor(x, y, w, h) { this.x = x; this.y = y; this.w = w; this.h = h; }
  get left() { return this.x; }
  get right() { return this.x + this.w; }
  get top() { return this.y; }
  get bottom() { return this.y + this.h; }
  intersects(o) { return !(this.right <= o.left || this.left >= o.right || this.bottom <= o.top || this.top >= o.bottom); }
}
const clamp = (v, mn, mx) => Math.max(mn, Math.min(mx, v));
const sign = (x) => (x < 0 ? -1 : x > 0 ? 1 : 0);
const tileCoords = (px, py) => ({ tx: Math.floor(px / TILE_SIZE), ty: Math.floor(py / TILE_SIZE) });

// Tilemap and world
const Tile = { EMPTY: 0, SOLID: 1, HAZARD: 2, COIN: 3, FLAG: 4 };
const isSolid = (id) => id === Tile.SOLID;
const isHazard = (id) => id === Tile.HAZARD;
const isCoin = (id) => id === Tile.COIN;
const isFlag = (id) => id === Tile.FLAG;

const world = {
  tilemap: null,
  camera: { x: 0, y: 0, w: 800, h: 480, update(player, bounds) {
    this.x = player.x + player.w / 2 - this.w / 2;
    this.y = player.y + player.h / 2 - this.h / 2;
    this.x = clamp(this.x, 0, Math.max(0, bounds.pixelWidth - this.w));
    this.y = clamp(this.y, 0, Math.max(0, bounds.pixelHeight - this.h));
  } },
  entities: [],
  player: null,
  coins: 0,
  lives: 3,
  won: false,
  paused: false,
  gameOver: false,
  spawn: { x: 0, y: 0 }
};

function makeTilemap(width, height, tiles) {
  const data = tiles ? tiles.slice() : new Array(width * height).fill(Tile.EMPTY);
  return {
    width, height, tiles: data,
    get(x, y) { if (x < 0 || y < 0 || x >= width || y >= height) return Tile.SOLID; return data[y * width + x]; },
    set(x, y, v) { if (x < 0 || y < 0 || x >= width || y >= height) return; data[y * width + x] = v; },
    get pixelWidth() { return width * TILE_SIZE; },
    get pixelHeight() { return height * TILE_SIZE; }
  };
}
function getTileAtPixel(px, py) { const { tx, ty } = tileCoords(px, py); return world.tilemap.get(tx, ty); }
function setTileAtPixel(px, py, id) { const { tx, ty } = tileCoords(px, py); world.tilemap.set(tx, ty, id); }

// Entities
class Entity extends Rect {
  constructor(x, y, w, h) { super(x, y, w, h); this.vx = 0; this.vy = 0; this.dir = 1; this.grounded = false; this.dead = false; }
  update(dt, world) {}
  render(ctx) {}
}

class Player extends Entity {
  constructor(x, y) {
    super(x, y, 22, 28);
    this.coyote = 0; this.jumpBuf = 0;
  }
  handleInput(input, dt) {
    const left = input.pressed('ArrowLeft') || input.pressed('KeyA');
    const right = input.pressed('ArrowRight') || input.pressed('KeyD');
    const accel = this.grounded ? MOVE_ACCEL : AIR_ACCEL;
    if (left && !right) this.vx -= accel * dt;
    else if (right && !left) this.vx += accel * dt;
    else if (this.grounded) {
      const f = Math.min(Math.abs(this.vx), FRICTION * dt) * sign(this.vx);
      this.vx -= f;
    }
    this.vx = clamp(this.vx, -MAX_RUN_SPEED, MAX_RUN_SPEED);
    if (this.vx !== 0) this.dir = sign(this.vx) || this.dir;

    if (input.consumePressed(['Space', 'KeyZ', 'ArrowUp', 'KeyW'])) this.jumpBuf = 0.12;
    if (this.jumpBuf > 0 && (this.grounded || this.coyote > 0)) {
      this.vy = -JUMP_VELOCITY;
      this.grounded = false;
      this.coyote = 0;
      this.jumpBuf = 0;
    }
    this.jumpBuf -= dt; this.coyote -= dt;
  }
  update(dt, world) {
    this.handleInput(world.input, dt);
  }
  render(ctx) {
    ctx.fillStyle = COLORS.player;
    ctx.fillRect(this.x, this.y, this.w, this.h);
    ctx.fillStyle = '#ffffff';
    const eyeX = this.dir >= 0 ? this.x + this.w - 8 : this.x + 4;
    ctx.fillRect(eyeX, this.y + 6, 3, 3);
  }
}

class Enemy extends Entity {
  constructor(x, y) { super(x, y, 22, 22); this.speed = 60; this.vx = -this.speed; this.dir = -1; }
  update(dt, world) {
    // maintain horizontal patrol speed
    this.vx = this.dir * this.speed;
    // edge detection: if the tile ahead and below is empty, flip
    const aheadX = this.x + (this.vx > 0 ? this.w + 2 : -2);
    const footY = this.y + this.h + 2;
    const belowAhead = getTileAtPixel(aheadX, footY);
    if (!isSolid(belowAhead)) this.dir = -this.dir;
  }
  render(ctx) {
    ctx.fillStyle = COLORS.enemy;
    ctx.fillRect(this.x, this.y, this.w, this.h);
  }
}

// Collision and interactions
function moveAndCollide(e, dt) {
  // integrate gravity
  e.vy = clamp(e.vy + GRAVITY * dt, -Infinity, MAX_FALL_SPEED);
  e.grounded = false;

  // horizontal sweep
  let nx = e.x + e.vx * dt;
  if (e.vx !== 0) {
    const minY = Math.floor(e.top / TILE_SIZE);
    const maxY = Math.floor((e.bottom - 1) / TILE_SIZE);
    if (e.vx > 0) {
      const right = Math.floor((nx + e.w - 1) / TILE_SIZE);
      for (let ty = minY; ty <= maxY; ty++) {
        if (isSolid(world.tilemap.get(right, ty))) {
          nx = right * TILE_SIZE - e.w;
          e.vx = 0; break;
        }
      }
    } else {
      const left = Math.floor(nx / TILE_SIZE);
      for (let ty = minY; ty <= maxY; ty++) {
        if (isSolid(world.tilemap.get(left, ty))) {
          nx = (left + 1) * TILE_SIZE;
          e.vx = 0; break;
        }
      }
    }
  }
  e.x = nx;

  // vertical sweep
  let ny = e.y + e.vy * dt;
  if (e.vy !== 0) {
    const minX = Math.floor(e.left / TILE_SIZE);
    const maxX = Math.floor((e.right - 1) / TILE_SIZE);
    if (e.vy > 0) {
      const bottom = Math.floor((ny + e.h - 1) / TILE_SIZE);
      for (let tx = minX; tx <= maxX; tx++) {
        if (isSolid(world.tilemap.get(tx, bottom))) {
          ny = bottom * TILE_SIZE - e.h;
          e.vy = 0; e.grounded = true; if (e instanceof Player) e.coyote = 0.08; break;
        }
      }
    } else {
      const top = Math.floor(ny / TILE_SIZE);
      for (let tx = minX; tx <= maxX; tx++) {
        if (isSolid(world.tilemap.get(tx, top))) {
          ny = (top + 1) * TILE_SIZE;
          e.vy = 0; break;
        }
      }
    }
  }
  e.y = ny;

  // interactions with tiles in current AABB
  const tminX = Math.floor(e.left / TILE_SIZE), tmaxX = Math.floor((e.right - 1) / TILE_SIZE);
  const tminY = Math.floor(e.top / TILE_SIZE), tmaxY = Math.floor((e.bottom - 1) / TILE_SIZE);
  for (let ty = tminY; ty <= tmaxY; ty++) {
    for (let tx = tminX; tx <= tmaxX; tx++) {
      const id = world.tilemap.get(tx, ty);
      if (isHazard(id) && e instanceof Player) { killPlayer(); return; }
      if (isCoin(id) && e instanceof Player) { world.coins++; world.tilemap.set(tx, ty, Tile.EMPTY); }
      if (isFlag(id) && e instanceof Player) { world.won = true; }
    }
  }
}

// Rendering
function render() {
  ctx.save();
  // sky
  ctx.fillStyle = COLORS.sky;
  ctx.fillRect(0, 0, world.camera.w, world.camera.h);

  ctx.translate(-world.camera.x, -world.camera.y);
  const sx = Math.max(0, Math.floor(world.camera.x / TILE_SIZE) - 1);
  const ex = Math.min(world.tilemap.width - 1, Math.floor((world.camera.x + world.camera.w) / TILE_SIZE) + 1);
  const sy = Math.max(0, Math.floor(world.camera.y / TILE_SIZE) - 1);
  const ey = Math.min(world.tilemap.height - 1, Math.floor((world.camera.y + world.camera.h) / TILE_SIZE) + 1);

  for (let y = sy; y <= ey; y++) {
    for (let x = sx; x <= ex; x++) {
      const id = world.tilemap.get(x, y);
      const px = x * TILE_SIZE, py = y * TILE_SIZE;
      if (id === Tile.SOLID) {
        ctx.fillStyle = COLORS.ground;
        ctx.fillRect(px, py, TILE_SIZE, TILE_SIZE);
        ctx.fillStyle = COLORS.groundTop;
        ctx.fillRect(px, py, TILE_SIZE, 4);
      } else if (id === Tile.HAZARD) {
        ctx.fillStyle = COLORS.hazard;
        ctx.fillRect(px, py + TILE_SIZE / 2, TILE_SIZE, TILE_SIZE / 2);
      } else if (id === Tile.COIN) {
        ctx.fillStyle = COLORS.coin;
        ctx.beginPath();
        ctx.arc(px + TILE_SIZE / 2, py + TILE_SIZE / 2, 6, 0, Math.PI * 2);
        ctx.fill();
      } else if (id === Tile.FLAG) {
        ctx.fillStyle = COLORS.flagPole;
        ctx.fillRect(px + TILE_SIZE / 2 - 2, py + 4, 4, TILE_SIZE - 8);
        ctx.fillStyle = COLORS.flagCap;
        ctx.fillRect(px + TILE_SIZE / 2, py + 8, 12, 6);
      }
    }
  }

  for (const e of world.entities) e.render(ctx);
  if (world.player) world.player.render(ctx);
  ctx.restore();

  // HUD
  ctx.fillStyle = 'rgba(0,0,0,0.35)';
  ctx.fillRect(8, 8, 180, 40);
  ctx.fillStyle = COLORS.hudText;
  ctx.font = 'bold 16px system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial';
  ctx.fillText(`Coins: ${world.coins}`, 16, 28);
  ctx.fillText(`Lives: ${world.lives}`, 100, 28);

  if (world.paused) drawCenterText('Paused');
  if (world.won) drawCenterText('You Win! (R to restart)');
  if (world.gameOver) drawCenterText('Game Over (R to restart)');
}

function drawCenterText(t) {
  ctx.fillStyle = 'rgba(0,0,0,0.45)';
  ctx.fillRect(0, world.camera.h / 2 - 40, world.camera.w, 80);
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 28px system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial';
  const m = ctx.measureText(t);
  ctx.fillText(t, (world.camera.w - m.width) / 2, world.camera.h / 2 + 10);
}

// Level/state
function loadLevel(level) {
  world.tilemap = makeTilemap(level.width, level.height, level.tiles);
  world.entities = [];
  world.coins = 0;
  world.won = false; world.paused = false; world.gameOver = false;
  world.spawn = { x: level.spawn.x, y: level.spawn.y };
  world.player = new Player(level.spawn.x, level.spawn.y);
  for (const e of level.enemies || []) world.entities.push(new Enemy(e.x, e.y));
}

function resetGame() { loadLevel(LEVEL1); world.lives = 3; }

function killPlayer() {
  if (world.gameOver || world.won) return;
  world.lives -= 1;
  if (world.lives > 0) {
    world.player.x = world.spawn.x; world.player.y = world.spawn.y;
    world.player.vx = 0; world.player.vy = 0; world.player.grounded = false; world.player.coyote = 0; world.player.jumpBuf = 0;
  } else {
    world.gameOver = true;
  }
}

// Simple level generation
const LEVEL1 = (() => {
  const width = 100, height = 15;
  const t = new Array(width * height).fill(Tile.EMPTY);
  const at = (x, y, id) => { if (x>=0&&y>=0&&x<width&&y<height) t[y*width+x]=id; };

  // ground baseline
  for (let x = 0; x < width; x++) for (let y = 13; y < height; y++) at(x, y, Tile.SOLID);

  // some platforms
  for (let x = 8; x < 14; x++) at(x, 10, Tile.SOLID);
  for (let x = 18; x < 25; x++) at(x, 9, Tile.SOLID);
  for (let x = 30; x < 34; x++) at(x, 8, Tile.SOLID);
  for (let x = 44; x < 50; x++) at(x, 9, Tile.SOLID);
  for (let x = 64; x < 70; x++) at(x, 8, Tile.SOLID);

  // coins
  const coinPos = [ [9,9],[12,9],[19,8],[22,8],[31,7],[33,7],[45,8],[48,8],[65,7],[67,7] ];
  for (const [cx,cy] of coinPos) at(cx, cy, Tile.COIN);

  // hazards (lava pits)
  for (let x = 26; x < 30; x++) at(x, 13, Tile.HAZARD);
  for (let x = 54; x < 58; x++) at(x, 13, Tile.HAZARD);
  for (let x = 74; x < 78; x++) at(x, 13, Tile.HAZARD);

  // flag at end
  at(96, 12, Tile.FLAG);

  return {
    width, height, tiles: t,
    spawn: { x: 64, y: 8 * TILE_SIZE - 64 },
    enemies: [ { x: 18 * TILE_SIZE, y: 12 * TILE_SIZE - 22 }, { x: 47 * TILE_SIZE, y: 12 * TILE_SIZE - 22 }, { x: 68 * TILE_SIZE, y: 11 * TILE_SIZE - 22 } ]
  };
})();

// Game loop
const state = { acc: 0, last: 0, dt: 1/60, maxSteps: 5 };
let input;

function step(dt) {
  if (world.paused || world.won || world.gameOver) return;
  // player
  world.player.update(dt, world);
  moveAndCollide(world.player, dt);
  if (!world.player.grounded && world.player.vy > 0) world.player.coyote = Math.max(world.player.coyote - dt, 0);

  // enemies
  for (const en of world.entities) {
    en.update(dt, world);
    moveAndCollide(en, dt);
    // if bumped into wall, reverse
    if (Math.abs(en.vx) < 1) { en.dir = -en.dir; en.vx = en.dir * en.speed; }
  }
  // player vs enemies
  for (let i = world.entities.length - 1; i >= 0; i--) {
    const en = world.entities[i];
    if (world.player.intersects(en)) {
      if (world.player.vy > 0 && world.player.bottom <= en.top + 6) {
        world.entities.splice(i, 1);
        world.player.vy = -0.6 * JUMP_VELOCITY;
      } else {
        killPlayer(); break;
      }
    }
  }

  // camera
  world.camera.update(world.player, world.tilemap);
}

function loop(ts) {
  if (!state.last) state.last = ts;
  let delta = Math.min(0.25, (ts - state.last) / 1000);
  state.last = ts; state.acc += delta;

  // global key actions
  if (input.consumePressed(['KeyP'])) world.paused = !world.paused;
  if (input.consumePressed(['KeyR'])) resetGame();

  let steps = 0;
  while (state.acc >= state.dt && steps < state.maxSteps) {
    step(state.dt);
    input.endFrame();
    state.acc -= state.dt; steps++;
  }
  render();
  requestAnimationFrame(loop);
}

function init() {
  setupCanvas();
  input = new Input();
  world.input = input;
  loadLevel(LEVEL1);
  world.camera.w = 800; world.camera.h = 480;
  world.lives = 3;
  requestAnimationFrame(loop);
}

window.addEventListener('load', init);

// Exports for potential debugging
export { ctx, canvas, world, Input, Rect, moveAndCollide, loadLevel, resetGame };
