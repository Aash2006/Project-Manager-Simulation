// Space Shooter Minigame
class SpaceShooter {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width;
    this.height = this.canvas.height;
    
    // Game state
    this.gameRunning = false;
    this.score = 0;
    this.lives = 3;
    this.level = 1;
    
    // Player ship
    this.player = {
      x: this.width / 2 - 25,
      y: this.height - 80,
      width: 50,
      height: 50,
      speed: 3,  
      color: '#667eea'
    };
    
    // Controls
    this.keys = {};
    this.lastShot = 0;
    this.shootCooldown = 250; // ms
    
    // Bullets
    this.bullets = [];
    this.bulletSpeed = 7;
    
    // Bugs (enemies)
    this.bugs = [];
    this.bugSpeed = 1;  
    this.bugSpawnRate = 1500; // ms
    this.lastBugSpawn = 0;
    this.bugsToSpawn = 12;
    this.bugsKilled = 0;
    
    // Animation
    this.animationId = null;
    
    this.setupControls();
  }
  
  setupControls() {
    document.addEventListener('keydown', (e) => {
      this.keys[e.key] = true;
      if (e.key === ' ' && this.gameRunning) {
        e.preventDefault();
        this.shoot();
      }
    });
    
    document.addEventListener('keyup', (e) => {
      this.keys[e.key] = false;
    });
  }
  
  start() {
    this.gameRunning = true;
    this.score = 0;
    this.lives = 3;
    this.bullets = [];
    this.bugs = [];
    this.bugsKilled = 0;
    this.lastBugSpawn = Date.now();
    this.player.x = this.width / 2 - 25;
    
    document.getElementById('shooter-overlay').style.display = 'none';
    this.updateUI();
    this.gameLoop();
  }
  
  gameLoop() {
    if (!this.gameRunning) return;
    
    this.update();
    this.draw();
    this.animationId = requestAnimationFrame(() => this.gameLoop());
  }
  
  update() {
    // Move player
    if (this.keys['ArrowLeft'] && this.player.x > 0) {
      this.player.x -= this.player.speed;
    }
    if (this.keys['ArrowRight'] && this.player.x < this.width - this.player.width) {
      this.player.x += this.player.speed;
    }
    
    // Update bullets
    this.bullets = this.bullets.filter(bullet => {
      bullet.y -= this.bulletSpeed;
      return bullet.y > 0;
    });
    
    // Spawn bugs
    const now = Date.now();
    if (now - this.lastBugSpawn > this.bugSpawnRate && this.bugsKilled < this.bugsToSpawn) {
      this.spawnBug();
      this.lastBugSpawn = now;
    }
    
    // Update bugs
    this.bugs = this.bugs.filter(bug => {
      bug.y += this.bugSpeed;
      
      // Bug reached bottom - lose a life
      if (bug.y > this.height) {
        this.loseLife();
        return false;
      }
      
      return true;
    });
    
    // Check collisions
    this.checkCollisions();
    
    // Check win condition
    if (this.bugsKilled >= this.bugsToSpawn && this.bugs.length === 0) {
      this.gameWin();
    }
  }
  
  draw() {
    // Clear canvas
    this.ctx.fillStyle = '#0a0e27';
    this.ctx.fillRect(0, 0, this.width, this.height);
    
    // Draw stars background
    this.drawStars();
    
    // Draw player ship
    this.drawPlayer();
    
    // Draw bullets
    this.bullets.forEach(bullet => {
      this.ctx.fillStyle = '#fbbf24';
      this.ctx.fillRect(bullet.x, bullet.y, bullet.width, bullet.height);
    });
    
    // Draw bugs
    this.bugs.forEach(bug => {
      this.ctx.font = `${bug.size}px Arial`;
      this.ctx.fillText('🐛', bug.x, bug.y);
    });
  }
  
  drawStars() {
    this.ctx.fillStyle = 'white';
    for (let i = 0; i < 50; i++) {
      const x = (i * 37) % this.width;
      const y = (i * 53) % this.height;
      this.ctx.fillRect(x, y, 2, 2);
    }
  }
  
  drawPlayer() {
    // Draw spaceship
    this.ctx.fillStyle = this.player.color;
    this.ctx.beginPath();
    // Triangle shape for ship
    this.ctx.moveTo(this.player.x + this.player.width / 2, this.player.y);
    this.ctx.lineTo(this.player.x, this.player.y + this.player.height);
    this.ctx.lineTo(this.player.x + this.player.width, this.player.y + this.player.height);
    this.ctx.closePath();
    this.ctx.fill();
    
    // Add engine glow
    this.ctx.fillStyle = '#fbbf24';
    this.ctx.fillRect(this.player.x + 15, this.player.y + this.player.height, 8, 10);
    this.ctx.fillRect(this.player.x + 27, this.player.y + this.player.height, 8, 10);
  }
  
  shoot() {
    const now = Date.now();
    if (now - this.lastShot < this.shootCooldown) return;
    
    this.bullets.push({
      x: this.player.x + this.player.width / 2 - 3,
      y: this.player.y,
      width: 6, 
      height: 15
    });
    
    this.lastShot = now;
    
    // Play sound effect (optional)
    this.playSound('shoot');
  }
  
  spawnBug() {
    const size = 30 + Math.random() * 20;
    this.bugs.push({
      x: Math.random() * (this.width - size),
      y: -size,
      size: size,
      width: size,
      height: size
    });
  }
  
  checkCollisions() {
    this.bullets.forEach((bullet, bulletIndex) => {
      this.bugs.forEach((bug, bugIndex) => {
        if (this.isColliding(bullet, bug)) {
          // Hit!
          this.bullets.splice(bulletIndex, 1);
          this.bugs.splice(bugIndex, 1);
          this.score += 10;
          this.bugsKilled++;
          this.updateUI();
          this.playSound('hit');
        }
      });
    });
  }
  
  isColliding(rect1, rect2) {

    const padding = 10; // pixels of forgiveness
    return rect1.x < rect2.x + rect2.width + padding &&
           rect1.x + rect1.width > rect2.x - padding &&
           rect1.y < rect2.y + rect2.height + padding &&
           rect1.y + rect1.height > rect2.y - padding;
  }
  
  loseLife() {
    this.lives--;
    this.updateUI();
    this.playSound('damage');
    
    if (this.lives <= 0) {
      this.gameOver();
    }
  }
  
  gameOver() {
    this.gameRunning = false;
    cancelAnimationFrame(this.animationId);
    this.showEndScreen(false);
  }
  
  gameWin() {
    this.gameRunning = false;
    cancelAnimationFrame(this.animationId);
    this.showEndScreen(true);
  }
  
  showEndScreen(won) {
    const overlay = document.getElementById('shooter-overlay');
    const title = document.getElementById('overlay-title');
    const message = document.getElementById('overlay-message');
    const startBtn = document.getElementById('shooter-start-btn');
    const results = document.getElementById('final-results');
    const finalScore = document.getElementById('final-score');
    const bugReduction = document.getElementById('bug-reduction-text');
    
    overlay.style.display = 'flex';
    startBtn.style.display = 'none';
    results.style.display = 'block';
    
    if (won) {
      title.textContent = '🎉 Victory!';
      message.textContent = 'All bugs eliminated!';
      overlay.style.background = 'rgba(72, 187, 120, 0.95)';
    } else {
      title.textContent = '💥 Game Over';
      message.textContent = 'The bugs got through...';
      overlay.style.background = 'rgba(229, 62, 62, 0.95)';
    }
    
    finalScore.textContent = this.score;
    
    // Calculate bug reduction
    const bugReductionPercent = Math.min(50, this.bugsKilled * 3);
  
    if (bugReduction) {
      bugReduction.textContent = won 
        ? `Bugs reduced by ${bugReductionPercent}%` 
        : `Bugs increased by 10%`;
    }
    
    window.shooterResult = {
      score: this.score,
      bugReduction: bugReductionPercent,
      won: won
    };
  }
  updateUI() {
    document.getElementById('shooter-score').textContent = this.score;
    document.getElementById('shooter-lives').textContent = '❤️'.repeat(this.lives);
    document.getElementById('bugs-remaining').textContent = this.bugsToSpawn - this.bugsKilled;
  }
  
  playSound(type) {
    // Simple sound feedback using AudioContext (optional)
    // You can implement actual sounds here if desired
  }
  
  reset() {
    this.gameRunning = false;
    cancelAnimationFrame(this.animationId);
    
    const overlay = document.getElementById('shooter-overlay');
    const startBtn = document.getElementById('shooter-start-btn');
    const results = document.getElementById('final-results');
    
    overlay.style.display = 'flex';
    overlay.style.background = 'rgba(10, 14, 39, 0.95)';
    startBtn.style.display = 'block';
    results.style.display = 'none';
    
    document.getElementById('overlay-title').textContent = 'Bug Blaster';
    document.getElementById('overlay-message').textContent = 'Defend your project from bugs!';
  }
}
