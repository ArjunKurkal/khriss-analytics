"use strict";
/* PJM Weather Dashboard — static, no build step, no backend.
 * Data payloads (generated separately by the pipeline) live under data/:
 *   data/meta.json
 *   data/monthly_station/<code>.json
 *   data/monthly_group/<code>.json
 *   data/daily_group/<code>.json
 * Only the selected variable's payload files are fetched, on demand.
 */

/* ---------- Constants ---------- */

var BBOX = { latMin: 36, latMax: 43, lonMin: -89.5, lonMax: -73 };
var SUBREGIONS = ["East", "Central", "West"];
var DAILY_PAGE_SIZE = 100;

/* Fallback variable list, used only if data/meta.json is unavailable.
 * The authoritative list (labels, units, sum_ok, derived flags) comes from meta.json. */
var FALLBACK_VARIABLES = [
  { code: "temp",       label: "Temperature",        unit: "°F",    source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: false },
  { code: "heat_index", label: "Heat index",         unit: "°F",    source: "derived",     derived: true,  approx_note: null, sum_ok: false },
  { code: "wind_chill", label: "Wind chill",         unit: "°F",    source: "derived",     derived: true,  approx_note: null, sum_ok: false },
  { code: "dew_point",  label: "Dew point",          unit: "°F",    source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: false },
  { code: "rh",         label: "Relative humidity",  unit: "%",     source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: false },
  { code: "wet_bulb",   label: "Wet bulb",           unit: "°F",    source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: false },
  { code: "wind_speed", label: "Wind speed",         unit: "mph",   source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: false },
  { code: "wind_gust",  label: "Wind gust",          unit: "mph",   source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: false },
  { code: "wind_dir",   label: "Wind direction",     unit: "°",     source: "GHCN-Hourly", derived: false, approx_note: "Mean is a vector mean.", sum_ok: false },
  { code: "ghi",        label: "Global horizontal irradiance (ERA5-derived via Open-Meteo, not measured)", unit: "W/m²", source: "ERA5 via Open-Meteo", derived: true, approx_note: null, sum_ok: false },
  { code: "cloud_cover",label: "Cloud cover",        unit: "%",     source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: false },
  { code: "precip",     label: "Precipitation",      unit: "in",    source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: true },
  { code: "snowfall",   label: "Snowfall",           unit: "in",    source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: true },
  { code: "snow_depth", label: "Snow depth",         unit: "in",    source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: false },
  { code: "slp",        label: "Sea-level pressure", unit: "hPa",   source: "GHCN-Hourly", derived: false, approx_note: null, sum_ok: false }
];

var STAT_LABELS = {
  mean: "Mean",
  median: "Median",
  max: "Max (hourly)",
  max_daily: "Max daily",
  min: "Min",
  range: "Range (max − min)",
  sum: "Sum"
};

/* Colour scales: arrays of [r,g,b] stops, interpolated linearly.
 * Temperature-like variables use a blue→red diverging-style ramp;
 * precipitation-like variables use white→blue; others get sensible ramps. */
var SCALES = {
  tempLike:  [[49,54,149],[69,117,180],[171,217,233],[255,255,191],[254,204,92],[244,109,67],[165,0,38]],
  precipLike:[[255,255,255],[222,235,247],[158,202,225],[66,146,198],[8,69,148]],
  percent:   [[255,255,255],[204,235,225],[102,194,165],[35,139,120],[0,88,72]],
  wind:      [[255,255,245],[254,224,144],[253,174,97],[230,85,13],[128,40,0]],
  solar:     [[255,255,235],[255,231,160],[254,178,76],[240,90,30],[150,20,10]],
  pressure:  [[49,54,149],[116,173,209],[255,255,191],[244,109,67],[165,0,38]],
  grey:      [[245,245,245],[189,189,189],[115,115,115],[37,37,37]]
};
function scaleFor(code) {
  switch (code) {
    case "temp": case "heat_index": case "wind_chill": case "dew_point": case "wet_bulb":
      return SCALES.tempLike;
    case "precip": case "snowfall": case "snow_depth":
      return SCALES.precipLike;
    case "rh": case "cloud_cover":
      return SCALES.percent;
    case "wind_speed": case "wind_gust":
      return SCALES.wind;
    case "ghi":
      return SCALES.solar;
    case "slp":
      return SCALES.pressure;
    case "wind_dir":
      return SCALES.grey;
    default:
      return SCALES.tempLike;
  }
}
function scaleColor(stops, t) {
  if (t === null || t === undefined || isNaN(t)) t = 0;
  t = Math.max(0, Math.min(1, t));
  var pos = t * (stops.length - 1);
  var i = Math.floor(pos);
  var f = pos - i;
  if (i >= stops.length - 1) { i = stops.length - 2; f = 1; }
  var a = stops[i], b = stops[i + 1];
  return [
    Math.round(a[0] + (b[0] - a[0]) * f),
    Math.round(a[1] + (b[1] - a[1]) * f),
    Math.round(a[2] + (b[2] - a[2]) * f)
  ];
}
function rgbCss(c, alpha) {
  if (alpha === undefined) return "rgb(" + c[0] + "," + c[1] + "," + c[2] + ")";
  return "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + alpha + ")";
}
function gradientCss(stops) {
  var parts = [];
  for (var i = 0; i < stops.length; i++) {
    parts.push(rgbCss(stops[i]) + " " + Math.round(100 * i / (stops.length - 1)) + "%");
  }
  return "linear-gradient(to right, " + parts.join(", ") + ")";
}

/* ---------- State ---------- */

var state = {
  meta: null,
  variables: FALLBACK_VARIABLES,
  view: "table",
  dailyPage: 0,
  dailyRows: []
};
var cache = { station: {}, group: {}, daily: {} }; // code -> payload | null (null = missing/failed)
var loadCount = 0;

/* ---------- DOM helpers ---------- */

function el(id) { return document.getElementById(id); }
function esc(s) {
  return String(s === null || s === undefined ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
function showLoading(on) {
  loadCount += on ? 1 : -1;
  if (loadCount < 0) loadCount = 0;
  el("loading").hidden = loadCount === 0;
}
function showError(msg) {
  var box = el("errorBox");
  if (!msg) { box.hidden = true; box.textContent = ""; return; }
  box.hidden = false;
  box.textContent = msg;
}

/* ---------- Formatting ---------- */

function currentVariable() {
  var code = el("varSelect").value;
  for (var i = 0; i < state.variables.length; i++) {
    if (state.variables[i].code === code) return state.variables[i];
  }
  return { code: code, label: code, unit: "", derived: false, approx_note: null, sum_ok: false };
}
function decimalsFor(code) {
  if (code === "precip" || code === "snowfall" || code === "snow_depth") return 2;
  if (code === "wind_dir" || code === "slp" || code === "ghi") return 0;
  return 1;
}
function fmt(value, code) {
  if (value === null || value === undefined || (typeof value === "number" && isNaN(value))) return "—";
  return Number(value).toFixed(decimalsFor(code));
}
function fmtN(value) {
  if (value === null || value === undefined || isNaN(value)) return "—";
  return Number(value).toLocaleString("en-US");
}

/* ---------- Selection helpers ---------- */

function currentLevel() { return el("levelSelect").value; }
function currentStat() { return el("statSelect").value; }
function currentGroup() {
  var level = currentLevel();
  if (level === "pjm") return "PJM";
  if (level === "subregion" || level === "state") return el("entitySelect").value;
  return null; // station level
}
function currentStationId() { return el("stationSelect").value; }
function monthRange() {
  var s = el("startMonth").value, e = el("endMonth").value;
  if (s && e && s > e) { var t = s; s = e; e = t; }
  return { start: s || null, end: e || null };
}
function monthInRange(month, range) {
  if (range.start && month < range.start) return false;
  if (range.end && month > range.end) return false;
  return true;
}
function lastDayOfMonth(ym) {
  var y = Number(ym.slice(0, 4)), m = Number(ym.slice(5, 7));
  return new Date(Date.UTC(y, m, 0)).getUTCDate();
}
function dateRangeForMonths(range) {
  var start = range.start ? range.start + "-01" : null;
  var end = null;
  if (range.end) end = range.end + "-" + String(lastDayOfMonth(range.end)).padStart(2, "0");
  return { start: start, end: end };
}

/* ---------- Data loading (on demand, per variable) ---------- */

function fetchJSON(url) {
  return fetch(url).then(function (r) {
    if (!r.ok) return null;
    return r.json();
  }).catch(function () { return null; });
}
function loadPayload(kind, code) {
  // kind: "station" | "group" | "daily" -> data/monthly_station|monthly_group|daily_group/<code>.json
  if (Object.prototype.hasOwnProperty.call(cache[kind], code)) {
    return Promise.resolve(cache[kind][code]);
  }
  var dir = kind === "station" ? "monthly_station" : (kind === "group" ? "monthly_group" : "daily_group");
  showLoading(true);
  return fetchJSON("data/" + dir + "/" + encodeURIComponent(code) + ".json").then(function (data) {
    cache[kind][code] = data;
    showLoading(false);
    return data;
  });
}

/* ---------- Statistic extraction ---------- */

/* Value of `stat` at index i of a monthly entry {n,mean,median,min,max,max_daily,min_daily,sum}.
 * Returns null for missing data. wind_dir: max_daily and sum are meaningless -> null. */
function monthlyValueAt(entry, stat, i, code) {
  if (!entry) return null;
  function at(arr) {
    if (!arr) return null;
    var v = arr[i];
    return (v === null || v === undefined) ? null : v;
  }
  if (code === "wind_dir" && (stat === "max_daily" || stat === "sum")) return null;
  switch (stat) {
    case "mean": return at(entry.mean);
    case "median": return at(entry.median);
    case "max": return at(entry.max);
    case "max_daily": return at(entry.max_daily);
    case "min": return at(entry.min);
    case "sum": return entry.sum ? at(entry.sum) : null;
    case "range": {
      var mx = at(entry.max), mn = at(entry.min);
      return (mx === null || mn === null) ? null : mx - mn;
    }
    default: return null;
  }
}

/* Combine one station's monthly values over the selected months into a single
 * range value for the map:
 *   mean / median : n-weighted combination of monthly values (median is APPROXIMATE)
 *   min           : min of monthly mins
 *   max (hourly)  : max of monthly max
 *   max_daily     : max of monthly max_daily
 *   range         : (max of monthly max) − (min of monthly min)
 *   sum           : sum of monthly sums
 */
function stationRangeValue(entry, months, range, stat, code) {
  if (!entry) return { value: null, n: 0 };
  if (code === "wind_dir" && (stat === "max_daily" || stat === "sum")) return { value: null, n: 0 };
  var wSum = 0, wVal = 0, totalN = 0;
  var minV = null, maxV = null, maxDailyV = null, sumV = null;
  for (var i = 0; i < months.length; i++) {
    if (!monthInRange(months[i], range)) continue;
    var n = entry.n ? entry.n[i] : null;
    if (n !== null && n !== undefined) totalN += n;
    if (stat === "mean" || stat === "median") {
      var arr = stat === "mean" ? entry.mean : entry.median;
      var v = arr ? arr[i] : null;
      if (v !== null && v !== undefined && n !== null && n !== undefined && n > 0) {
        wVal += v * n; wSum += n;
      }
    } else if (stat === "min") {
      var mn = entry.min ? entry.min[i] : null;
      if (mn !== null && mn !== undefined && (minV === null || mn < minV)) minV = mn;
    } else if (stat === "max") {
      var mx = entry.max ? entry.max[i] : null;
      if (mx !== null && mx !== undefined && (maxV === null || mx > maxV)) maxV = mx;
    } else if (stat === "max_daily") {
      var md = entry.max_daily ? entry.max_daily[i] : null;
      if (md !== null && md !== undefined && (maxDailyV === null || md > maxDailyV)) maxDailyV = md;
    } else if (stat === "range") {
      var a = entry.max ? entry.max[i] : null;
      var b = entry.min ? entry.min[i] : null;
      if (a !== null && a !== undefined && (maxV === null || a > maxV)) maxV = a;
      if (b !== null && b !== undefined && (minV === null || b < minV)) minV = b;
    } else if (stat === "sum") {
      if (entry.sum) {
        var s = entry.sum[i];
        if (s !== null && s !== undefined) sumV = (sumV === null ? 0 : sumV) + s;
      }
    }
  }
  var value = null;
  if (stat === "mean" || stat === "median") value = wSum > 0 ? wVal / wSum : null;
  else if (stat === "min") value = minV;
  else if (stat === "max") value = maxV;
  else if (stat === "max_daily") value = maxDailyV;
  else if (stat === "range") value = (maxV !== null && minV !== null) ? maxV - minV : null;
  else if (stat === "sum") value = sumV;
  return { value: value, n: totalN };
}

/* ---------- Labelling / notes ---------- */

function isGroupMedianContext() {
  return currentStat() === "median" && currentLevel() !== "station";
}
function updateNotes() {
  var v = currentVariable();
  var notes = [];

  // Variable badges next to the selector
  var badges = [];
  if (v.code === "heat_index" || v.code === "wind_chill" || v.derived) {
    badges.push('<span class="badge derived">derived</span>');
  }
  if (v.code === "ghi") {
    badges.push('<span class="badge derived">ERA5-derived via Open-Meteo — not measured at stations</span>');
  }
  if (currentStat() === "median" && (currentLevel() !== "station" || state.view !== "table")) {
    badges.push('<span class="badge approx">median: approximate (rolled)</span>');
  }
  el("varBadges").innerHTML = badges.join("");

  if (v.code === "heat_index") notes.push("Heat index is a <strong>derived</strong> variable (computed from temperature and humidity), not a direct measurement.");
  if (v.code === "wind_chill") notes.push("Wind chill is a <strong>derived</strong> variable (computed from temperature and wind), not a direct measurement.");
  if (v.derived && v.code !== "heat_index" && v.code !== "wind_chill" && v.code !== "ghi") {
    notes.push("<strong>" + esc(v.label) + "</strong> is a derived variable.");
  }
  if (v.code === "ghi") notes.push("<strong>GHI:</strong> ERA5-derived via Open-Meteo — not measured at stations.");
  if (v.approx_note) notes.push("<strong>" + esc(v.label) + ":</strong> " + esc(v.approx_note));
  if (v.code === "wind_dir") {
    notes.push("Wind direction: the mean is a <strong>vector mean</strong>. Sum and max-daily statistics are not meaningful for wind direction and are shown as missing.");
  }
  if (isGroupMedianContext()) {
    notes.push("Group median is a median of station medians: <strong>approximate (rolled)</strong>.");
  }
  if (currentStat() === "median" && state.view !== "table") {
    notes.push("Map median combines monthly station medians (n-weighted): <strong>approximate (rolled)</strong>.");
  }
  el("notesBox").innerHTML = notes.map(function (n) {
    return '<div class="note-item">' + n + "</div>";
  }).join("");

  // Statistic note (sum availability)
  var statNote = el("statNote");
  if (!v.sum_ok) {
    statNote.textContent = "Sum is only available for variables where a sum is meaningful (precip, snowfall).";
  } else {
    statNote.textContent = "";
  }
}

function updateStatAvailability() {
  var v = currentVariable();
  var sel = el("statSelect");
  for (var i = 0; i < sel.options.length; i++) {
    var opt = sel.options[i];
    if (opt.value === "sum") {
      opt.disabled = !v.sum_ok;
      opt.textContent = v.sum_ok ? "Sum" : "Sum (not available for this variable)";
    }
    if (opt.value === "max_daily" && v.code === "wind_dir") {
      opt.disabled = true;
      opt.textContent = "Max daily (n/a for wind direction)";
    } else if (opt.value === "max_daily") {
      opt.disabled = false;
      opt.textContent = "Max daily";
    }
  }
  if ((sel.value === "sum" && !v.sum_ok) ||
      (sel.value === "max_daily" && v.code === "wind_dir")) {
    sel.value = "mean";
  }
}

/* ---------- Controls setup ---------- */

function populateVariables() {
  var sel = el("varSelect");
  var prev = sel.value;
  sel.innerHTML = "";
  state.variables.forEach(function (v) {
    var opt = document.createElement("option");
    opt.value = v.code;
    opt.textContent = v.label + (v.unit ? " (" + v.unit + ")" : "");
    sel.appendChild(opt);
  });
  if (prev && sel.querySelector('option[value="' + prev + '"]')) sel.value = prev;
}

function populateStations() {
  var sel = el("stationSelect");
  var prev = sel.value;
  sel.innerHTML = "";
  var stations = state.meta && state.meta.stations ? state.meta.stations : [];
  stations.forEach(function (s) {
    var opt = document.createElement("option");
    opt.value = s.id;
    opt.textContent = s.id + " — " + s.name + ", " + s.state + " (" + s.subregion + ")";
    sel.appendChild(opt);
  });
  if (prev && sel.querySelector('option[value="' + CSS.escape(prev) + '"]')) sel.value = prev;
}

function populateEntities() {
  var level = currentLevel();
  var wrap = el("entityControl");
  var sel = el("entitySelect");
  var prev = sel.value;
  var options = [];
  if (level === "subregion") {
    el("entityLabel").textContent = "Subregion";
    options = SUBREGIONS.slice();
    if (state.meta && state.meta.groups) {
      options = options.filter(function (g) { return state.meta.groups.indexOf(g) >= 0; });
      if (!options.length) options = SUBREGIONS.slice();
    }
  } else if (level === "state") {
    el("entityLabel").textContent = "State";
    var groups = state.meta && state.meta.groups ? state.meta.groups : [];
    options = groups.filter(function (g) {
      return g !== "PJM" && SUBREGIONS.indexOf(g) < 0;
    });
  }
  sel.innerHTML = "";
  options.forEach(function (g) {
    var opt = document.createElement("option");
    opt.value = g; opt.textContent = g;
    sel.appendChild(opt);
  });
  if (prev && options.indexOf(prev) >= 0) sel.value = prev;
  wrap.hidden = !(level === "subregion" || level === "state");
  el("stationControl").hidden = level !== "station";
}

function applyMetaToControls() {
  if (!state.meta) return;
  populateVariables();
  populateStations();
  populateEntities();
  if (state.meta.range) {
    var s = el("startMonth"), e = el("endMonth");
    s.min = state.meta.range.start; s.max = state.meta.range.end;
    e.min = state.meta.range.start; e.max = state.meta.range.end;
    if (!s.value) s.value = state.meta.range.start;
    if (!e.value) e.value = state.meta.range.end;
  }
  var info = [];
  if (state.meta.generated) info.push("Data generated: " + state.meta.generated);
  if (state.meta.range) info.push("Monthly range: " + state.meta.range.start + " to " + state.meta.range.end);
  if (state.meta.daily_range) info.push("Daily range: " + state.meta.daily_range.start + " to " + state.meta.daily_range.end);
  if (state.meta.stations) info.push(state.meta.stations.length + " stations");
  el("metaInfo").textContent = info.join(" · ");
}

/* ---------- Monthly table ---------- */

function renderMonthlyTable(payload, kind) {
  var v = currentVariable();
  var stat = currentStat();
  var range = monthRange();
  var tbody = el("monthlyTable").querySelector("tbody");
  tbody.innerHTML = "";
  var level = currentLevel();

  el("valueHeader").textContent =
    STAT_LABELS[stat] + (v.unit ? " (" + v.unit + ")" : "") +
    (stat === "median" && level !== "station" ? " — approximate (rolled)" : "") +
    (stat === "median" && level === "station" ? "" : "");

  var months = payload && payload.months ? payload.months : [];
  var entry = null, title = "";
  if (kind === "station") {
    var sid = currentStationId();
    entry = payload && payload.stations ? payload.stations[sid] : null;
    var st = findStation(sid);
    title = "Station " + sid + (st ? " — " + st.name + ", " + st.state : "");
  } else {
    var g = currentGroup();
    entry = payload && payload.groups ? payload.groups[g] : null;
    title = "Group: " + g;
  }
  el("monthlyTitle").textContent = "Monthly values — " + v.label + ", " + STAT_LABELS[stat];
  el("monthlyCaption").textContent = title +
    (range.start || range.end ? " · " + (range.start || "…") + " to " + (range.end || "…") : "") +
    (stat === "median" && level !== "station" ? " · Median is approximate (rolled): a median of station medians." : "");

  var shown = 0;
  months.forEach(function (month, i) {
    if (!monthInRange(month, range)) return;
    var value = monthlyValueAt(entry, stat, i, v.code);
    var nObs = entry && entry.n ? entry.n[i] : null;
    var nSt = null;
    if (kind === "group") nSt = entry && entry.n_stations ? entry.n_stations[i] : null;
    else nSt = (entry && entry.n && entry.n[i] !== null && entry.n[i] !== undefined) ? 1 : null;
    var tr = document.createElement("tr");
    tr.innerHTML = "<td>" + esc(month) + "</td>" +
      '<td class="num">' + fmt(value, v.code) + "</td>" +
      '<td class="num">' + fmtN(nSt) + "</td>" +
      '<td class="num">' + fmtN(nObs) + "</td>";
    tbody.appendChild(tr);
    shown++;
  });
  el("monthlyEmpty").hidden = shown > 0;
  if (!payload) {
    el("monthlyEmpty").textContent = "No monthly data file for variable “" + v.code + "” (data/" +
      (kind === "station" ? "monthly_station" : "monthly_group") + "/" + v.code + ".json).";
  } else if (!entry) {
    el("monthlyEmpty").textContent = "No data for this selection in the payload.";
  } else {
    el("monthlyEmpty").textContent = "No monthly data for this selection.";
  }
}

function findStation(id) {
  if (!state.meta || !state.meta.stations) return null;
  for (var i = 0; i < state.meta.stations.length; i++) {
    if (state.meta.stations[i].id === id) return state.meta.stations[i];
  }
  return null;
}

/* ---------- Daily table ---------- */

function buildDailyRows(payload) {
  var v = currentVariable();
  var level = currentLevel();
  var rows = [];
  if (!payload || level === "state" || level === "station") return rows;
  var g = currentGroup();
  var entry = payload.groups ? payload.groups[g] : null;
  if (!entry) return rows;
  var dr = dateRangeForMonths(monthRange());
  var dates = payload.dates || [];
  for (var i = 0; i < dates.length; i++) {
    var d = dates[i];
    if (dr.start && d < dr.start) continue;
    if (dr.end && d > dr.end) continue;
    function at(arr) {
      if (!arr) return null;
      var x = arr[i];
      return (x === null || x === undefined) ? null : x;
    }
    rows.push({
      date: d,
      mean: at(entry.mean),
      min: at(entry.min),
      max: at(entry.max),
      sum: (v.code === "wind_dir") ? null : (entry.sum ? at(entry.sum) : null),
      nStations: at(entry.n_stations)
    });
  }
  return rows;
}

function renderDailyTable(payload) {
  var level = currentLevel();
  var showDaily = (level === "pjm" || level === "subregion");
  el("dailyBlock").style.display = showDaily ? "" : "none";
  if (!showDaily) return;
  var v = currentVariable();
  state.dailyRows = buildDailyRows(payload);
  if (state.dailyPage * DAILY_PAGE_SIZE >= state.dailyRows.length) state.dailyPage = 0;
  var start = state.dailyPage * DAILY_PAGE_SIZE;
  var pageRows = state.dailyRows.slice(start, start + DAILY_PAGE_SIZE);
  var tbody = el("dailyTable").querySelector("tbody");
  tbody.innerHTML = "";
  pageRows.forEach(function (r) {
    var tr = document.createElement("tr");
    tr.innerHTML = "<td>" + esc(r.date) + "</td>" +
      '<td class="num">' + fmt(r.mean, v.code) + "</td>" +
      '<td class="num">' + fmt(r.min, v.code) + "</td>" +
      '<td class="num">' + fmt(r.max, v.code) + "</td>" +
      '<td class="num">' + (v.sum_ok ? fmt(r.sum, v.code) : "—") + "</td>" +
      '<td class="num">' + fmtN(r.nStations) + "</td>";
    tbody.appendChild(tr);
  });
  el("dailyEmpty").hidden = state.dailyRows.length > 0;
  if (!payload) {
    el("dailyEmpty").textContent = "No daily data file for variable “" + v.code + "” (data/daily_group/" + v.code + ".json).";
  } else {
    el("dailyEmpty").textContent = "No daily data for this selection.";
  }
  var total = state.dailyRows.length;
  var pages = Math.max(1, Math.ceil(total / DAILY_PAGE_SIZE));
  el("dailyPageInfo").textContent = total === 0 ? "0 days" :
    "Showing " + (start + 1) + "–" + (start + pageRows.length) + " of " + total +
    " days (page " + (state.dailyPage + 1) + " of " + pages + "; rows are paginated at " +
    DAILY_PAGE_SIZE + " per page)";
  el("dailyPrev").disabled = state.dailyPage <= 0;
  el("dailyNext").disabled = state.dailyPage >= pages - 1;
  el("dailyCaption").textContent = "Group: " + currentGroup() + " · Daily mean / min / max" +
    (v.sum_ok ? " / sum" : "") + " per day within the selected month range." +
    (v.code === "wind_dir" ? " Sum is not meaningful for wind direction." : "");
}

/* ---------- Map ---------- */

var map = null, markerLayer = null, heatLayer = null, legendControl = null;

function ensureMap() {
  if (map) return true;
  if (typeof L === "undefined") {
    el("map").innerHTML = '<p class="empty" style="padding:12px">Leaflet failed to load (CDN unavailable). The table view still works.</p>';
    return false;
  }
  map = L.map("map");
  map.fitBounds([[BBOX.latMin, BBOX.lonMin], [BBOX.latMax, BBOX.lonMax]]);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 12,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);
  L.rectangle([[BBOX.latMin, BBOX.lonMin], [BBOX.latMax, BBOX.lonMax]], {
    color: "#2166ac", weight: 1, fill: false, dashArray: "4 4"
  }).addTo(map);
  markerLayer = L.layerGroup().addTo(map);
  legendControl = L.control({ position: "bottomright" });
  legendControl.onAdd = function () {
    var div = L.DomUtil.create("div", "map-legend");
    div.id = "mapLegend";
    div.innerHTML = "No data";
    return div;
  };
  legendControl.addTo(map);
  return true;
}

function computeStationValues(payload) {
  var v = currentVariable();
  var stat = currentStat();
  var range = monthRange();
  var out = [];
  if (!payload || !payload.stations || !state.meta || !state.meta.stations) return out;
  var months = payload.months || [];
  state.meta.stations.forEach(function (s) {
    var entry = payload.stations[s.id];
    if (!entry) return;
    var r = stationRangeValue(entry, months, range, stat, v.code);
    out.push({ station: s, value: r.value, n: r.n });
  });
  return out;
}

/* IDW (power 2) interpolation onto a lat/lon grid, rendered to a canvas. */
function buildHeatmapImage(points, stops, vMin, vMax) {
  var NX = 132, NY = 56; // grid cells across the bbox (~0.125° steps)
  var canvas = document.createElement("canvas");
  canvas.width = NX; canvas.height = NY;
  var ctx = canvas.getContext("2d");
  var img = ctx.createImageData(NX, NY);
  var span = (vMax - vMin) || 1;
  for (var y = 0; y < NY; y++) {
    var lat = BBOX.latMax - (y + 0.5) / NY * (BBOX.latMax - BBOX.latMin);
    for (var x = 0; x < NX; x++) {
      var lon = BBOX.lonMin + (x + 0.5) / NX * (BBOX.lonMax - BBOX.lonMin);
      var wSum = 0, wVal = 0, exact = null;
      for (var k = 0; k < points.length; k++) {
        var p = points[k];
        var dLat = lat - p.station.lat, dLon = lon - p.station.lon;
        var d2 = dLat * dLat + dLon * dLon;
        if (d2 < 1e-8) { exact = p.value; break; }
        var w = 1 / d2; // inverse-distance weighting, power 2
        wSum += w; wVal += w * p.value;
      }
      var val = exact !== null ? exact : (wSum > 0 ? wVal / wSum : null);
      var idx = (y * NX + x) * 4;
      if (val === null) { img.data[idx + 3] = 0; continue; }
      var c = scaleColor(stops, (val - vMin) / span);
      img.data[idx] = c[0]; img.data[idx + 1] = c[1]; img.data[idx + 2] = c[2];
      img.data[idx + 3] = 165; // semi-transparent
    }
  }
  ctx.putImageData(img, 0, 0);
  return canvas.toDataURL("image/png");
}

function renderMap(payload) {
  if (state.view === "table") return;
  if (!ensureMap()) return;
  var v = currentVariable();
  var stat = currentStat();
  var range = monthRange();
  var values = computeStationValues(payload);
  var valid = values.filter(function (d) { return d.value !== null && d.value !== undefined && !isNaN(d.value); });

  el("mapTitle").textContent = "Station map — " + v.label + ", " + STAT_LABELS[stat];
  el("mapCaption").textContent =
    "Each station's value is computed in the browser from its monthly values over " +
    (range.start || "…") + " to " + (range.end || "…") + ": mean/median are n-weighted combinations of monthly values" +
    (stat === "median" ? " (median: approximate (rolled))" : "") +
    ", min is the min of monthly mins, max is the max of monthly max values, range is max − min, sum is the sum of monthly sums." +
    (v.code === "ghi" ? " GHI is ERA5-derived via Open-Meteo — not measured at stations." : "") +
    ((v.code === "heat_index" || v.code === "wind_chill") ? " This variable is derived." : "");

  markerLayer.clearLayers();
  if (heatLayer) { map.removeLayer(heatLayer); heatLayer = null; }

  el("mapEmpty").hidden = valid.length > 0;
  if (!payload) {
    el("mapEmpty").textContent = "No monthly station data file for variable “" + v.code + "” (data/monthly_station/" + v.code + ".json).";
  } else {
    el("mapEmpty").textContent = "No station values could be computed for this selection.";
  }
  var legend = el("mapLegend");
  if (!valid.length) { if (legend) legend.innerHTML = "No data"; return; }

  var vMin = Math.min.apply(null, valid.map(function (d) { return d.value; }));
  var vMax = Math.max.apply(null, valid.map(function (d) { return d.value; }));
  var stops = scaleFor(v.code);
  var span = (vMax - vMin) || 1;

  var showMarkers = el("layerMarkers").checked;
  var showHeat = el("layerHeat").checked;

  if (showHeat) {
    var url = buildHeatmapImage(valid, stops, vMin, vMax);
    heatLayer = L.imageOverlay(url, [[BBOX.latMin, BBOX.lonMin], [BBOX.latMax, BBOX.lonMax]], { opacity: 0.75, interactive: false });
    heatLayer.addTo(map);
  }
  if (showMarkers) {
    valid.forEach(function (d) {
      var c = scaleColor(stops, (d.value - vMin) / span);
      var marker = L.circleMarker([d.station.lat, d.station.lon], {
        radius: 8, color: "#333", weight: 1, fillColor: rgbCss(c), fillOpacity: 0.9
      });
      marker.bindPopup(
        "<strong>" + esc(d.station.name) + "</strong> (" + esc(d.station.id) + ")<br>" +
        "State: " + esc(d.station.state) + " · Subregion: " + esc(d.station.subregion) + "<br>" +
        esc(v.label) + " — " + esc(STAT_LABELS[stat]) + ": <strong>" + fmt(d.value, v.code) +
        (v.unit ? " " + esc(v.unit) : "") + "</strong>" +
        (stat === "median" ? " (approximate (rolled))" : "") + "<br>" +
        "n obs in range: " + fmtN(d.n)
      );
      marker.addTo(markerLayer);
    });
    // Also plot stations with no valid value as small grey markers.
    values.forEach(function (d) {
      if (d.value !== null && d.value !== undefined && !isNaN(d.value)) return;
      var marker = L.circleMarker([d.station.lat, d.station.lon], {
        radius: 5, color: "#888", weight: 1, fillColor: "#cccccc", fillOpacity: 0.7
      });
      marker.bindPopup("<strong>" + esc(d.station.name) + "</strong> (" + esc(d.station.id) + ")<br>No data for this selection.");
      marker.addTo(markerLayer);
    });
  }

  if (legend) {
    legend.innerHTML =
      "<strong>" + esc(v.label) + "</strong><br>" + esc(STAT_LABELS[stat]) +
      (stat === "median" ? " — approximate (rolled)" : "") +
      '<div class="gradient" style="background:' + gradientCss(stops) + '"></div>' +
      '<div class="ends"><span>' + fmt(vMin, v.code) + "</span><span>" + fmt(vMax, v.code) + "</span></div>" +
      "<div>" + esc(v.unit || "") + " · " + valid.length + " stations</div>";
  }
  setTimeout(function () { if (map) map.invalidateSize(); }, 50);
}

/* ---------- View toggle ---------- */

function applyView() {
  el("tableSection").hidden = state.view === "map";
  el("mapSection").hidden = state.view === "table";
  ["viewTableBtn", "viewMapBtn", "viewBothBtn"].forEach(function (id) {
    el(id).classList.remove("active");
  });
  el(state.view === "table" ? "viewTableBtn" : state.view === "map" ? "viewMapBtn" : "viewBothBtn").classList.add("active");
}

/* ---------- Refresh ---------- */

function refresh() {
  updateStatAvailability();
  updateNotes();
  var code = currentVariable().code;
  var level = currentLevel();
  state.dailyPage = 0;

  var needDaily = (level === "pjm" || level === "subregion") && state.view !== "map";
  var jobs = [];
  var monthlyKind = level === "station" ? "station" : "group";
  jobs.push(loadPayload(monthlyKind, code));
  jobs.push(loadPayload("station", code)); // map always uses monthly_station
  if (needDaily) jobs.push(loadPayload("daily", code));

  Promise.all(jobs).then(function (results) {
    // Guard against stale responses after a fast selection change.
    if (currentVariable().code !== code) return;
    var monthlyPayload = results[0];
    var stationPayload = results[1];
    var dailyPayload = needDaily ? results[2] : null;

    var missing = [];
    if (!monthlyPayload) missing.push("monthly " + (monthlyKind === "station" ? "station" : "group") + " data");
    if (!stationPayload && monthlyKind !== "station") missing.push("monthly station data (map)");
    showError(missing.length ? "Could not load " + missing.join(" and ") + " for variable “" + code + "”. Other views may still work." : null);

    renderMonthlyTable(monthlyPayload, monthlyKind);
    if (needDaily) renderDailyTable(dailyPayload);
    else el("dailyBlock").style.display = "none";
    renderMap(stationPayload);
  });
}

/* ---------- Init ---------- */

function bindEvents() {
  el("varSelect").addEventListener("change", refresh);
  el("statSelect").addEventListener("change", refresh);
  el("levelSelect").addEventListener("change", function () {
    populateEntities();
    refresh();
  });
  el("entitySelect").addEventListener("change", refresh);
  el("stationSelect").addEventListener("change", refresh);
  el("startMonth").addEventListener("change", refresh);
  el("endMonth").addEventListener("change", refresh);
  el("layerMarkers").addEventListener("change", refresh);
  el("layerHeat").addEventListener("change", refresh);
  el("dailyPrev").addEventListener("click", function () {
    if (state.dailyPage > 0) { state.dailyPage--; renderDailyFromCache(); }
  });
  el("dailyNext").addEventListener("click", function () {
    state.dailyPage++; renderDailyFromCache();
  });
  el("viewTableBtn").addEventListener("click", function () { setView("table"); });
  el("viewMapBtn").addEventListener("click", function () { setView("map"); });
  el("viewBothBtn").addEventListener("click", function () { setView("both"); });
}
function renderDailyFromCache() {
  var code = currentVariable().code;
  loadPayload("daily", code).then(function (p) { renderDailyTable(p); });
}
function setView(view) {
  state.view = view;
  applyView();
  refresh();
}

function init() {
  populateVariables();
  bindEvents();
  applyView();
  showLoading(true);
  fetchJSON("data/meta.json").then(function (meta) {
    showLoading(false);
    if (meta) {
      state.meta = meta;
      if (meta.variables && meta.variables.length) state.variables = meta.variables;
    } else {
      showError("Could not load data/meta.json — using the built-in variable list; payload tables/maps will be empty until data is generated.");
    }
    applyMetaToControls();
    refresh();
  });
}

document.addEventListener("DOMContentLoaded", init);
