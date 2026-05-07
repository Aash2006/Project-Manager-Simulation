console.log("NEW MINIGAMES JS LOADED");
/*
  Mini-games system
  - Bug Battle is now a special mini-game
  - It ONLY appears on Day 12
  - No timer for Bug Battle
  - Losing Bug Battle adds 0% bugs
  - Winning Bug Battle reduces bug bar by 40%
*/

function pickRandom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function clamp(n, lo, hi) {
  return Math.max(lo, Math.min(hi, n));
}

function getBugStorageKey() {
  const saveIdEl = document.getElementById("bugBarSaveId");
  const suffix = saveIdEl ? saveIdEl.value : "global";
  return `bug_percent_${suffix}`;
}

function getBugPercent() {
  const key = getBugStorageKey();
  const raw = localStorage.getItem(key);
  const n = raw === null ? 0 : Number(raw);
  return clamp(isNaN(n) ? 0 : n, 0, 100);
}

function setBugPercent(pct) {
  const key = getBugStorageKey();
  const v = clamp(pct, 0, 100);
  localStorage.setItem(key, String(v));
  renderBugBar(v);
}

function renderBugBar(pct) {
  const fill = document.getElementById("bugBarFill");
  const label = document.getElementById("bugBarPct");
  if (fill) fill.style.width = `${pct}%`;
  if (label) label.textContent = String(pct);
  console.log("renderBugBar called with:", pct);
  if (pct >= 100) {
    console.log("gameEnd URL:", window.ENDPOINTS.gameEnd);
    window.location.replace(window.ENDPOINTS.gameEnd);
  }
}

function pulseBugBar() {
  const wrap = document.getElementById("bugBarWrap");
  if (wrap) {
    wrap.classList.remove("minigame-pulse");
    void wrap.offsetWidth;
    wrap.classList.add("minigame-pulse");
  }
}

function bumpBug(amount) {
  const current = getBugPercent();
  const next = clamp(current + amount, 0, 100);
  setBugPercent(next);
  pulseBugBar();
}

function reduceBug(amount) {
  const current = getBugPercent();
  const next = clamp(current - amount, 0, 100);
  setBugPercent(next);
  pulseBugBar();
}

/* =========================
   QUIZ MINI-GAMES
========================= */

function renderChoices({ prompt, snippet, choices, name }) {
  const codeHtml = snippet
    ? `<pre class="bg-light border rounded p-3"><code>${escapeHtml(snippet)}</code></pre>`
    : "";

  const optionsHtml = choices
    .map(
      (c, idx) => `
        <div class="form-check mb-2">
          <input class="form-check-input" type="radio" name="${name}" id="${name}_${idx}" value="${idx}">
          <label class="form-check-label" for="${name}_${idx}">${escapeHtml(c)}</label>
        </div>`
    )
    .join("");

  return `
    <div class="mb-2 fw-semibold">${escapeHtml(prompt)}</div>
    ${codeHtml}
    <div class="mt-2">${optionsHtml}</div>
    <button type="button" class="btn btn-primary mt-3" id="mini-game-submit">Submit</button>
  `;
}

const QUIZ_GAMES = [
  {
    type: "quiz",
    id: "semicolon",
    title: "Bug Hunt: Missing Semicolon",
    prompt: "Which line is causing the syntax error?",
    snippet: `function add(a, b) {
  const sum = a + b
  return sum;
}
console.log(add(2, 3));`,
    choices: ["Line 1", "Line 2", "Line 3", "Line 4"],
    correctIndex: 1,
    explanation: "Line 2 is missing a semicolon (in semicolon-required style).",
  },
  {
    type: "quiz",
    id: "off_by_one",
    title: "Bug Hunt: Off-by-One",
    prompt: "Which loop condition correctly prints 0..9 (10 numbers)?",
    snippet: `for (let i = 0; ??? ; i++) {
  console.log(i);
}`,
    choices: ["i < 9", "i <= 9", "i <= 10", "i < 10 && i > 0"],
    correctIndex: 1,
    explanation: "`i <= 9` prints 0 through 9 inclusive.",
  },
  {
    type: "quiz",
    id: "null_check",
    title: "Bug Hunt: Null Reference",
    prompt: "How do you prevent the crash when user might be null?",
    snippet: `function greet(user) {
  return "Hello " + user.name;
}
// Sometimes user is null`,
    choices: [
      "Assume user is never null",
      "Add a null check before reading user.name",
      "Convert user.name to an integer",
      "Remove the return statement",
    ],
    correctIndex: 1,
    explanation: "Check null/undefined before accessing .name.",
  },
  {
    type: "quiz",
    id: "infinite_recursion",
    title: "Bug Hunt: Infinite Recursion",
    prompt: "What fix stops this function from calling itself forever?",
    snippet: `function factorial(n) {
  return n * factorial(n - 1);
}
console.log(factorial(5));`,
    choices: [
      "Add a base case: if (n <= 1) return 1;",
      "Change multiplication to addition",
      "Call factorial(n + 1) instead",
      "Remove console.log",
    ],
    correctIndex: 0,
    explanation: "Recursive functions need a base case.",
  },
  {
    type: "quiz",
    id: "typo_variable",
    title: "Bug Hunt: Variable Name Typo",
    prompt: "Why does this code print undefined?",
    snippet: `const progressPercent = 80;
console.log(progressPrecent);`,
    choices: [
      "Because console.log is broken",
      "Because progressPercent is a number",
      "Because the variable name is misspelled on line 2",
      "Because const variables can’t be logged",
    ],
    correctIndex: 2,
    explanation: "progressPrecent is misspelled; it should be progressPercent.",
  },
];

/* =========================
   COMMON MINI-GAME HELPERS
========================= */

function finishMiniGameSuccess(msgHtml) {
  const feedbackEl = document.getElementById("mini-game-feedback");
  if (feedbackEl) {
    feedbackEl.innerHTML =
      msgHtml ||
      `<div class="alert alert-success mb-0"><strong>Fixed!</strong> Nice work.</div>`;
  }

  const modalEl = document.getElementById("miniGameModal");
  if (modalEl) {
    const bsModal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    setTimeout(() => bsModal.hide(), 1100);
  }
}

function finishMiniGameFail(msgHtml, shouldIncreaseBug = true) {
  if (shouldIncreaseBug) {
    bumpBug(10);
  }

  const feedbackEl = document.getElementById("mini-game-feedback");
  if (feedbackEl) {
    feedbackEl.innerHTML =
      msgHtml ||
      `<div class="alert alert-danger mb-0"><strong>Bugged!</strong> Bugs increased by 10%.</div>`;
  }

  const modalEl = document.getElementById("miniGameModal");
  if (modalEl) {
    const dialog = modalEl.querySelector(".modal-dialog");
    if (dialog) {
      dialog.classList.remove("minigame-shake");
      void dialog.offsetWidth;
      dialog.classList.add("minigame-shake");
    }

    const bsModal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    setTimeout(() => bsModal.hide(), 1200);
  }
}

/* =========================
   COMPLEX GAME 1: BUG SPRAY
========================= */

function startBugSprayGame(state) {
  const body = document.getElementById("mini-game-body");
  const feedback = document.getElementById("mini-game-feedback");
  if (!body || !feedback) return;

  feedback.innerHTML = "";

  const BUG_COUNT = 10;
  let alive = BUG_COUNT;

  body.innerHTML = `
    <div class="minigame-header">
      <div class="minigame-title">Bug Spray</div>
      <div class="minigame-desc">Click all the bugs before time runs out!</div>
    </div>

    <div class="bug-spray-controls text-center mb-3">
      <div class="bug-spray-count fs-5">Bugs left: <strong id="bugLeftCount">${alive}</strong></div>
    </div>

    <div class="bug-spray-area" id="bugSprayArea" style="cursor: crosshair;"></div>
  `;

  const area = document.getElementById("bugSprayArea");
  const leftLabel = document.getElementById("bugLeftCount");

  const bugs = [];
  for (let i = 0; i < BUG_COUNT; i++) {
    const bug = document.createElement("div");
    bug.className = "bug";
    bug.innerHTML = "🪲";

    bug.dataset.x = String(Math.random() * 90);
    bug.dataset.y = String(Math.random() * 80);
    bug.style.left = `${bug.dataset.x}%`;
    bug.style.top = `${bug.dataset.y}%`;

    bug.onclick = () => {
      if (state.answered) return;

      bug.classList.add("bug-sprayed");
      setTimeout(() => bug.remove(), 150);

      alive -= 1;
      leftLabel.textContent = String(alive);

      if (alive <= 0 && !state.answered) {
        state.answered = true;
        state.success = true;
        finishMiniGameSuccess(`<div class="alert alert-success mb-0"><strong>Clean!</strong> You squashed them all.</div>`);
      }
    };

    area.appendChild(bug);
    bugs.push(bug);
  }

  const moveInterval = window.setInterval(() => {
    if (state.answered) return;

    for (const bug of bugs) {
      if (!bug.isConnected) continue;

      const x = Number(bug.dataset.x);
      const y = Number(bug.dataset.y);

      const dx = (Math.random() - 0.5) * 10;
      const dy = (Math.random() - 0.5) * 10;
      const nx = clamp(x + dx, 0, 92);
      const ny = clamp(y + dy, 0, 86);

      bug.dataset.x = String(nx);
      bug.dataset.y = String(ny);
      bug.style.left = `${nx}%`;
      bug.style.top = `${ny}%`;
    }
  }, 650);

  state.cleanups.push(() => window.clearInterval(moveInterval));
}

/* =========================
   COMPLEX GAME 2: PIPELINE
========================= */

function startPipelineGame(state) {
  const body = document.getElementById("mini-game-body");
  const feedback = document.getElementById("mini-game-feedback");
  if (!body || !feedback) return;

  feedback.innerHTML = "";

  const correct = ["Compile", "Run", "Test", "Deploy", "Monitor"];
  const shuffled = [...correct].sort(() => Math.random() - 0.5);

  body.innerHTML = `
    <div class="minigame-header">
      <div class="minigame-title">Build Pipeline Fix</div>
      <div class="minigame-desc">Drag the steps into the correct order.</div>
    </div>

    <ul id="pipelineList" class="pipeline-list" style="padding: 0; margin: 0;"></ul>
    <button class="btn btn-primary mt-3" id="checkPipeline" type="button">Check Order</button>
  `;

  const list = document.getElementById("pipelineList");
  shuffled.forEach((step) => {
    const li = document.createElement("li");
    li.className = "pipeline-item";
    li.style.cssText = "color: white !important; background-color: #1e1b4b; border: 1px solid #4338ca; border-radius: 6px; padding: 10px 15px; margin-bottom: 8px; cursor: grab; list-style: none;";
    li.textContent = step;
    li.draggable = true;
    list.appendChild(li);
  });

  let dragged = null;

  list.addEventListener("dragstart", (e) => {
    if (e.target && e.target.classList.contains("pipeline-item")) {
      dragged = e.target;
      e.target.classList.add("dragging");
    }
  });

  list.addEventListener("dragend", (e) => {
    if (e.target && e.target.classList.contains("pipeline-item")) {
      e.target.classList.remove("dragging");
    }
  });

  list.addEventListener("dragover", (e) => {
    e.preventDefault();
    const afterElement = getDragAfterElement(list, e.clientY);
    if (!dragged) return;
    if (afterElement == null) list.appendChild(dragged);
    else list.insertBefore(dragged, afterElement);
  });

  function getDragAfterElement(container, y) {
    const els = [...container.querySelectorAll(".pipeline-item:not(.dragging)")];
    return els.reduce(
      (closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
          return { offset, element: child };
        }
        return closest;
      },
      { offset: Number.NEGATIVE_INFINITY, element: null }
    ).element;
  }

  document.getElementById("checkPipeline").onclick = () => {
    if (state.answered) return;
    state.answered = true;

    const current = [...list.children].map((li) => li.textContent);
    if (JSON.stringify(current) === JSON.stringify(correct)) {
      state.success = true;
      finishMiniGameSuccess(`<div class="alert alert-success mb-0"><strong>Build green!</strong> Pipeline fixed.</div>`);
    } else {
      state.success = false;
      finishMiniGameFail(`<div class="alert alert-danger mb-0"><strong>Build failed!</strong> Wrong order. Bugs increased by 10%.</div>`);
    }
  };
}

/* =========================
   COMPLEX GAME 3: MEMORY
========================= */

function startMemoryPatchGame(state) {
  const body = document.getElementById("mini-game-body");
  const feedback = document.getElementById("mini-game-feedback");
  if (!body || !feedback) return;

  feedback.innerHTML = "";

  const pairs = [
    ["Null", "Check"],
    ["Loop", "Break"],
    ["Memory", "Free"],
    ["Crash", "Log"],
    ["Index", "Bounds"],
    ["Auth", "Token"],
  ];

  const cards = pairs.flat().sort(() => Math.random() - 0.5);

  let selected = [];
  let matched = 0;

  body.innerHTML = `
    <div class="minigame-header">
      <div class="minigame-title">Memory Patch</div>
      <div class="minigame-desc">Match bug ↔ fix pairs before time runs out.</div>
    </div>
    <div class="memory-grid" id="memoryGrid"></div>
  `;

  const grid = document.getElementById("memoryGrid");

  function isPair(a, b) {
    return pairs.some((p) => p.includes(a) && p.includes(b));
  }

  cards.forEach((value) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "memory-card";
    card.dataset.value = value;
    card.dataset.revealed = "false";
    card.textContent = "•";

    card.onclick = () => {
      if (state.answered) return;
      if (card.classList.contains("done")) return;
      if (selected.length >= 2) return;
      if (card.dataset.revealed === "true") return;

      card.dataset.revealed = "true";
      card.textContent = value;
      selected.push(card);

      if (selected.length === 2) {
        const a = selected[0].dataset.value;
        const b = selected[1].dataset.value;

        window.setTimeout(() => {
          if (isPair(a, b)) {
            selected.forEach((c) => c.classList.add("done"));
            matched += 2;
          } else {
            selected.forEach((c) => {
              c.dataset.revealed = "false";
              c.textContent = "•";
              c.classList.add("memory-wrong");
              setTimeout(() => c.classList.remove("memory-wrong"), 220);
            });
          }

          selected = [];

          if (matched === cards.length && !state.answered) {
            state.answered = true;
            state.success = true;
            finishMiniGameSuccess(`<div class="alert alert-success mb-0"><strong>Patched!</strong> All pairs matched.</div>`);
          }
        }, 500);
      }
    };

    grid.appendChild(card);
  });
}

/* =========================
   COMPLEX GAME 4: BUG BATTLE
   Special day-12-only mini-game
========================= */

function startBugBattleGame(state) {
  const body = document.getElementById("mini-game-body");
  const feedback = document.getElementById("mini-game-feedback");
  if (!body || !feedback) return;

  feedback.innerHTML = "";

  const player = {
    name: "Debugger",
    hp: 100,
    maxHp: 100,
    sprite: "🧑‍💻",
    level: 25,
  };

  const bugVariants = [
    {
      name: "Syntax Bug",
      sprite: "🐛",
      hp: 70,
      maxHp: 70,
      level: 19,
      moves: [
        { name: "Missing Semicolon", damage: 10, critChance: 0.20 },
        { name: "Brace Bite", damage: 13, critChance: 0.14 },
      ],
    },
    {
      name: "Null Pointer Bug",
      sprite: "🕷️",
      hp: 85,
      maxHp: 85,
      level: 22,
      moves: [
        { name: "Null Bite", damage: 12, critChance: 0.16 },
        { name: "Crash Sting", damage: 16, critChance: 0.11 },
      ],
    },
    {
      name: "Memory Leak Bug",
      sprite: "🪳",
      hp: 100,
      maxHp: 100,
      level: 27,
      moves: [
        { name: "Leak Drain", damage: 15, critChance: 0.12 },
        { name: "Heap Slam", damage: 19, critChance: 0.08 },
      ],
    },
  ];

  let currentBugIndex = 0;
  let currentBug = structuredClone(bugVariants[currentBugIndex]);

  const cards = [
    { name: "Quick Patch", damage: 14, type: "attack", critChance: 0.28 },
    { name: "Refactor Slash", damage: 22, type: "attack", critChance: 0.14 },
    { name: "Cache Burst", damage: 18, type: "attack", critChance: 0.20 },
    { name: "Stack Overload", damage: 28, type: "attack", critChance: 0.07 },
    { name: "Recovery Script", heal: 18, type: "heal" },
  ];

  body.innerHTML = `
    <div class="special-minigame-banner" id="specialMinigameBanner">
      SPECIAL MINI-GAME
    </div>

    <div class="gb-battle-wrap">
      <div class="gb-battle-arena">
        <div class="gb-enemy-status gb-panel">
          <div class="gb-name-row">
            <span id="battleBugName">${currentBug.name.toUpperCase()}</span>
            <span>:L<span id="battleBugLevel">${currentBug.level}</span></span>
          </div>

          <div class="gb-hp-row">
            <span class="gb-hp-label">HP:</span>
            <div class="gb-hpbar">
              <div id="bugBattleHpFill" class="gb-hpfill gb-enemy-hp" style="width:${(currentBug.hp / currentBug.maxHp) * 100}%"></div>
            </div>
          </div>

          <div class="gb-enemy-hp-text">
            <span id="bugBattleHpText">${currentBug.hp}</span>/<span id="bugBattleHpMax">${currentBug.maxHp}</span>
          </div>
        </div>

        <div class="gb-enemy-sprite" id="battleBugSprite">${currentBug.sprite}</div>

        <div class="gb-player-sprite">${player.sprite}</div>

        <div class="gb-player-status gb-panel">
          <div class="gb-name-row">
            <span>${player.name.toUpperCase()}</span>
            <span>:L${player.level}</span>
          </div>

          <div class="gb-hp-row">
            <span class="gb-hp-label">HP:</span>
            <div class="gb-hpbar">
              <div id="playerBattleHpFill" class="gb-hpfill gb-player-hp" style="width:${(player.hp / player.maxHp) * 100}%"></div>
            </div>
          </div>

          <div class="gb-player-hp-text">
            <span id="playerBattleHpText">${player.hp}</span>/<span id="playerBattleHpMax">${player.maxHp}</span>
          </div>
        </div>
      </div>

      <div class="gb-stage-indicator">
        BUG <span id="battleStageIndex">${currentBugIndex + 1}</span> / ${bugVariants.length}
      </div>

      <div class="gb-bottom-ui">
        <div class="gb-log-box gb-panel" id="battleLog">
          A wild ${currentBug.name} appeared!
        </div>

        <div class="gb-command-box gb-panel" id="battleCards">
          ${cards.map((c, idx) => `
            <button type="button" class="gb-card-btn" data-card-index="${idx}">
              <span class="gb-card-arrow">▶</span>
              <span class="gb-card-main">
                <span class="gb-card-name">${c.name.toUpperCase()}</span>
                <span class="gb-card-meta">
                  ${
                    c.type === "attack"
                      ? `${c.damage} DMG • 80% HIT • ${Math.round(c.critChance * 100)}% CRIT`
                      : `HEAL ${c.heal}`
                  }
                </span>
              </span>
            </button>
          `).join("")}
        </div>
      </div>
    </div>
  `;

  const banner = document.getElementById("specialMinigameBanner");
  if (banner) {
    setTimeout(() => {
      banner.classList.add("hide");
    }, 1800);
  }

  const bugHpFill = document.getElementById("bugBattleHpFill");
  const bugHpText = document.getElementById("bugBattleHpText");
  const bugHpMax = document.getElementById("bugBattleHpMax");
  const bugName = document.getElementById("battleBugName");
  const bugLevel = document.getElementById("battleBugLevel");
  const bugSprite = document.getElementById("battleBugSprite");
  const stageIndex = document.getElementById("battleStageIndex");

  const playerHpFill = document.getElementById("playerBattleHpFill");
  const playerHpText = document.getElementById("playerBattleHpText");
  const playerHpMax = document.getElementById("playerBattleHpMax");

  const battleLog = document.getElementById("battleLog");
  const cardButtons = [...document.querySelectorAll(".gb-card-btn")];

  let turnLocked = false;

  function renderBattleBars() {
    const bugPct = clamp((currentBug.hp / currentBug.maxHp) * 100, 0, 100);
    const playerPct = clamp((player.hp / player.maxHp) * 100, 0, 100);

    bugHpFill.style.width = `${bugPct}%`;
    playerHpFill.style.width = `${playerPct}%`;

    bugHpText.textContent = String(Math.max(0, currentBug.hp));
    bugHpMax.textContent = String(currentBug.maxHp);
    playerHpText.textContent = String(Math.max(0, player.hp));
    playerHpMax.textContent = String(player.maxHp);
  }

  function renderBugIdentity() {
    bugName.textContent = currentBug.name.toUpperCase();
    bugLevel.textContent = String(currentBug.level);
    bugSprite.textContent = currentBug.sprite;
    stageIndex.textContent = String(currentBugIndex + 1);
    renderBattleBars();
  }

  function setCardsDisabled(disabled) {
    cardButtons.forEach((btn) => {
      btn.disabled = disabled;
      btn.classList.toggle("disabled", disabled);
    });
  }

  function log(msg) {
    battleLog.innerHTML = msg;
  }

  function advanceToNextBug() {
    currentBugIndex += 1;

    if (currentBugIndex >= bugVariants.length) {
      state.answered = true;
      state.success = true;
      setCardsDisabled(true);

      reduceBug(40);

      finishMiniGameSuccess(
        `<div class="alert alert-success mb-0"><strong>Victory!</strong> You defeated all 3 bugs and reduced the bug bar by 40%.</div>`
      );
      return;
    }

    currentBug = structuredClone(bugVariants[currentBugIndex]);
    renderBugIdentity();
    setCardsDisabled(false);
    turnLocked = false;
    log(`Another bug appeared! <strong>${currentBug.name}</strong> enters the battle.`);
  }

  function endBattleIfNeeded() {
    if (currentBug.hp <= 0) {
      setCardsDisabled(true);
      log(`<strong>${currentBug.name}</strong> fainted!`);

      setTimeout(() => {
        advanceToNextBug();
      }, 900);

      return true;
    }

    if (player.hp <= 0) {
      state.answered = true;
      state.success = false;
      setCardsDisabled(true);

      finishMiniGameFail(
        `<div class="alert alert-danger mb-0"><strong>Defeat!</strong> You lost the special battle.</div>`,
        false
      );
      return true;
    }

    return false;
  }

  function bugTurn() {
    if (state.answered) return;

    const move = pickRandom(currentBug.moves);

    setTimeout(() => {
      const hit = Math.random() < 0.9;
      const crit = Math.random() < move.critChance;
      let damage = move.damage;

      if (hit) {
        if (crit) damage = Math.round(damage * 1.5);

        player.hp = clamp(player.hp - damage, 0, player.maxHp);
        renderBattleBars();

        log(
          `The <strong>${currentBug.name}</strong> used <strong>${move.name}</strong>${
            crit ? ` — <span class="battle-crit">CRITICAL HIT!</span>` : ""
          } and dealt <strong>${damage}</strong> damage!`
        );
      } else {
        log(`The <strong>${currentBug.name}</strong> used <strong>${move.name}</strong> but it missed!`);
      }

      if (endBattleIfNeeded()) return;

      turnLocked = false;
      setCardsDisabled(false);
    }, 700);
  }

  function playerTurn(cardIndex) {
    if (state.answered || turnLocked) return;

    const card = cards[cardIndex];
    if (!card) return;

    turnLocked = true;
    setCardsDisabled(true);

    if (card.type === "heal") {
      const before = player.hp;
      player.hp = clamp(player.hp + card.heal, 0, player.maxHp);
      const actual = player.hp - before;
      renderBattleBars();

      log(`You used <strong>${card.name}</strong> and restored <strong>${actual}</strong> HP!`);

      setTimeout(() => {
        bugTurn();
      }, 550);

      return;
    }

    const hit = Math.random() < 0.8;
    const crit = Math.random() < card.critChance;
    let damage = card.damage;

    if (hit) {
      if (crit) damage = Math.round(damage * 1.5);

      currentBug.hp = clamp(currentBug.hp - damage, 0, currentBug.maxHp);
      renderBattleBars();

      log(
        `You used <strong>${card.name}</strong>${
          crit ? ` — <span class="battle-crit">CRITICAL HIT!</span>` : ""
        } and dealt <strong>${damage}</strong> damage!`
      );
    } else {
      log(`You used <strong>${card.name}</strong> but it missed!`);
    }

    if (endBattleIfNeeded()) return;

    bugTurn();
  }

  cardButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = Number(btn.dataset.cardIndex);
      playerTurn(idx);
    });
  });

  renderBugIdentity();
}


/* =========================
   COMPLEX GAME 5: Space shooter mini game
   
========================= */

  function startSpaceShooterGame(state) {
  const body = document.getElementById("mini-game-body");
  const feedback = document.getElementById("mini-game-feedback");
  if (!body || !feedback) return;
 
  feedback.innerHTML = "";
 
  // Inject the space shooter HTML
  body.innerHTML = `
    <div id="space-shooter-game" style="position: relative; max-width: 100%; overflow: hidden;">
      <!-- Game Stats -->
      <div class="game-stats" style="display: flex; justify-content: space-around; padding: 10px; background: #1a1d2e; color: white; font-weight: bold;">
        <div class="stat-display">
          <span class="stat-label">Score:</span>
          <span id="shooter-score">0</span>
        </div>
        <div class="stat-display">
          <span class="stat-label">Lives:</span>
          <span id="shooter-lives">❤️❤️❤️</span>
        </div>
        <div class="stat-display">
          <span class="stat-label">Bugs Left:</span>
          <span id="bugs-remaining">20</span>
        </div>
      </div>

      <!-- Game Canvas - SMALLER SIZE -->
      <canvas id="shooter-canvas" width="600" height="400" style="display: block; margin: 0 auto; background: #0a0e27; max-width: 100%;"></canvas>

      <!-- Game Start/End Overlay -->
      <div id="shooter-overlay" class="shooter-overlay" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; background: rgba(10, 14, 39, 0.95); z-index: 10;">
        <div class="overlay-content" style="text-align: center; color: white; padding: 20px; max-width: 90%;">
          <h2 id="overlay-title" style="font-size: 1.8rem; margin-bottom: 10px;">Bug Blaster</h2>
          <p id="overlay-message" style="font-size: 1rem; margin-bottom: 15px;">Defend your project from bugs!</p>
          <div class="controls-info" style="margin: 15px 0; font-size: 0.9rem; color: white; user-select: none; background: transparent;">
            <p style="margin: 5px 0; background: transparent;">⬅️ ➡️ Arrow Keys to Move</p>
            <p style="margin: 5px 0; background: transparent;">SPACE to Shoot</p>
          </div>
          <button id="shooter-start-btn" class="btn btn-primary btn-lg">Start Game</button>
          <div id="final-results" style="display: none;">
            <h3 style="font-size: 1.3rem; margin: 10px 0;">Final Score: <span id="final-score">0</span></h3>
            <p id="bug-reduction-text" style="font-size: 0.9rem; margin: 10px 0;"></p>
            <button id="shooter-continue-btn" class="btn btn-success btn-lg" style="margin-top: 10px;">Continue</button>
          </div>
        </div>
      </div>
  `;
 
  // Initialize the Space Shooter game
  const shooter = new SpaceShooter('shooter-canvas');
 
  // Start button handler
  document.getElementById('shooter-start-btn').addEventListener('click', () => {
    shooter.start();
  });
 
  // Continue button handler (after game ends)
  document.getElementById('shooter-continue-btn').addEventListener('click', () => {
  if (!state.answered) {
    state.answered = true;

    const result = window.shooterResult;
    
    if (result && result.won) {
      // Use the pre-calculated reduction from showEndScreen
      const bugReductionPercent = result.bugReduction;
      
      state.success = true;
      reduceBug(bugReductionPercent);
      
      finishMiniGameSuccess(
        `<div class="alert alert-success mb-0"><strong>Victory!</strong> All bugs eliminated! Bugs reduced by ${bugReductionPercent}%.</div>`
      );
    } else {
      state.success = false;
      finishMiniGameFail(
        `<div class="alert alert-danger mb-0"><strong>Defeated!</strong> The bugs got through. Bugs increased by 10%.</div>`,
        true
      );
    }
  }
  }
);



  // Cleanup function
  state.cleanups.push(() => {
    if (shooter.gameRunning) {
      shooter.gameRunning = false;
      cancelAnimationFrame(shooter.animationId);
    }
  });
}


const COMPLEX_GAMES = [
  { type: "complex", id: "spray", title: "Bug Spray", start: startBugSprayGame },
  { type: "complex", id: "pipeline", title: "Build Pipeline Fix", start: startPipelineGame },
  { type: "complex", id: "memory", title: "Memory Patch", start: startMemoryPatchGame },
  { type: "complex", id: "battle", title: "Bug Battle", start: startBugBattleGame },
  { type: "complex", id: "shooter", title: "Space Shooter", start: startSpaceShooterGame },
];

/* =========================
   LAUNCHER
========================= */

function getCurrentProjectDay() {
  const dayEl = document.getElementById("days-in-project-text");
  if (!dayEl) return null;

  const text = dayEl.textContent || "";
  const match = text.match(/(\d+)/);
  if (!match) return null;

  return Number(match[1]);
}

function showMiniGameShell(title, options = {}) {
  const modalEl = document.getElementById("miniGameModal");
  const bodyEl = document.getElementById("mini-game-body");
  const feedbackEl = document.getElementById("mini-game-feedback");
  const titleEl = document.getElementById("miniGameModalLabel");
  const timerEl = document.getElementById("miniGameTimer");
  const previewFill = document.getElementById("miniBugPreviewFill");
  const previewLabel = document.getElementById("miniGameImpactLabel");
  const timerWrapper = document.getElementById("miniGameTimerWrapper");

  if (!modalEl || !bodyEl || !feedbackEl || !titleEl) {
    console.warn("Mini game modal elements missing from DOM");
    return null;
  }

  if (timerWrapper) {
    timerWrapper.style.display = options.hideTimer ? "none" : "";
  }

  if (timerEl && !options.hideTimer) {
    timerEl.textContent = "60";
    timerEl.classList.remove("timer-warn", "timer-danger");
  }

  if (previewLabel) {
    previewLabel.innerHTML = options.previewLabel || `Bug impact on failure: <strong>+10%</strong>`;
  }

  if (previewFill) {
    if (options.previewFillWidth !== undefined) {
      previewFill.style.width = `${options.previewFillWidth}%`;
      previewFill.style.background = options.previewFillColor || "#ef4444";
    } else {
      const current = getBugPercent();
      const next = clamp(current + 10, 0, 100);
      previewFill.style.width = `${next}%`;
      previewFill.style.background = "#ef4444";
    }
  }

  titleEl.textContent = title || "Bug Challenge";
  feedbackEl.innerHTML = "";
  bodyEl.innerHTML = "";

  const bsModal = new bootstrap.Modal(modalEl, { backdrop: "static", keyboard: false });
  bsModal.show();

  return { modalEl, timerEl };
}

function runMiniGame(game) {
  const isBattle = game.id === "battle";

  const shell = showMiniGameShell(game.title, {
    hideTimer: isBattle,
    previewLabel: isBattle
      ? `Failure impact: <strong>0%</strong> · Victory reward: <strong>-40%</strong>`
      : `Bug impact on failure: <strong>+10%</strong>`,
    previewFillWidth: isBattle ? clamp(getBugPercent() - 40, 0, 100) : undefined,
    previewFillColor: isBattle ? "#22c55e" : undefined,
  });

  if (!shell) return;

  const { modalEl, timerEl } = shell;

  const state = {
    answered: false,
    success: false,
    cleanups: [],
    noClosePenalty: isBattle,
  };

  if (game.type === "quiz") {
    const bodyEl = document.getElementById("mini-game-body");
    bodyEl.innerHTML = renderChoices({
      prompt: game.prompt,
      snippet: game.snippet,
      choices: game.choices,
      name: "mini_game_choice",
    });

    const submitBtn = document.getElementById("mini-game-submit");
    submitBtn.onclick = () => {
      if (state.answered) return;

      const selected = document.querySelector('input[name="mini_game_choice"]:checked');
      if (!selected) {
        document.getElementById("mini-game-feedback").innerHTML =
          `<div class="alert alert-warning mb-0">Pick an option first.</div>`;
        return;
      }

      state.answered = true;
      submitBtn.disabled = true;

      const idx = Number(selected.value);
      if (idx === game.correctIndex) {
        state.success = true;
        finishMiniGameSuccess(
          `<div class="alert alert-success mb-0"><strong>Fixed!</strong> ${escapeHtml(game.explanation)}</div>`
        );
      } else {
        state.success = false;
        finishMiniGameFail(
          `<div class="alert alert-danger mb-0"><strong>Incorrect.</strong> Bugs increased by 10%.</div>`,
          true
        );
      }
    };
  } else if (game.type === "complex") {
    game.start(state);
  }

  let intervalId = null;

  if (!isBattle) {
    let remaining = 60;

    const tick = () => {
      if (state.answered) return;

      remaining -= 1;
      remaining = Math.max(0, remaining);
      timerEl.textContent = String(remaining);

      if (remaining <= 10) timerEl.classList.add("timer-warn");
      if (remaining <= 5) timerEl.classList.add("timer-danger");

      if (remaining === 0 && !state.answered) {
        state.answered = true;
        state.success = false;
        finishMiniGameFail(
          `<div class="alert alert-danger mb-0"><strong>Time’s up!</strong> Bugs increased by 10%.</div>`,
          true
        );
      }
    };

    intervalId = window.setInterval(tick, 1000);
  }

  const cleanupAll = () => {
    if (intervalId) window.clearInterval(intervalId);
    state.cleanups.forEach((fn) => {
      try {
        fn();
      } catch (_) {}
    });
  };

  const onHidden = () => {
    if (!state.answered && !state.noClosePenalty) {
      state.answered = true;
      state.success = false;
      bumpBug(10);
    }
    cleanupAll();
    modalEl.removeEventListener("hidden.bs.modal", onHidden);
  };

  modalEl.addEventListener("hidden.bs.modal", onHidden);
}

function maybeLaunchMiniGame() {
  const day = getCurrentProjectDay();
  console.log("Current day:", day);
  
  // Special Day 8: Space Shooter (always spawns)
  if (day === 12) {
    runMiniGame({
      type: "complex",
      id: "shooter",
      title: "Space Shooter",
      start: startSpaceShooterGame,
    });
    return;
  }

  // Special Day 12: Bug Battle (always spawns)
  if (day === 22) {
    runMiniGame({
      type: "complex",
      id: "battle",
      title: "Special Bug Battle",
      start: startBugBattleGame,
    });
    return; 
  }
  
  // 90% chance to show mini-game
  if (Math.random() >= 0.6) return; 
  
  // Build array of all available mini-games
  const allMiniGames = [
    ...QUIZ_GAMES,
    { type: "complex", id: "spray", title: "Bug Spray", start: startBugSprayGame },
    { type: "complex", id: "pipeline", title: "Build Pipeline Fix", start: startPipelineGame },
    { type: "complex", id: "memory", title: "Memory Patch", start: startMemoryPatchGame },
    { type: "complex", id: "shooter", title: "Space Shooter", start: startSpaceShooterGame },
  ];
  
  runMiniGame(pickRandom(allMiniGames)); 
}

document.addEventListener("DOMContentLoaded", () => {
  renderBugBar(getBugPercent());

  const startDayPopup = document.getElementById("myPopupModal");
  if (!startDayPopup) {
    console.warn("Start day popup not found!");
    return;
  }

  startDayPopup.addEventListener("hidden.bs.modal", () => {
    console.log("Start day popup closed, launching mini-game...");
    setTimeout(() => maybeLaunchMiniGame(), 150);
    //setTimeout(() => loadDecisionModal(), 300);
  });
});
