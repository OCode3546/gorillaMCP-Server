// __APP_TITLE__ — HTML5 canvas arcade game.
// Dodge the falling hazards, collect stars. Arrow keys / A-D to move, P to pause,
// Enter or Space to start. On touch screens, drag to move and tap to start.
(() => {
  "use strict";

  const CONFIG = {
    width: 480,
    height: 720,
    playerSpeed: 360,          // px per second
    startLives: 3,
    hazardBaseSpeed: 160,      // px per second at level 1
    hazardSpeedPerLevel: 35,
    hazardSpawnEvery: 0.9,     // seconds at level 1
    pickupSpawnEvery: 2.5,
    pointsPerLevel: 100,
    invulnerableTime: 1.5,     // seconds after being hit
    storageKey: "__APP_NAME__:highscore",
  };

  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");

  // ------------------------------------------------------------------ input

  const keys = new Set();
  let touchX = null;

  window.addEventListener("keydown", (e) => {
    keys.add(e.code);
    if (["ArrowLeft", "ArrowRight", "Space"].includes(e.code)) e.preventDefault();
    if (e.code === "Enter" || e.code === "Space") onAction();
    if (e.code === "KeyP" || e.code === "Escape") togglePause();
  });
  window.addEventListener("keyup", (e) => keys.delete(e.code));

  function canvasX(clientX) {
    const rect = canvas.getBoundingClientRect();
    return ((clientX - rect.left) / rect.width) * CONFIG.width;
  }
  canvas.addEventListener("pointerdown", (e) => { touchX = canvasX(e.clientX); onAction(); });
  canvas.addEventListener("pointermove", (e) => { if (e.buttons || e.pointerType === "touch") touchX = canvasX(e.clientX); });
  window.addEventListener("pointerup", () => { touchX = null; });

  // ------------------------------------------------------------------ helpers

  const rand = (min, max) => min + Math.random() * (max - min);
  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
  const circlesHit = (a, b) => Math.hypot(a.x - b.x, a.y - b.y) < a.r + b.r;

  function loadHighScore() {
    try { return Number(localStorage.getItem(CONFIG.storageKey)) || 0; } catch { return 0; }
  }
  function saveHighScore(value) {
    try { localStorage.setItem(CONFIG.storageKey, String(value)); } catch { /* storage unavailable */ }
  }

  // ------------------------------------------------------------------ entities

  class Player {
    constructor() {
      this.x = CONFIG.width / 2;
      this.y = CONFIG.height - 80;
      this.r = 18;
      this.invulnerable = 0;
    }
    update(dt) {
      let dir = 0;
      if (keys.has("ArrowLeft") || keys.has("KeyA")) dir -= 1;
      if (keys.has("ArrowRight") || keys.has("KeyD")) dir += 1;
      if (touchX !== null) dir = clamp((touchX - this.x) / 40, -1, 1);
      this.x = clamp(this.x + dir * CONFIG.playerSpeed * dt, this.r, CONFIG.width - this.r);
      this.invulnerable = Math.max(0, this.invulnerable - dt);
    }
    draw() {
      if (this.invulnerable > 0 && Math.floor(this.invulnerable * 10) % 2 === 0) return; // blink
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.fillStyle = "#5ad1ff";
      ctx.beginPath();
      ctx.moveTo(0, -this.r - 4);
      ctx.lineTo(this.r, this.r);
      ctx.lineTo(0, this.r * 0.5);
      ctx.lineTo(-this.r, this.r);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = "#ffb347";
      ctx.fillRect(-4, this.r * 0.6, 8, 6 + Math.random() * 6); // engine flame
      ctx.restore();
    }
  }

  class Hazard {
    constructor(speed) {
      this.r = rand(14, 30);
      this.x = rand(this.r, CONFIG.width - this.r);
      this.y = -this.r;
      this.vy = speed * rand(0.8, 1.25);
      this.spin = rand(-2, 2);
      this.angle = 0;
      this.points = Array.from({ length: 8 }, (_, i) => {
        const a = (i / 8) * Math.PI * 2;
        return [Math.cos(a) * this.r * rand(0.75, 1.05), Math.sin(a) * this.r * rand(0.75, 1.05)];
      });
    }
    update(dt) {
      this.y += this.vy * dt;
      this.angle += this.spin * dt;
    }
    get gone() { return this.y - this.r > CONFIG.height; }
    draw() {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.angle);
      ctx.fillStyle = "#8a6f5a";
      ctx.strokeStyle = "#c4a484";
      ctx.lineWidth = 2;
      ctx.beginPath();
      this.points.forEach(([px, py], i) => (i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)));
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    }
  }

  class Pickup {
    constructor(speed) {
      this.r = 12;
      this.x = rand(this.r, CONFIG.width - this.r);
      this.y = -this.r;
      this.vy = speed * 0.7;
      this.t = 0;
    }
    update(dt) {
      this.y += this.vy * dt;
      this.t += dt;
    }
    get gone() { return this.y - this.r > CONFIG.height; }
    draw() {
      const pulse = 1 + Math.sin(this.t * 8) * 0.15;
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.scale(pulse, pulse);
      ctx.fillStyle = "#ffe066";
      ctx.beginPath();
      for (let i = 0; i < 10; i++) {
        const a = (i / 10) * Math.PI * 2 - Math.PI / 2;
        const rad = i % 2 === 0 ? this.r : this.r * 0.45;
        ctx.lineTo(Math.cos(a) * rad, Math.sin(a) * rad);
      }
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }
  }

  const stars = Array.from({ length: 80 }, () => ({
    x: rand(0, CONFIG.width), y: rand(0, CONFIG.height), s: rand(0.5, 2), v: rand(20, 80),
  }));

  // ------------------------------------------------------------------ game state

  let state = "menu"; // menu | playing | paused | gameover
  let player, hazards, pickups, score, lives, level, hazardTimer, pickupTimer, highScore = loadHighScore();

  function reset() {
    player = new Player();
    hazards = [];
    pickups = [];
    score = 0;
    lives = CONFIG.startLives;
    level = 1;
    hazardTimer = 0;
    pickupTimer = CONFIG.pickupSpawnEvery;
  }

  function onAction() {
    if (state === "menu" || state === "gameover") {
      reset();
      state = "playing";
    }
  }

  function togglePause() {
    if (state === "playing") state = "paused";
    else if (state === "paused") state = "playing";
  }

  function hazardSpeed() {
    return CONFIG.hazardBaseSpeed + (level - 1) * CONFIG.hazardSpeedPerLevel;
  }

  function update(dt) {
    for (const s of stars) {
      s.y += s.v * dt * (state === "playing" ? 1 + level * 0.2 : 0.5);
      if (s.y > CONFIG.height) { s.y = 0; s.x = rand(0, CONFIG.width); }
    }
    if (state !== "playing") return;

    player.update(dt);

    hazardTimer -= dt;
    if (hazardTimer <= 0) {
      hazards.push(new Hazard(hazardSpeed()));
      hazardTimer = Math.max(0.25, CONFIG.hazardSpawnEvery - (level - 1) * 0.07);
    }
    pickupTimer -= dt;
    if (pickupTimer <= 0) {
      pickups.push(new Pickup(hazardSpeed()));
      pickupTimer = CONFIG.pickupSpawnEvery;
    }

    hazards.forEach((h) => h.update(dt));
    pickups.forEach((p) => p.update(dt));

    for (const h of hazards) {
      if (player.invulnerable === 0 && circlesHit(player, h)) {
        h.y = CONFIG.height + 999; // remove on next filter
        lives -= 1;
        player.invulnerable = CONFIG.invulnerableTime;
        if (lives <= 0) return gameOver();
      }
    }
    for (const p of pickups) {
      if (circlesHit(player, p)) {
        p.y = CONFIG.height + 999;
        score += 25;
      }
    }

    // Survival points: 10 per second.
    score += dt * 10;
    level = 1 + Math.floor(score / CONFIG.pointsPerLevel);

    hazards = hazards.filter((h) => !h.gone);
    pickups = pickups.filter((p) => !p.gone);
  }

  function gameOver() {
    state = "gameover";
    if (Math.floor(score) > highScore) {
      highScore = Math.floor(score);
      saveHighScore(highScore);
    }
  }

  // ------------------------------------------------------------------ rendering

  function text(str, x, y, size = 20, color = "#e8eaed", align = "center") {
    ctx.fillStyle = color;
    ctx.font = `bold ${size}px system-ui, sans-serif`;
    ctx.textAlign = align;
    ctx.fillText(str, x, y);
  }

  function render() {
    ctx.fillStyle = "#0b0e17";
    ctx.fillRect(0, 0, CONFIG.width, CONFIG.height);
    ctx.fillStyle = "#ffffff";
    for (const s of stars) ctx.fillRect(s.x, s.y, s.s, s.s);

    const cx = CONFIG.width / 2;
    const cy = CONFIG.height / 2;

    if (state === "menu") {
      text("__APP_TITLE__", cx, cy - 60, 40);
      text("Dodge the rocks, grab the stars", cx, cy - 10, 18, "#9aa0a6");
      text("Press Enter / Tap to start", cx, cy + 40, 20, "#5ad1ff");
      text(`High score: ${highScore}`, cx, cy + 90, 16, "#9aa0a6");
      return;
    }

    pickups.forEach((p) => p.draw());
    hazards.forEach((h) => h.draw());
    player.draw();

    text(`Score ${Math.floor(score)}`, 16, 32, 18, "#e8eaed", "left");
    text(`Level ${level}`, cx, 32, 18);
    text("♥".repeat(Math.max(0, lives)), CONFIG.width - 16, 32, 20, "#ff6b6b", "right");

    if (state === "paused") {
      text("Paused", cx, cy, 36);
      text("Press P to resume", cx, cy + 40, 18, "#9aa0a6");
    } else if (state === "gameover") {
      ctx.fillStyle = "rgba(0, 0, 0, 0.55)";
      ctx.fillRect(0, 0, CONFIG.width, CONFIG.height);
      text("Game over", cx, cy - 40, 40, "#ff6b6b");
      text(`Score: ${Math.floor(score)}   Best: ${highScore}`, cx, cy + 5, 20);
      text("Press Enter / Tap to play again", cx, cy + 50, 18, "#5ad1ff");
    }
  }

  // ------------------------------------------------------------------ loop

  let last = performance.now();
  function frame(now) {
    const dt = Math.min(0.05, (now - last) / 1000); // clamp so a background tab doesn't teleport everything
    last = now;
    update(dt);
    render();
    requestAnimationFrame(frame);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden && state === "playing") state = "paused";
  });

  reset();
  requestAnimationFrame(frame);
})();
