/* ---------- The questions (the form is drawn from this) ---------- */
const QUESTIONS = [
  { key: "light", title: "How much sunlight does the spot get?", options: [
    { value: 1, label: "Low",    hint: "North window, or far from one" },
    { value: 2, label: "Medium", hint: "Bright room, no direct sun", default: true },
    { value: 3, label: "Bright", hint: "Direct sun for hours" } ] },
  { key: "water", title: "How often will you really water?", options: [
    { value: 1, label: "Rarely", hint: "Every 2–3 weeks, I forget" },
    { value: 2, label: "Weekly", hint: "Once a week-ish", default: true },
    { value: 3, label: "Often",  hint: "Several times a week" } ] },
  { key: "humidity", title: "How humid is the air?", options: [
    { value: 1, label: "Dry",    hint: "AC or heating most of the day" },
    { value: 2, label: "Normal", hint: "Typical room", default: true },
    { value: 3, label: "Humid",  hint: "Bathroom, kitchen, monsoon" } ] },
  { key: "size", title: "How much space do you have?", options: [
    { value: 1, label: "Small",  hint: "Desk or shelf" },
    { value: 2, label: "Medium", hint: "Floor corner", default: true },
    { value: 3, label: "Large",  hint: "Room for a tall plant" } ] },
  { key: "effort", title: "How much care are you up for?", options: [
    { value: 1, label: "Minimal", hint: "Set it and forget it" },
    { value: 2, label: "Some",    hint: "Fine with a routine", default: true },
    { value: 3, label: "Lots",    hint: "I enjoy fussing" } ] },
  { key: "priority", title: "What matters most?", options: [
    { value: "balanced", label: "Balanced",       hint: "A bit of everything", default: true },
    { value: "easy",     label: "Easiest care",   hint: "Lowest maintenance first" },
    { value: "light",    label: "Best light fit", hint: "Light match first" } ] }
];

/* ---------- BOUNCER RULES: true = plant survives this rule ---------- */
const CHECKS = {
  light:    (p, u) => u.light >= p.light[0] && u.light <= p.light[1], // my light is inside its range
  water:    (p, u) => p.water <= u.water,           // I can give it the water it needs
  humidity: (p, u) => p.humidity <= u.humidity + 1, // not a humid-lover in a very dry room
  size:     (p, u) => p.size <= u.size,             // it fits in my space
  effort:   (p, u) => p.effort <= u.effort,         // I'll give it enough care
  pets:     (p, u) => !u.pets || p.pet              // if I have pets, it must be pet-safe
};

function filterPlants(u, ignore = []) {
  const passed = [];    // plants that got in
  const rejected = [];  // plants that got kicked out

  for (const p of PLANTS) {
    // go through the rules, find the FIRST one this plant breaks
    const failed = Object.keys(CHECKS).find(
      rule => !ignore.includes(rule) && !CHECKS[rule](p, u)
    );

    if (failed) rejected.push({ plant: p, failed: failed });
    else passed.push(p);
  }
  return { passed, rejected };
}

// 1 = perfect match, 0.5 = one step off, 0 = two steps off
function closeness(a, b) {
  return 1 - Math.abs(a - b) / 2;
}

const WEIGHTS = {
  balanced: { light: 0.35, water: 0.25, humidity: 0.20, effort: 0.20 },
  easy:     { light: 0.20, water: 0.25, humidity: 0.15, effort: 0.40 },
  light:    { light: 0.55, water: 0.20, humidity: 0.15, effort: 0.10 }
};

function scorePlant(p, u) {
  const parts = {
    light:    closeness(p.light[2], u.light),  // [2] = the plant's happiest light
    water:    closeness(p.water, u.water),
    humidity: closeness(p.humidity, u.humidity),
    effort:   closeness(p.effort, u.effort)
  };
  const w = WEIGHTS[u.priority];
  let total = 0;
  for (const key in w) {
    total += w[key] * parts[key];   // weight × closeness, added up
  }
  return { total, parts };
}

function recommend(u) {
  const { passed, rejected } = filterPlants(u);
  const ranked = passed.map(p => {
    const s = scorePlant(p, u);
    return { plant: p, score: s.total, why: explain(p, u, s.parts) };
  });
  ranked.sort((a, b) => b.score - a.score);
  return { ranked, rejected };
}

/* ---------- Words for the cards ---------- */
const LIGHT_WORD  = ["", "low light", "medium light", "bright light"];
const WATER_WORD  = ["", "Drought-tolerant", "Weekly water", "Loves water"];
const EFFORT_WORD = ["", "Easy care", "Some care", "High care"];

// why a plant got kicked out (one sentence per rule)
const FAIL_TEXT = {
  light:    (p, u) => u.light < p.light[0] ? "Needs more light than your spot gets" : "Scorches in that much sun",
  water:    () => "Needs more water than you plan to give",
  humidity: () => "Needs a more humid spot",
  size:     () => "Grows too big for your space",
  effort:   () => "Needs more care than you want to give",
  pets:     () => "Not pet-safe"
};

// used when NO plant survives
const RELAX_TEXT = {
  light: "your light level", water: "how often you can water", humidity: "the humidity",
  size: "the space", effort: "the care level", pets: "the pet-safe filter"
};

// "why this plant" lines (max 3)
function explain(p, u, parts) {
  const lines = [];
  lines.push(parts.light === 1 ? "Happy in " + LIGHT_WORD[u.light] : "Tolerates your light");
  if (parts.water === 1) lines.push(u.water === 1 ? "Forgives missed waterings" : "Fits your watering rhythm");
  if (u.pets && p.pet) lines.push("Pet-safe");
  if (parts.humidity === 1) lines.push("Comfortable at your humidity");
  if (p.effort === 1) lines.push("Very low maintenance");
  return lines.slice(0, 3);
}

// if nothing survives: which ONE rule, if relaxed, lets in the most plants?
function bestRelaxation(u) {
  let best = null;
  for (const rule of Object.keys(CHECKS)) {
    if (rule === "pets" && !u.pets) continue;
    const count = filterPlants(u, [rule]).passed.length;   // <- the "ignore" trick!
    if (!best || count > best.count) best = { rule, count };
  }
  return best;
}

/* ---------- Draw the form + read the answers ---------- */
const form = document.getElementById("finder-form");
const resultsEl = document.getElementById("results");

function buildQuestions() {
  // for each question, make a box with 3 radio "chips" inside
  document.getElementById("questions").innerHTML = QUESTIONS.map(q => `
    <fieldset class="question">
      <legend>${q.title}</legend>
      <div class="chips">
        ${q.options.map(o => `
          <label class="chip">
            <input type="radio" name="${q.key}" value="${o.value}" ${o.default ? "checked" : ""}>
            <span class="chip-body"><strong>${o.label}</strong><small>${o.hint}</small></span>
          </label>`).join("")}
      </div>
    </fieldset>`).join("");
}

function readPrefs() {
  const d = new FormData(form);   // grabs everything the user picked
  return {
    light: +d.get("light"),       // the + turns text "2" into number 2
    water: +d.get("water"),
    humidity: +d.get("humidity"),
    size: +d.get("size"),
    effort: +d.get("effort"),
    priority: d.get("priority"),
    pets: d.get("pets") === "on"
  };
}

/* ---------- NEW: draw one plant card ---------- */
function plantCard(item, i) {
  const p = item.plant;
  return `
    <article class="plant-card" style="animation-delay:${i * 60}ms">
      <div class="plant-top">
        <span aria-hidden="true">${p.emoji}</span>
        <span class="score">${Math.round(item.score * 100)}% match</span>
      </div>
      <div class="plant-body">
        <h3>${p.name}</h3>
        <p class="sci">${p.sci}</p>
        <div class="tags">
          <span>☀️ ${LIGHT_WORD[p.light[2]]}</span>
          <span>💧 ${WATER_WORD[p.water]}</span>
          <span>${EFFORT_WORD[p.effort]}</span>
        </div>
        <ul class="why">${item.why.map(t => `<li>${t}</li>`).join("")}</ul>
      </div>
    </article>`;
}

/* ---------- NEW: draw the whole results area ---------- */
function render(u) {
  const { ranked, rejected } = recommend(u);
  let html = "";

  if (ranked.length === 0) {
    // nobody survived -> tell the user what to relax
    const relax = bestRelaxation(u);
    html += `
      <div class="empty">
        <h3>No plant fits every one of those</h3>
        <p>Relaxing <strong>${RELAX_TEXT[relax.rule]}</strong> would open up
           <strong>${relax.count}</strong> plant${relax.count === 1 ? "" : "s"}.
           Change that answer and try again.</p>
      </div>`;
  } else {
    html += `
      <div class="results-head">
        <h2>Your top matches</h2>
        <p>${ranked.length} plant${ranked.length === 1 ? "" : "s"} can survive your room. ${rejected.length} ruled out.</p>
      </div>
      <div class="grid">${ranked.slice(0, 6).map(plantCard).join("")}</div>`;
  }

  // the twist: always show why plants were kicked out
  html += `
    <details class="ruled-out">
      <summary>Why were ${rejected.length} plants ruled out?</summary>
      <ul>${rejected.map(r =>
        `<li>${r.plant.name}<span>${FAIL_TEXT[r.failed](r.plant, u)}</span></li>`).join("")}</ul>
    </details>`;

  resultsEl.innerHTML = html;
  resultsEl.hidden = false;
  resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---------- Start everything ---------- */
buildQuestions();

form.addEventListener("submit", function (e) {
  e.preventDefault();       // stop the page from reloading
  render(readPrefs());      // read answers -> recommend -> draw cards
});