const controls = {
  battery: document.querySelector("#battery"),
  speed: document.querySelector("#speed"),
  acceleration: document.querySelector("#acceleration"),
  braking: document.querySelector("#braking"),
  acLoad: document.querySelector("#acLoad"),
  route: document.querySelector("#route"),
  traffic: document.querySelector("#traffic"),
  weather: document.querySelector("#weather"),
  road: document.querySelector("#road"),
  mode: document.querySelector("#mode"),
};

const ui = {
  clock: document.querySelector("#clock"),
  driveMode: document.querySelector("#driveMode"),
  cabinTemp: document.querySelector("#cabinTemp"),
  batteryValue: document.querySelector("#batteryValue"),
  currentRange: document.querySelector("#currentRange"),
  optimizedRange: document.querySelector("#optimizedRange"),
  utilizationIndex: document.querySelector("#utilizationIndex"),
  routeDistance: document.querySelector("#routeDistance"),
  arrivalBuffer: document.querySelector("#arrivalBuffer"),
  primarySuggestion: document.querySelector("#primarySuggestion"),
  suggestionImpact: document.querySelector("#suggestionImpact"),
  secondaryTip: document.querySelector("#secondaryTip"),
  energyShort: document.querySelector("#energyShort"),
  gaugeNeedle: document.querySelector("#gaugeNeedle"),
  breakdownBars: document.querySelector("#breakdownBars"),
  tipsList: document.querySelector("#tipsList"),
  tripReport: document.querySelector("#tripReport"),
  assistantForm: document.querySelector("#assistantForm"),
  assistantInput: document.querySelector("#assistantInput"),
  assistantAnswer: document.querySelector("#assistantAnswer"),
};

let backendTimer;

const labelEls = {
  battery: document.querySelector("#batteryLabel"),
  speed: document.querySelector("#speedLabel"),
  acceleration: document.querySelector("#accelerationLabel"),
  braking: document.querySelector("#brakingLabel"),
  ac: document.querySelector("#acLabel"),
  route: document.querySelector("#routeLabel"),
};

const trafficPenalty = { light: 2, moderate: 7, dense: 14 };
const weatherPenalty = { clear: 0, hot: 6, rain: 5, wind: 7 };
const roadPenalty = { city: 5, highway: 8, hills: 14, mixed: 7 };
const modePenalty = { eco: -5, normal: 3, sport: 11 };

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function getState() {
  return {
    battery: Number(controls.battery.value),
    speed: Number(controls.speed.value),
    acceleration: Number(controls.acceleration.value),
    braking: Number(controls.braking.value),
    acLoad: Number(controls.acLoad.value),
    route: Number(controls.route.value),
    traffic: controls.traffic.value,
    weather: controls.weather.value,
    road: controls.road.value,
    mode: controls.mode.value,
  };
}

function classify(value, lowLabel, midLabel, highLabel) {
  if (value < 34) return lowLabel;
  if (value < 68) return midLabel;
  return highLabel;
}

function calculateModel(state) {
  const speedWaste = state.speed < 35 ? 4 : state.speed <= 72 ? 0 : (state.speed - 72) * 0.38;
  const accelerationWaste = state.acceleration * 0.15;
  const brakingWaste = state.braking > 58 ? (state.braking - 58) * 0.14 : 0;
  const acWaste = state.acLoad * 0.11;
  const contextWaste =
    trafficPenalty[state.traffic] +
    weatherPenalty[state.weather] +
    roadPenalty[state.road] +
    modePenalty[state.mode];

  const wastage = clamp(4 + speedWaste + accelerationWaste + brakingWaste + acWaste + contextWaste, 0, 42);
  const utilization = Math.round(clamp(100 - wastage * 1.55, 35, 98));
  const baseRange = state.battery * 3.25;
  const currentRange = Math.round(baseRange * (1 - wastage / 100));
  const optimizedWaste = Math.max(3, wastage - 11);
  const optimizedRange = Math.round(baseRange * (1 - optimizedWaste / 100));
  const savedRange = Math.max(0, optimizedRange - currentRange);
  const arrivalBuffer = currentRange - state.route;

  const breakdown = {
    motor: clamp(42 + state.speed * 0.16 + state.acceleration * 0.08, 35, 68),
    climate: clamp(8 + state.acLoad * 0.23 + (state.weather === "hot" ? 7 : 0), 5, 32),
    traffic: clamp(trafficPenalty[state.traffic] * 1.5 + (state.braking > 55 ? 5 : 0), 3, 26),
    road: clamp(roadPenalty[state.road] * 1.2, 4, 24),
    waste: clamp(wastage, 3, 42),
  };

  return {
    wastage,
    utilization,
    currentRange,
    optimizedRange,
    savedRange,
    arrivalBuffer,
    breakdown,
  };
}

function buildSuggestions(state, model) {
  const tips = [];

  if (state.acceleration > 62) {
    tips.push({
      title: "Smooth acceleration",
      body: "Ease into starts for the next few minutes. Sharp launches are the biggest avoidable drain right now.",
      impact: "Save 4-7 km",
    });
  }

  if (state.speed > 78) {
    tips.push({
      title: "Reduce cruising speed",
      body: "Stay near 68-74 km/h on this road. The current speed is pushing motor load up quickly.",
      impact: "Save 5-9 km",
    });
  } else if (state.traffic === "dense") {
    tips.push({
      title: "Traffic strategy",
      body: "Traffic is dense ahead. Hold 42-48 km/h, keep regen high, and avoid sharp starts.",
      impact: "Save 3-5 km",
    });
  }

  if (state.acLoad > 55 || state.weather === "hot") {
    tips.push({
      title: "Cabin efficiency",
      body: "Set cabin temperature around 24C and keep fan near level 2 to reduce climate load.",
      impact: "Climate load -6%",
    });
  }

  if (model.arrivalBuffer < 15) {
    tips.push({
      title: "Destination buffer",
      body: "Your arrival buffer is tight. Use Eco mode, reduce AC load, and keep acceleration smooth.",
      impact: "Protect arrival range",
    });
  }

  if (state.mode === "sport") {
    tips.push({
      title: "Switch drive mode",
      body: "Sport mode is costing range on this route. Eco mode gives the safest battery buffer.",
      impact: "Save 6-10 km",
    });
  }

  if (tips.length < 4) {
    tips.push(
      {
        title: "Regenerative braking",
        body: "Lift earlier before stops so regen can recover more energy instead of using hard braking.",
        impact: "Improve index",
      },
      {
        title: "Charging plan",
        body: model.arrivalBuffer > 35
          ? "Fast charging is not needed for this route. Charge after arrival if the next trip is long."
          : "Plan a short top-up only if the next destination adds more than 50 km.",
        impact: "Avoid battery stress",
      },
    );
  }

  return tips.slice(0, 4);
}

function answerQuestion(question, state, model, tips) {
  const q = question.toLowerCase();
  const topTip = tips[0];

  if (q.includes("draining") || q.includes("fast")) {
    return `Your battery is draining faster mainly because of ${state.traffic} traffic, ${state.acLoad > 55 ? "high AC load" : "cabin load"}, and ${state.acceleration > 58 ? "aggressive acceleration" : "stop-go driving"}. EVision estimates ${model.wastage.toFixed(1)}% avoidable energy wastage right now. ${topTip.body}`;
  }

  if (q.includes("destination") || q.includes("reach")) {
    if (model.arrivalBuffer >= 0) {
      return `Yes. Your current predicted range is ${model.currentRange} km for a ${state.route} km route, leaving about ${model.arrivalBuffer} km of buffer. If you follow the optimized driving plan, range can improve to about ${model.optimizedRange} km.`;
    }
    return `Not safely at the current pattern. Your predicted range is ${model.currentRange} km for a ${state.route} km route. Switch to Eco mode, lower AC load, and drive smoothly; otherwise plan a short charge stop.`;
  }

  if (q.includes("save") || q.includes("battery")) {
    return `${topTip.body} Also keep the cabin around 24C, avoid sharp braking, and stay in Eco mode. These changes can add roughly ${model.savedRange} km of practical range on this trip.`;
  }

  if (q.includes("fast charge") || q.includes("charge")) {
    if (model.arrivalBuffer > 30) {
      return `Fast charging is not needed for this route. You have about ${model.arrivalBuffer} km of arrival buffer, so charging after arrival is better unless your next trip is long.`;
    }
    return `A short top-up is sensible if you cannot reduce load. Your buffer is only ${model.arrivalBuffer} km, so use Eco mode first and charge if the next leg is more than 50 km.`;
  }

  return `EVision recommends: ${topTip.body} Your Battery Utilization Index is ${model.utilization}, current range is ${model.currentRange} km, and optimized range is ${model.optimizedRange} km.`;
}

function renderBreakdown(model) {
  const rows = [
    ["Motor load", model.breakdown.motor, "var(--green)"],
    ["Climate load", model.breakdown.climate, "var(--amber)"],
    ["Traffic and idle", model.breakdown.traffic, "var(--blue)"],
    ["Road and terrain", model.breakdown.road, "var(--mint)"],
    ["Avoidable wastage", model.breakdown.waste, "var(--red)"],
  ];

  ui.breakdownBars.innerHTML = rows
    .map(
      ([label, value, color]) => `
        <div class="bar-row">
          <div class="bar-meta"><span>${label}</span><span>${Math.round(value)}%</span></div>
          <div class="bar-track"><div class="bar-fill" style="width: ${value}%; background: ${color}"></div></div>
        </div>
      `,
    )
    .join("");
}

function renderTips(tips) {
  ui.tipsList.innerHTML = tips
    .map(
      (tip) => `
        <article class="tip-item">
          <strong>${tip.title}</strong>
          <p>${tip.body}</p>
        </article>
      `,
    )
    .join("");
}

function renderReport(state, model, tips) {
  const status = model.arrivalBuffer >= 0 ? "Destination reachable" : "Charging advised";
  const improvement = tips[0]?.title || "Efficiency steady";

  ui.tripReport.innerHTML = `
    <article class="report-item">
      <strong>${status}</strong>
      <p>Predicted range is ${model.currentRange} km for a ${state.route} km route. Optimized driving can add about ${model.savedRange} km.</p>
    </article>
    <article class="report-item">
      <strong>Current energy wastage: ${model.wastage.toFixed(1)}%</strong>
      <p>The biggest improvement area is ${improvement.toLowerCase()}.</p>
    </article>
    <article class="report-item">
      <strong>Weekly learning</strong>
      <p>EVision will compare this trip with past behavior to personalize future speed, AC, and charging advice.</p>
    </article>
  `;
}

function renderLabels(state) {
  labelEls.battery.textContent = `${state.battery}%`;
  labelEls.speed.textContent = `${state.speed} km/h`;
  labelEls.acceleration.textContent = classify(state.acceleration, "Soft", "Smooth", "Aggressive");
  labelEls.braking.textContent = classify(state.braking, "Light", "Balanced", "Harsh");
  labelEls.ac.textContent = `${Math.round(28 - state.acLoad / 25)}C`;
  labelEls.route.textContent = `${state.route} km`;
}

function render() {
  const state = getState();
  const model = calculateModel(state);
  const tips = buildSuggestions(state, model);

  renderLabels(state);

  ui.clock.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  ui.driveMode.textContent = state.mode.toUpperCase();
  ui.cabinTemp.textContent = `Cabin ${Math.round(28 - state.acLoad / 25)}C`;
  ui.batteryValue.textContent = `${state.battery}%`;
  ui.currentRange.textContent = `${model.currentRange} km`;
  ui.optimizedRange.textContent = `${model.optimizedRange} km`;
  ui.utilizationIndex.textContent = model.utilization;
  ui.routeDistance.textContent = `${state.route} km route`;
  ui.arrivalBuffer.textContent =
    model.arrivalBuffer >= 0 ? `${model.arrivalBuffer} km buffer` : `${Math.abs(model.arrivalBuffer)} km short`;
  ui.primarySuggestion.textContent = tips[0].body;
  ui.suggestionImpact.textContent = tips[0].impact;
  ui.secondaryTip.textContent = tips[1]?.body || "Keep speed steady and avoid sharp starts.";
  ui.energyShort.textContent = `Motor ${Math.round(model.breakdown.motor)}% · AC ${Math.round(model.breakdown.climate)}% · Waste ${model.wastage.toFixed(1)}%`;
  ui.gaugeNeedle.style.transform = `rotate(${clamp((model.utilization - 50) * 1.7, -45, 58)}deg)`;

  renderBreakdown(model);
  renderTips(tips);
  renderReport(state, model, tips);

  ui.assistantAnswer.dataset.lastModel = JSON.stringify({ state, model, tips });
  scheduleBackendAnalysis(state);
}

function applyBackendAnalysis(payload, state) {
  const model = {
    utilization: payload.battery_utilization_index,
    currentRange: payload.current_predicted_range,
    optimizedRange: payload.optimized_predicted_range,
    savedRange: Math.max(0, payload.optimized_predicted_range - payload.current_predicted_range),
    wastage: payload.energy_wastage_percent,
    arrivalBuffer: payload.arrival_buffer,
    breakdown: {
      motor: payload.energy_breakdown.motor_load,
      climate: payload.energy_breakdown.climate_load,
      traffic: payload.energy_breakdown.traffic_idle,
      road: payload.energy_breakdown.road_terrain,
      waste: payload.energy_breakdown.avoidable_wastage,
    },
  };
  const tips = payload.suggestions.map((tip) => ({
    title: tip.title,
    body: tip.message,
    impact: tip.impact,
  }));
  if (!tips.length) return;

  ui.currentRange.textContent = `${model.currentRange} km`;
  ui.optimizedRange.textContent = `${model.optimizedRange} km`;
  ui.utilizationIndex.textContent = model.utilization;
  ui.arrivalBuffer.textContent = model.arrivalBuffer >= 0
    ? `${model.arrivalBuffer} km buffer`
    : `${Math.abs(model.arrivalBuffer)} km short`;
  ui.primarySuggestion.textContent = tips[0].body;
  ui.suggestionImpact.textContent = tips[0].impact;
  ui.secondaryTip.textContent = tips[1]?.body || "Keep speed steady and avoid sharp starts.";
  ui.energyShort.textContent = `Motor ${Math.round(model.breakdown.motor)}% · AC ${Math.round(model.breakdown.climate)}% · Waste ${model.wastage.toFixed(1)}%`;
  ui.gaugeNeedle.style.transform = `rotate(${clamp((model.utilization - 50) * 1.7, -45, 58)}deg)`;
  renderBreakdown(model);
  renderTips(tips);
  renderReport(state, model, tips);
}

function scheduleBackendAnalysis(state) {
  clearTimeout(backendTimer);
  backendTimer = setTimeout(async () => {
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toBackendTelemetry(state)),
      });
      if (!response.ok) return;
      applyBackendAnalysis(await response.json(), state);
    } catch {
      // The local explainable model remains available when the backend is offline.
    }
  }, 120);
}

function toBackendTelemetry(state) {
  return {
    battery: state.battery,
    speed: state.speed,
    acceleration: state.acceleration,
    braking: state.braking,
    ac_load: state.acLoad,
    route_distance: state.route,
    traffic: state.traffic,
    weather: state.weather,
    road_type: state.road,
    drive_mode: state.mode,
    charging_habit_score: 72,
    past_efficiency_score: 78,
  };
}

async function handleAssistant(question) {
  const state = getState();
  const model = calculateModel(state);
  const tips = buildSuggestions(state, model);
  ui.assistantAnswer.textContent = "EVision is checking live telemetry and knowledge base context...";

  try {
    const response = await fetch("/api/assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        telemetry: toBackendTelemetry(state),
      }),
    });
    if (!response.ok) throw new Error("Backend unavailable");
    const payload = await response.json();
    ui.assistantAnswer.textContent = payload.answer;
  } catch {
    ui.assistantAnswer.textContent = answerQuestion(question, state, model, tips);
  }
}

Object.values(controls).forEach((control) => {
  control.addEventListener("input", render);
  control.addEventListener("change", render);
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    const question = button.dataset.question;
    ui.assistantInput.value = question;
    handleAssistant(question);
  });
});

ui.assistantForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = ui.assistantInput.value.trim();
  if (!question) return;
  handleAssistant(question);
});

render();
