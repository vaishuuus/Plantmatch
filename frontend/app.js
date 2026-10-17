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

/* ---------- Words for the cards ---------- */
const LIGHT_WORD  = ["", "low light", "medium light", "bright light"];
const WATER_WORD  = ["", "Drought-tolerant", "Weekly water", "Loves water"];
const EFFORT_WORD = ["", "Easy care", "Some care", "High care"];

const form = document.getElementById("finder-form");
const resultsEl = document.getElementById("results");

/* ---------- Draw the form + read the answers ---------- */
function buildQuestions() {
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
  const d = new FormData(form);
  return {
    light: +d.get("light"),
    water: +d.get("water"),
    humidity: +d.get("humidity"),
    size: +d.get("size"),
    effort: +d.get("effort"),
    priority: d.get("priority"),
    pets: d.get("pets") === "on"
  };
}

/* ---------- NEW: ask the backend ---------- */
async function getRecommendations(answers) {
  const res = await fetch("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(answers)
  });
  if (!res.ok) throw new Error("Server error " + res.status);
  return res.json();
}

/* ---------- Draw one plant card ---------- */
function plantCard(item, i) {
  const p = item.plant;
  const pct = x => Math.round(x * 100);
  return `
    <article class="plant-card" style="animation-delay:${i * 60}ms">
      <div class="plant-top">
        <span aria-hidden="true">${p.emoji}</span>
        <span class="score">${pct(item.score)}% match</span>
      </div>
      <div class="plant-body">
        <h3>${p.name}</h3>
        <p class="sci">${p.sci}</p>
        <div class="tags">
          <span>☀️ ${LIGHT_WORD[p.light_ideal]}</span>
          <span>💧 ${WATER_WORD[p.water]}</span>
          <span>${EFFORT_WORD[p.effort]}</span>
        </div>
        <div class="breakdown">
          <div class="bar"><span>Fit</span>
            <div class="bar-track"><div class="bar-fill" style="width:${pct(item.content)}%"></div></div>
            <b>${pct(item.content)}%</b></div>
          <div class="bar"><span>Community</span>
            <div class="bar-track"><div class="bar-fill" style="width:${pct(item.collab)}%"></div></div>
            <b>${pct(item.collab)}%</b></div>
        </div>
        <ul class="why">${item.why.map(t => `<li>${t}</li>`).join("")}</ul>
        <div class="feedback">
          <span>Would you grow it?</span>
          <button class="fb-btn" data-plant="${p.id}" data-liked="1" aria-label="Thumbs up">👍</button>
          <button class="fb-btn" data-plant="${p.id}" data-liked="0" aria-label="Thumbs down">👎</button>
        </div>
      </div>
    </article>`;
}

/* ---------- Draw the results area ---------- */
async function render(answers) {
    roomId = newId();
  lastAnswers = answers;
  resultsEl.hidden = false;
  resultsEl.innerHTML = `<p class="results-head">Finding your plants…</p>`;

  try {
    const data = await getRecommendations(answers);   // <- the backend does the thinking
    const { ranked, rejected, relax } = data;
    let html = "";

    if (ranked.length === 0) {
      html += `
        <div class="empty">
          <h3>No plant fits every one of those</h3>
          <p>Relaxing <strong>${relax.label}</strong> would open up
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

    html += `
      <details class="ruled-out">
        <summary>Why were ${rejected.length} plants ruled out?</summary>
        <ul>${rejected.map(r => `<li>${r.plant.name}<span>${r.reason}</span></li>`).join("")}</ul>
      </details>`;

    resultsEl.innerHTML = html;
    resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    resultsEl.innerHTML = `
      <div class="empty">
        <h3>Can't reach the server</h3>
        <p>Is the backend running? In the <strong>backend</strong> folder, run
           <strong>python -m uvicorn main:app --reload</strong>, then open
           <strong>http://127.0.0.1:8000</strong>.</p>
      </div>`;
  }
}

/* ---------- Feedback (thumbs up / down) ---------- */
let roomId = null;       // new id for every "Find my plants" click
let lastAnswers = null;  // the answers behind the cards on screen

function newId() {
  return (crypto.randomUUID && crypto.randomUUID()) ||
         Date.now().toString(36) + Math.random().toString(36).slice(2);
}

async function loadStats() {
  try {
    const s = await (await fetch("/api/stats")).json();
    document.getElementById("stats").textContent =
      `Community data: ${s.simulated_users} simulated users · ${s.simulated_ratings} simulated ratings · ${s.feedback_ratings} real ratings`;
  } catch (e) { /* the footer line is optional */ }
}

// one listener handles every 👍/👎 button, even ones created later
resultsEl.addEventListener("click", async function (e) {
  const btn = e.target.closest(".fb-btn");
  if (!btn || !roomId) return;

  const row = btn.parentElement;
  const label = row.querySelector("span");
  row.querySelectorAll(".fb-btn").forEach(b => b.classList.remove("picked"));
  btn.classList.add("picked");

  try {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_id: roomId,
        plant_id: +btn.dataset.plant,
        liked: btn.dataset.liked === "1",
        answers: lastAnswers
      })
    });
    if (!res.ok) throw new Error("bad response");
    label.textContent = "Thanks! Added to the community ratings";
    loadStats();
  } catch (err) {
    label.textContent = "Couldn't save. Is the server running?";
  }
});

/* ---------- Start everything ---------- */
buildQuestions();
loadStats();
form.addEventListener("submit", function (e) {
  e.preventDefault();
  render(readPrefs());
});