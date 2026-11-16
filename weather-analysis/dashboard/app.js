"use strict";
/* PJM Weather Dashboard — static, no build step, no backend.
 * Data payloads (generated separately by the pipeline) live under data/:
 *   data/meta.json
 *   data/monthly_station/<code>.json
 *   data/monthly_group/<code>.json
 *   data/daily_group/<code>.json
 * Only the selected variable's payload files are fetched, on demand.
 *
 * Selector scheme (cascading, no silent precedence):
 *   1 · Aggregation level  -> PJM total | Subregion | State | Station
 *   2 · Group              -> only at Subregion/State level; "All" (default)
 *                             lists every group of that level together in
 *                             the table, a single group narrows table + map.
 *   2 · Station scope      -> only at Station level; scopes step 3 and the map.
 *   3 · Station            -> only at Station level; only stations inside the
 *                             current scope are offered.
 * A control that does not apply at the current level is hidden, never ignored.
 * Statistics are multi-select: the monthly table shows one column per
 * selected statistic, in selection order. The map colours by the first
 * selected statistic unless swapped via the map-only statistic control.
 */

/* ---------- Constants ---------- */

var BBOX = { latMin: 36, latMax: 43, lonMin: -89.5, lonMax: -73 };
var SUBREGIONS = ["East", "Central", "West"];
var DAILY_PAGE_SIZE = 100;
var STAT_UI_ORDER = ["mean", "median", "max", "max_daily", "min", "range", "sum"];

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

/* Colour scales: arrays of [r,g,b] stops, interpolated linearly. */
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
  view: "both",
  selectedStats: ["mean", "max", "min"],
  mapStat: "mean",
  dailyPage: 0,
  dailyRows: [],
  refreshToken: 0
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
function selectedStats() { return state.selectedStats.slice(); }
function statAvailable(stat) {
  var v = currentVariable();
  if (stat === "sum") return !!v.sum_ok;
  if (stat === "max_daily") return v.code !== "wind_dir";
  return true;
}
function currentGroupSelection() {
  // Only meaningful at subregion/state level. Returns "ALL" or one group name.
  var level = currentLevel();
  if (level !== "subregion" && level !== "state") return null;
  return el("groupSelect").value || "ALL";
}
function currentScope() {
  if (currentLevel() !== "station") return null;
  return el("scopeSelect").value || "ALL";
}
function currentStationId() {
  if (currentLevel() !== "station") return null;
  return el("stationSelect").value || null;
}
function allStations() {
  return state.meta && state.meta.stations ? state.meta.stations : [];
}
function statesList() {
  var groups = state.meta && state.meta.groups ? state.meta.groups : [];
  return groups.filter(function (g) { return g !== "PJM" && SUBREGIONS.indexOf(g) < 0; });
}
function stationsInScope(scope) {
  var stations = allStations();
  if (!scope || scope === "ALL") return stations.slice();
  if (scope.indexOf("SR:") === 0) {
    var sr = scope.slice(3);
    return stations.filter(function (s) { return s.subregion === sr; });
  }
  if (scope.indexOf("ST:") === 0) {
    var st = scope.slice(3);
    return stations.filter(function (s) { return s.state === st; });
  }
  return stations.slice();
}
function scopeLabel(scope) {
  if (!scope || scope === "ALL") return "All PJM stations";
  if (scope.indexOf("SR:") === 0) return "Subregion " + scope.slice(3);
  if (scope.indexOf("ST:") === 0) return scope.slice(3);
  return scope;
}
/* Stations the map displays under the current cascade. */
function mapStationFilter() {
  var level = currentLevel();
  var stations = allStations();
  if (level === "pjm") return stations.slice();
  if (level === "subregion" || level === "state") {
    var g = currentGroupSelection();
    if (!g || g === "ALL") return stations.slice();
    if (level === "subregion") return stations.filter(function (s) { return s.subregion === g; });
    return stations.filter(function (s) { return s.state === g; });
  }
  return stationsInScope(currentScope());
}
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
function subtractMonths(ym, n) {
  var y = Number(ym.slice(0, 4)), m = Number(ym.slice(5, 7));
  var total = y * 12 + (m - 1) - n;
  var ny = Math.floor(total / 12), nm = (total % 12) + 1;
  return ny + "-" + String(nm).padStart(2, "0");
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
function findStation(id) {
  var stations = allStations();
  for (var i = 0; i < stations.length; i++) {
    if (stations[i].id === id) return stations[i];
  }
  return null;
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

/* ---------- Statistics multi-select ---------- */

function pruneUnavailableStats() {
  var before = state.selectedStats.join(",");
  state.selectedStats = state.selectedStats.filter(statAvailable);
  if (!state.selectedStats.length) state.selectedStats = ["mean"];
  if (state.selectedStats.indexOf(state.mapStat) < 0) state.mapStat = state.selectedStats[0];
  return state.selectedStats.join(",") !== before;
}
function updateStatUI(guardMsg) {
  var v = currentVariable();
  var boxes = el("statList").querySelectorAll("input[type=checkbox][data-stat]");
  boxes.forEach(function (box) {
    var stat = box.getAttribute("data-stat");
    box.checked = state.selectedStats.indexOf(stat) >= 0;
    box.disabled = !statAvailable(stat);
    box.parentElement.classList.toggle("stat-disabled", box.disabled);
  });
  el("statList").querySelectorAll(".stat-order").forEach(function (span) {
    var stat = span.getAttribute("data-order-for");
    var idx = state.selectedStats.indexOf(stat);
    span.textContent = idx >= 0 ? "#" + (idx + 1) : "";
  });
  var notes = [];
  if (!v.sum_ok) notes.push("Sum is only available for variables where a sum is meaningful (precipitation, snowfall).");
  if (v.code === "wind_dir") notes.push("Max daily is not meaningful for wind direction.");
  if (guardMsg) notes.push(guardMsg);
  el("statNote").textContent = notes.join(" ");
  updateMapStatOptions();
}
function onStatCheckboxChange(box) {
  var stat = box.getAttribute("data-stat");
  if (box.checked) {
    if (state.selectedStats.indexOf(stat) < 0) state.selectedStats.push(stat);
    updateStatUI();
  } else {
    if (state.selectedStats.length <= 1) {
      box.checked = true; // never leave the table with zero statistic columns
      updateStatUI("At least one statistic must be selected.");
      return;
    }
    state.selectedStats = state.selectedStats.filter(function (s) { return s !== stat; });
    if (state.mapStat === stat) state.mapStat = state.selectedStats[0];
    updateStatUI();
  }
  refresh();
}
function updateMapStatOptions() {
  var sel = el("mapStatSelect");
  if (!sel) return;
  var prev = sel.value;
  sel.innerHTML = "";
  state.selectedStats.forEach(function (stat) {
    var opt = document.createElement("option");
    opt.value = stat;
    opt.textContent = STAT_LABELS[stat] + (stat === state.selectedStats[0] ? " (first selected — default)" : "");
    sel.appendChild(opt);
  });
  if (state.selectedStats.indexOf(state.mapStat) < 0) state.mapStat = state.selectedStats[0];
  sel.value = state.selectedStats.indexOf(prev) >= 0 && prev === state.mapStat ? prev : state.mapStat;
  sel.value = state.mapStat;
}

/* ---------- Labelling / notes ---------- */

function updateNotes() {
  var v = currentVariable();
  var notes = [];
  var stats = selectedStats();
  var hasMedian = stats.indexOf("median") >= 0;

  var badges = [];
  if (v.code === "heat_index" || v.code === "wind_chill" || v.derived) {
    badges.push('<span class="badge derived">derived</span>');
  }
  if (v.code === "ghi") {
    badges.push('<span class="badge derived">ERA5-derived via Open-Meteo — not measured at stations</span>');
  }
  if (hasMedian && currentLevel() !== "station") {
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
  if (hasMedian && currentLevel() !== "station") {
    notes.push("Group median is a median of station medians: <strong>approximate (rolled)</strong>.");
  }
  if (hasMedian && state.view !== "table") {
    notes.push("Map medians combine monthly station medians (n-weighted): <strong>approximate (rolled)</strong>.");
  }
  el("notesBox").innerHTML = notes.map(function (n) {
    return '<div class="note-item">' + n + "</div>";
  }).join("");
}

function updateCascadeHint() {
  var level = currentLevel();
  var total = allStations().length;
  var hint = "";
  if (level === "pjm") {
    hint = "Showing: <strong>PJM total</strong> — one row per month in the table; the map shows all " + total +
      " stations. Group and station pickers do not apply at this level, so they are hidden.";
  } else if (level === "subregion" || level === "state") {
    var g = currentGroupSelection();
    var levelName = level === "subregion" ? "Subregion" : "State";
    var mapN = mapStationFilter().length;
    if (g === "ALL") {
      hint = "Showing: <strong>all " + (level === "subregion" ? "subregions" : "states") + " together</strong> — " +
        "the table lists every " + levelName.toLowerCase() + "; the map shows all " + total + " stations. " +
        "Pick a single " + levelName.toLowerCase() + " in step 2 to narrow both.";
    } else {
      hint = "Showing: <strong>" + levelName + " — " + esc(g) + "</strong> — the table lists " + esc(g) +
        " only; the map shows its " + mapN + " station" + (mapN === 1 ? "" : "s") + ".";
    }
  } else if (level === "station") {
    var scope = currentScope();
    var scoped = stationsInScope(scope);
    var sid = currentStationId();
    var st = sid ? findStation(sid) : null;
    hint = "Showing: <strong>Station level · scope: " + esc(scopeLabel(scope)) + "</strong> — the station picker " +
      "offers only the " + scoped.length + " station" + (scoped.length === 1 ? "" : "s") + " in this scope" +
      (st ? "; the table lists <strong>" + esc(st.name) + "</strong>" : "") +
      "; the map shows the scoped stations with the selected station highlighted.";
  }
  el("cascadeHint").innerHTML = hint;
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

function populateGroupOptions() {
  var level = currentLevel();
  var sel = el("groupSelect");
  var prev = sel.value;
  var options = [];
  if (level === "subregion") {
    el("groupLabel").textContent = "2 · Subregion";
    var subs = SUBREGIONS.slice();
    if (state.meta && state.meta.groups) {
      subs = subs.filter(function (g) { return state.meta.groups.indexOf(g) >= 0; });
      if (!subs.length) subs = SUBREGIONS.slice();
    }
    options = [{ value: "ALL", label: "All subregions" }].concat(
      subs.map(function (g) { return { value: g, label: g }; }));
  } else if (level === "state") {
    el("groupLabel").textContent = "2 · State";
    options = [{ value: "ALL", label: "All states" }].concat(
      statesList().map(function (g) { return { value: g, label: g }; }));
  }
  sel.innerHTML = "";
  options.forEach(function (o) {
    var opt = document.createElement("option");
    opt.value = o.value; opt.textContent = o.label;
    sel.appendChild(opt);
  });
  var values = options.map(function (o) { return o.value; });
  sel.value = values.indexOf(prev) >= 0 ? prev : "ALL";
}

function populateScopeOptions() {
  var sel = el("scopeSelect");
  var prev = sel.value;
  sel.innerHTML = "";
  var all = document.createElement("option");
  all.value = "ALL"; all.textContent = "All PJM stations";
  sel.appendChild(all);
  var gSr = document.createElement("optgroup");
  gSr.label = "Subregions";
  SUBREGIONS.forEach(function (sr) {
    var opt = document.createElement("option");
    opt.value = "SR:" + sr; opt.textContent = sr;
    gSr.appendChild(opt);
  });
  sel.appendChild(gSr);
  var gSt = document.createElement("optgroup");
  gSt.label = "States";
  statesList().forEach(function (st) {
    var opt = document.createElement("option");
    opt.value = "ST:" + st; opt.textContent = st;
    gSt.appendChild(opt);
  });
  sel.appendChild(gSt);
  var values = ["ALL"].concat(
    SUBREGIONS.map(function (sr) { return "SR:" + sr; }),
    statesList().map(function (st) { return "ST:" + st; }));
  sel.value = values.indexOf(prev) >= 0 ? prev : "ALL";
}

function populateStationsScoped() {
  var sel = el("stationSelect");
  var prev = sel.value;
  var stations = stationsInScope(currentScope());
  sel.innerHTML = "";
  if (!stations.length) {
    var opt = document.createElement("option");
    opt.value = ""; opt.textContent = "No stations in this scope"; opt.disabled = true;
    sel.appendChild(opt);
    return;
  }
  stations.forEach(function (s) {
    var opt = document.createElement("option");
    opt.value = s.id;
    opt.textContent = s.id + " — " + s.name + ", " + s.state + " (" + s.subregion + ")";
    sel.appendChild(opt);
  });
  if (prev && stations.some(function (s) { return s.id === prev; })) sel.value = prev;
}

/* Show/hide and (re)build the cascade controls for the current level.
 * Controls that do not apply at this level are hidden — never left visible
 * to be silently ignored. */
function populateCascade() {
  var level = currentLevel();
  var isGroupLevel = level === "subregion" || level === "state";
  var isStationLevel = level === "station";
  el("groupControl").hidden = !isGroupLevel;
  el("scopeControl").hidden = !isStationLevel;
  el("stationControl").hidden = !isStationLevel;
  if (isGroupLevel) populateGroupOptions();
  if (isStationLevel) {
    populateScopeOptions();
    populateStationsScoped();
  }
}

function applyMetaToControls() {
  if (!state.meta) return;
  populateVariables();
  populateCascade();
  if (state.meta.range) {
    var s = el("startMonth"), e = el("endMonth");
    s.min = state.meta.range.start; s.max = state.meta.range.end;
    e.min = state.meta.range.start; e.max = state.meta.range.end;
    if (!e.value) e.value = state.meta.range.end;
    // Default date range: trailing 12 months of the data.
    if (!s.value) s.value = subtractMonths(state.meta.range.end, 11);
  }
  var info = [];
  if (state.meta.generated) info.push("Data generated: " + state.meta.generated);
  if (state.meta.range) info.push("Monthly range: " + state.meta.range.start + " to " + state.meta.range.end);
  if (state.meta.daily_range) info.push("Daily range: " + state.meta.daily_range.start + " to " + state.meta.daily_range.end);
  if (state.meta.stations) info.push(state.meta.stations.length + " stations");
  el("metaInfo").textContent = info.join(" · ");
}

/* ---------- Monthly table ---------- */

/* Entities the monthly table lists under the current cascade. At group
 * levels with "All" selected this is every group of the level, together. */
function monthlyEntities() {
  var level = currentLevel();
  if (level === "pjm") return [{ key: "PJM", label: "PJM", kind: "group" }];
  if (level === "subregion" || level === "state") {
    var g = currentGroupSelection();
    var all = level === "subregion" ? SUBREGIONS.slice() : statesList();
    var keys = g === "ALL" ? all : [g];
    return keys.map(function (k) { return { key: k, label: k, kind: "group" }; });
  }
  var sid = currentStationId();
  if (!sid) return [];
  var st = findStation(sid);
  return [{ key: sid, label: st ? st.name + " (" + sid + ")" : sid, kind: "station" }];
}

function renderMonthlyTable(payload, kind) {
  var v = currentVariable();
  var stats = selectedStats();
  var range = monthRange();
  var level = currentLevel();
  var entities = monthlyEntities();
  var months = payload && payload.months ? payload.months : [];
  var showEntityCol = entities.length > 1;
  var entityColLabel = level === "subregion" ? "Subregion" : (level === "state" ? "State" : "Group");

  // Header: Month | [Entity] | one column per selected statistic, in
  // selection order | N stations | N obs
  var headHtml = "<tr><th>Month</th>";
  if (showEntityCol) headHtml += "<th>" + esc(entityColLabel) + "</th>";
  stats.forEach(function (stat) {
    var approx = stat === "median" && level !== "station";
    headHtml += '<th class="num">' + esc(STAT_LABELS[stat]) +
      (v.unit ? " (" + esc(v.unit) + ")" : "") + (approx ? " ≈" : "") + "</th>";
  });
  headHtml += '<th class="num">N stations</th><th class="num">N obs</th></tr>';
  el("monthlyHead").innerHTML = headHtml;

  el("monthlyTitle").textContent = "Monthly values — " + v.label;
  var entityDesc = level === "pjm" ? "PJM total" :
    level === "station" ? (entities.length ? "Station " + entities[0].label : "No station selected") :
    (currentGroupSelection() === "ALL"
      ? "All " + (level === "subregion" ? "subregions" : "states") + " together"
      : (level === "subregion" ? "Subregion " : "State ") + currentGroupSelection());
  el("monthlyCaption").textContent = entityDesc +
    (range.start || range.end ? " · " + (range.start || "…") + " to " + (range.end || "…") : "") +
    " · Statistic columns are in selection order (#1 first)" +
    (stats.indexOf("median") >= 0 && level !== "station" ? " · Median ≈ approximate (rolled): a median of station medians." : "");

  var tbody = el("monthlyTable").querySelector("tbody");
  tbody.innerHTML = "";
  var shown = 0;
  entities.forEach(function (ent) {
    var entry = null;
    if (payload) {
      entry = kind === "station"
        ? (payload.stations ? payload.stations[ent.key] : null)
        : (payload.groups ? payload.groups[ent.key] : null);
    }
    months.forEach(function (month, i) {
      if (!monthInRange(month, range)) return;
      var nObs = entry && entry.n ? entry.n[i] : null;
      var nSt = null;
      if (kind === "group") nSt = entry && entry.n_stations ? entry.n_stations[i] : null;
      else nSt = (nObs !== null && nObs !== undefined) ? 1 : null;
      var tr = document.createElement("tr");
      var html = "<td>" + esc(month) + "</td>";
      if (showEntityCol) html += "<td>" + esc(ent.label) + "</td>";
      stats.forEach(function (stat) {
        html += '<td class="num">' + fmt(monthlyValueAt(entry, stat, i, v.code), v.code) + "</td>";
      });
      html += '<td class="num">' + fmtN(nSt) + "</td>" +
        '<td class="num">' + fmtN(nObs) + "</td>";
      tr.innerHTML = html;
      tbody.appendChild(tr);
      shown++;
    });
  });
  el("monthlyEmpty").hidden = shown > 0;
  if (!payload) {
    el("monthlyEmpty").textContent = "No monthly data file for variable “" + v.code + "” (data/" +
      (kind === "station" ? "monthly_station" : "monthly_group") + "/" + v.code + ".json).";
  } else if (!entities.length) {
    el("monthlyEmpty").textContent = "No station is selected — the current scope offers no stations.";
  } else {
    el("monthlyEmpty").textContent = "No monthly data for this selection.";
  }
}

/* ---------- Daily table ---------- */

function dailyEntityName() {
  var level = currentLevel();
  if (level === "pjm") return "PJM";
  if (level === "subregion") {
    var g = currentGroupSelection();
    return g === "ALL" ? "PJM" : g;
  }
  return null; // daily payloads exist only for PJM + subregions
}

function buildDailyRows(payload, entityName) {
  var v = currentVariable();
  var rows = [];
  if (!payload || !entityName) return rows;
  var entry = payload.groups ? payload.groups[entityName] : null;
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
  el("dailyNote").hidden = showDaily;
  if (!showDaily) return;
  var v = currentVariable();
  var entityName = dailyEntityName();
  state.dailyRows = buildDailyRows(payload, entityName);
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
  el("dailyCaption").textContent = "Group: " + entityName +
    (level === "subregion" && currentGroupSelection() === "ALL" ? " (all subregions — daily is published for PJM as a whole)" : "") +
    " · Daily mean / min / max" + (v.sum_ok ? " / sum" : "") + " per day within the selected month range." +
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
  L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
    maxZoom: 12,
    attribution: 'Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, and the GIS user community'
  }).addTo(map);
  L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}", {
    maxZoom: 12
  }).addTo(map);
  L.rectangle([[BBOX.latMin, BBOX.lonMin], [BBOX.latMax, BBOX.lonMax]], {
    color: "#4da3ff", weight: 1, fill: false, dashArray: "4 4"
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

/* Per-station values for EVERY selected statistic over the selected range,
 * restricted to the stations the current cascade puts on the map. */
function computeStationStats(payload) {
  var v = currentVariable();
  var stats = selectedStats();
  var range = monthRange();
  var out = [];
  if (!payload || !payload.stations || !state.meta || !state.meta.stations) return out;
  var months = payload.months || [];
  var stations = mapStationFilter();
  stations.forEach(function (s) {
    var entry = payload.stations[s.id];
    if (!entry) return;
    var byStat = {};
    var anyN = 0;
    stats.forEach(function (stat) {
      var r = stationRangeValue(entry, months, range, stat, v.code);
      byStat[stat] = r;
      if (r.n > anyN) anyN = r.n;
    });
    out.push({ station: s, byStat: byStat, n: anyN });
  });
  return out;
}

function stationTooltipHtml(d, v, stats) {
  var lines = ["<strong>" + esc(d.station.name) + "</strong> (" + esc(d.station.id) + ")<br>" +
    "State: " + esc(d.station.state) + " · Subregion: " + esc(d.station.subregion) + "<br>"];
  stats.forEach(function (stat) {
    var r = d.byStat[stat];
    lines.push(esc(STAT_LABELS[stat]) + ": <strong>" + fmt(r ? r.value : null, v.code) +
      (v.unit ? " " + esc(v.unit) : "") + "</strong>" +
      (stat === "median" ? " (approximate (rolled))" : "") + "<br>");
  });
  lines.push("n obs in range: " + fmtN(d.n));
  return lines.join("");
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
  var stats = selectedStats();
  var mapStat = state.mapStat;
  if (stats.indexOf(mapStat) < 0) mapStat = stats[0];
  var range = monthRange();
  var values = computeStationStats(payload);
  function mapValue(d) {
    var r = d.byStat[mapStat];
    return r ? r.value : null;
  }
  var valid = values.filter(function (d) {
    var val = mapValue(d);
    return val !== null && val !== undefined && !isNaN(val);
  });

  el("mapTitle").textContent = "Station map — " + v.label + ", coloured by " + STAT_LABELS[mapStat];
  el("mapCaption").textContent =
    "Map is coloured by " + STAT_LABELS[mapStat] +
    (mapStat === stats[0] ? " (the first selected statistic)" : " (swapped via the map statistic control above; the table is unaffected)") +
    ". Hover a station to see all " + stats.length + " selected statistics for it. " +
    "Each station's values are computed in the browser from its monthly values over " +
    (range.start || "…") + " to " + (range.end || "…") + ": mean/median are n-weighted combinations of monthly values" +
    (stats.indexOf("median") >= 0 ? " (median: approximate (rolled))" : "") +
    ", min is the min of monthly mins, max is the max of monthly max values, range is max − min, sum is the sum of monthly sums." +
    " Stations shown: " + values.length + " (scoped by the current level/group/scope selection)." +
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

  var vMin = Math.min.apply(null, valid.map(mapValue));
  var vMax = Math.max.apply(null, valid.map(mapValue));
  var stops = scaleFor(v.code);
  var span = (vMax - vMin) || 1;

  var showMarkers = el("layerMarkers").checked;
  var showHeat = el("layerHeat").checked;

  if (showHeat) {
    var points = valid.map(function (d) { return { station: d.station, value: mapValue(d) }; });
    var url = buildHeatmapImage(points, stops, vMin, vMax);
    heatLayer = L.imageOverlay(url, [[BBOX.latMin, BBOX.lonMin], [BBOX.latMax, BBOX.lonMax]], { opacity: 0.75, interactive: false });
    heatLayer.addTo(map);
  }
  if (showMarkers) {
    var selectedId = currentStationId();
    valid.forEach(function (d) {
      var val = mapValue(d);
      var c = scaleColor(stops, (val - vMin) / span);
      var isSelected = currentLevel() === "station" && d.station.id === selectedId;
      var marker = L.circleMarker([d.station.lat, d.station.lon], {
        radius: isSelected ? 11 : 8,
        color: isSelected ? "#ffffff" : "#e6ebf2", weight: isSelected ? 3 : 1,
        fillColor: rgbCss(c), fillOpacity: 0.9
      });
      var html = stationTooltipHtml(d, v, stats);
      marker.bindTooltip(html, { direction: "top", offset: [0, -6] });
      marker.bindPopup(html);
      marker.addTo(markerLayer);
      if (isSelected && marker.bringToFront) marker.bringToFront();
    });
    // Stations in scope with no valid value for the colour statistic: grey.
    values.forEach(function (d) {
      var val = mapValue(d);
      if (val !== null && val !== undefined && !isNaN(val)) return;
      var marker = L.circleMarker([d.station.lat, d.station.lon], {
        radius: 5, color: "#5d6d87", weight: 1, fillColor: "#39445c", fillOpacity: 0.7
      });
      var html = stationTooltipHtml(d, v, stats);
      marker.bindTooltip(html, { direction: "top", offset: [0, -6] });
      marker.bindPopup(html);
      marker.addTo(markerLayer);
    });
  }

  if (legend) {
    legend.innerHTML =
      "<strong>" + esc(v.label) + "</strong><br>" + esc(STAT_LABELS[mapStat]) +
      (mapStat === "median" ? " — approximate (rolled)" : "") +
      '<div class="gradient" style="background:' + gradientCss(stops) + '"></div>' +
      '<div class="ends"><span>' + fmt(vMin, v.code) + "</span><span>" + fmt(vMax, v.code) + "</span></div>" +
      "<div>" + esc(v.unit || "") + " · " + valid.length + " stations</div>";
  }
  setTimeout(function () { if (map) map.invalidateSize(); }, 50);
}

function renderMapFromCache() {
  var code = currentVariable().code;
  loadPayload("station", code).then(function (p) {
    if (currentVariable().code !== code) return;
    renderMap(p);
  });
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
  pruneUnavailableStats();
  updateStatUI();
  updateNotes();
  updateCascadeHint();
  var code = currentVariable().code;
  var level = currentLevel();
  state.dailyPage = 0;
  var token = ++state.refreshToken;

  var needDaily = (level === "pjm" || level === "subregion") && state.view !== "map";
  var monthlyKind = level === "station" ? "station" : "group";
  var jobs = [];
  jobs.push(loadPayload(monthlyKind, code));
  jobs.push(loadPayload("station", code)); // map always uses monthly_station
  if (needDaily) jobs.push(loadPayload("daily", code));

  Promise.all(jobs).then(function (results) {
    // Guard against stale responses after a fast selection change.
    if (token !== state.refreshToken || currentVariable().code !== code) return;
    var monthlyPayload = results[0];
    var stationPayload = results[1];
    var dailyPayload = needDaily ? results[2] : null;

    var missing = [];
    if (!monthlyPayload) missing.push("monthly " + (monthlyKind === "station" ? "station" : "group") + " data");
    if (!stationPayload && monthlyKind !== "station") missing.push("monthly station data (map)");
    showError(missing.length ? "Could not load " + missing.join(" and ") + " for variable “" + code + "”. Other views may still work." : null);

    renderMonthlyTable(monthlyPayload, monthlyKind);
    if (needDaily) renderDailyTable(dailyPayload);
    else {
      el("dailyBlock").style.display = "none";
      el("dailyNote").hidden = (level === "pjm" || level === "subregion");
    }
    renderMap(stationPayload);
  });
}

/* ---------- Init ---------- */

function bindEvents() {
  el("varSelect").addEventListener("change", function () {
    pruneUnavailableStats();
    updateStatUI();
    refresh();
  });
  el("statList").addEventListener("change", function (ev) {
    if (ev.target && ev.target.matches("input[type=checkbox][data-stat]")) {
      onStatCheckboxChange(ev.target);
    }
  });
  el("levelSelect").addEventListener("change", function () {
    populateCascade();
    refresh();
  });
  el("groupSelect").addEventListener("change", refresh);
  el("scopeSelect").addEventListener("change", function () {
    populateStationsScoped();
    refresh();
  });
  el("stationSelect").addEventListener("change", refresh);
  el("startMonth").addEventListener("change", refresh);
  el("endMonth").addEventListener("change", refresh);
  el("mapStatSelect").addEventListener("change", function () {
    state.mapStat = el("mapStatSelect").value;
    renderMapFromCache();
  });
  el("layerMarkers").addEventListener("change", renderMapFromCache);
  el("layerHeat").addEventListener("change", renderMapFromCache);
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
    updateStatUI();
    refresh();
  });
}

document.addEventListener("DOMContentLoaded", init);
