const $ = s => document.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = iso => new Date(iso).toLocaleDateString(undefined, {year:"numeric", month:"short", day:"numeric"});
const COL = {plastic:"#0ea5e9", paper:"#f59e0b", metal:"#64748b", glass:"#14b8a6", organic:"#16a34a"};
const badge = s => `<span class="badge-s s-${esc(s)}">${esc(s)}</span>`;
let csrf = null;

function toast(msg, ok = true) {
  const el = document.createElement("div");
  el.className = `toast align-items-center text-bg-${ok ? "success" : "danger"} border-0`;
  el.innerHTML = `<div class="d-flex"><div class="toast-body">${esc(msg)}</div><button class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`;
  $("#toasts").append(el); new bootstrap.Toast(el, {delay: 3500}).show();
}

async function api(url, {method = "GET", body} = {}) {
  const opt = {method, headers: {}, credentials: "same-origin"};
  if (method !== "GET") {
    if (!csrf) csrf = (await (await fetch("/api/auth/csrf")).json()).token;
    opt.headers["X-CSRF-Token"] = csrf;
  }
  if (body instanceof FormData) opt.body = body;
  else if (body) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
  let res, data = {};
  try { res = await fetch(url, opt); data = await res.json(); }
  catch { return {ok: false, status: 0, data: {error: "Network or server error"}}; }
  if (res.status === 401 && !location.pathname.match(/login|register/)) location.href = "/login";
  return {ok: res.ok, status: res.status, data};
}

function showFieldErrors(form, fields) {
  form.querySelectorAll(".is-invalid").forEach(e => e.classList.remove("is-invalid"));
  for (const [k, m] of Object.entries(fields || {})) {
    const i = form.elements[k]; if (!i) continue;
    i.classList.add("is-invalid"); const fb = i.parentElement.querySelector(".invalid-feedback"); if (fb) fb.textContent = m;
  }
}
const showErr = (m) => { const e = $("#err"); e.textContent = m; e.classList.remove("d-none"); };
const form = () => Object.fromEntries(new FormData($("#f")));

function drawChart(id, type, labels, data, colors, label = "") {
  const ds = {data, backgroundColor: colors, borderRadius: type === "bar" ? 8 : 0, label, borderColor: type === "line" ? colors : undefined, tension: .35};
  return new Chart($(id), {type, data: {labels, datasets: [ds]},
    options: {plugins: {legend: {display: type === "doughnut", position: "bottom"}}, scales: type === "doughnut" ? {} : {y: {beginAtZero: true, ticks: {precision: 0}}}}});
}

const pages = {
  async login() {
    $("#f").addEventListener("submit", async e => {
      e.preventDefault(); const f = e.target;
      if (!f.checkValidity()) { f.classList.add("was-validated"); return; }
      const {ok, data} = await api("/api/auth/login", {method: "POST", body: form()});
      if (!ok) return showErr(data.error);
      location.href = data.user.role === "admin" ? "/admin" : "/dashboard";
    });
  },
  async register() {
    $("#f").addEventListener("submit", async e => {
      e.preventDefault(); const f = e.target; const d = form();
      if (d.password !== d.confirm_password) { showFieldErrors(f, {confirm_password: "Passwords do not match"}); return; }
      const {ok, data} = await api("/api/auth/register", {method: "POST", body: d});
      if (!ok) { showFieldErrors(f, data.fields); return showErr(data.error); }
      const r = await api("/api/auth/login", {method: "POST", body: {email: d.email, password: d.password}});
      location.href = r.ok ? "/dashboard" : "/login";
    });
  },
  async dashboard() {
    const [s, h] = await Promise.all([api("/api/stats/user"), api("/api/classify/history")]);
    if (s.ok) {
      $("#s-total").textContent = s.data.total;
      for (const c of Object.keys(COL)) $("#s-" + c).textContent = s.data.by_category[c];
      drawChart("#c-cat", "doughnut", Object.keys(COL), Object.keys(COL).map(c => s.data.by_category[c]), Object.values(COL));
      drawChart("#c-mon", "bar", s.data.monthly.map(m => m.month), s.data.monthly.map(m => m.count), "#16a34a", "Classifications");
    }
    $("#recent").innerHTML = (h.data.items || []).slice(0, 8).map(c =>
      `<tr><td><img class="thumb" src="${esc(c.image_url)}" alt=""></td><td class="text-capitalize">${esc(c.category)}</td><td>${esc(c.confidence)}%</td><td>${fmt(c.created_at)}</td></tr>`
    ).join("") || `<tr><td colspan="4" class="text-muted">No classifications yet.</td></tr>`;
  },
  async classify() {
    const file = $("#file"), go = $("#go");
    file.addEventListener("change", () => {
      const f = file.files[0]; go.disabled = true; if (!f) return;
      if (!["image/jpeg", "image/png"].includes(f.type)) return toast("Please choose a JPG or PNG image", false);
      if (f.size > 5 * 1024 * 1024) return toast("Image must be 5 MB or smaller", false);
      $("#prev").src = URL.createObjectURL(f); $("#prev").classList.remove("d-none"); $("#ph").classList.add("d-none"); go.disabled = false;
    });
    go.addEventListener("click", async () => {
      const fd = new FormData(); fd.append("image", file.files[0]);
      go.disabled = true; go.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Analysing…`;
      const {ok, data} = await api("/api/classify", {method: "POST", body: fd});
      go.disabled = false; go.innerHTML = `<i class="bi bi-stars"></i> Classify Waste`;
      if (!ok) { $("#res").innerHTML = `<div class="alert alert-danger mb-0">${esc(data.error)}</div>`; return; }
      const r = data.result;
      $("#res").innerHTML = `<span class="text-muted small">Predicted category</span><h2 class="text-capitalize fw-bold" style="color:${COL[r.category]}">${esc(r.category)}</h2>
        <div class="small mb-1">Confidence: <b>${esc(r.confidence)}%</b></div><div class="progress mb-3"><div class="progress-bar bg-success" style="width:${Number(r.confidence)}%"></div></div>
        <h6><i class="bi bi-trash3"></i> Disposal &amp; recycling</h6><p class="mb-0">${esc(r.recommendation)}</p>
        ${r.confidence < 60 ? '<div class="alert alert-warning mt-3 mb-0 small">Low confidence. Try a clearer photo of a single item.</div>' : ""}`;
    });
  },
  async collect() {
    const f = $("#f"); f.elements.pickup_date.min = new Date().toISOString().slice(0, 10);
    const load = async () => {
      const {data} = await api("/api/collections");
      $("#list").innerHTML = (data.items || []).slice(0, 5).map(r => `<div class="d-flex justify-content-between align-items-center border-bottom py-2">
        <div><b class="text-capitalize">${esc(r.category)}</b> · ${esc(r.quantity)} kg<div class="small text-muted">Pickup ${fmt(r.pickup_date)}</div></div>${badge(r.status)}</div>`).join("") || `<p class="text-muted mt-3">No requests yet.</p>`;
    };
    f.addEventListener("submit", async e => {
      e.preventDefault(); $("#err").classList.add("d-none");
      const {ok, data} = await api("/api/collections", {method: "POST", body: form()});
      if (!ok) { showFieldErrors(f, data.fields); return showErr(data.error); }
      showFieldErrors(f, {}); f.reset(); toast("Collection request submitted"); load();
    });
    load();
  },
  async history() {
    const load = async () => {
      const {data} = await api("/api/collections");
      $("#rows").innerHTML = (data.items || []).map(r => `<tr><td>${r.id}</td><td>${fmt(r.created_at)}</td><td>${fmt(r.pickup_date)}</td>
        <td class="text-capitalize">${esc(r.category)}</td><td>${esc(r.quantity)} kg</td><td>${badge(r.status)}</td>
        <td class="text-nowrap"><button class="btn btn-sm btn-ghost py-0" data-tl="${r.id}">Timeline</button>
        ${r.status === "pending" ? `<button class="btn btn-sm btn-outline-danger py-0" data-cx="${r.id}">Cancel</button>` : ""}</td></tr>`).join("")
        || `<tr><td colspan="7" class="text-muted">No requests yet.</td></tr>`;
    };
    $("#rows").addEventListener("click", async e => {
      const t = e.target.closest("[data-tl]"), c = e.target.closest("[data-cx]");
      if (t) {
        const {data} = await api(`/api/collections/${t.dataset.tl}/history`);
        $("#tlb").innerHTML = data.items.map(h => `<div class="d-flex justify-content-between py-1">${badge(h.status)}<span class="text-muted small">${new Date(h.updated_at).toLocaleString()}</span></div>`).join("");
        new bootstrap.Modal("#tl").show();
      }
      if (c && confirm("Cancel this request?")) {
        const r = await api(`/api/collections/${c.dataset.cx}/cancel`, {method: "POST"});
        r.ok ? toast("Request cancelled") : toast(r.data.error, false); load();
      }
    });
    load();
  },
  async admin() {
    const NEXT = {pending: ["approved", "cancelled"], approved: ["completed", "cancelled"]};
    const st = await api("/api/stats/admin"), d = st.data;
    for (const k of ["users", "classifications", "requests", "pending", "completed"]) $("#a-" + k).textContent = d[k];
    drawChart("#c-cat", "doughnut", Object.keys(COL), Object.keys(COL).map(c => d.by_category[c]), Object.values(COL));
    const S = {pending: "#f59e0b", approved: "#3b82f6", completed: "#16a34a", cancelled: "#ef4444"};
    drawChart("#c-st", "doughnut", Object.keys(S), Object.keys(S).map(k => d.by_status[k] || 0), Object.values(S));
    const months = [...new Set([...d.monthly_classifications, ...d.monthly_requests].map(m => m.month))].sort();
    const val = (arr, m) => (arr.find(x => x.month === m) || {count: 0}).count;
    new Chart($("#c-mon"), {type: "line", data: {labels: months, datasets: [
      {label: "Classifications", data: months.map(m => val(d.monthly_classifications, m)), borderColor: "#16a34a", tension: .35},
      {label: "Requests", data: months.map(m => val(d.monthly_requests, m)), borderColor: "#14532d", tension: .35}]},
      options: {plugins: {legend: {position: "bottom"}}, scales: {y: {beginAtZero: true, ticks: {precision: 0}}}}});
    const loadReq = async () => {
      const {data} = await api("/api/admin/requests" + ($("#flt").value ? "?status=" + $("#flt").value : ""));
      $("#reqs").innerHTML = (data.items || []).map(r => `<tr><td>${r.id}</td><td>${esc(r.user)}<div class="small text-muted">${esc(r.email)}</div></td>
        <td class="text-capitalize">${esc(r.category)}</td><td>${esc(r.quantity)} kg</td><td>${fmt(r.pickup_date)}</td><td>${badge(r.status)}</td>
        <td class="text-nowrap">${(NEXT[r.status] || []).map(n => `<button class="btn btn-sm ${n === "cancelled" ? "btn-outline-danger" : "btn-eco"} py-0" data-id="${r.id}" data-s="${n}">${n === "cancelled" ? "Cancel" : n === "approved" ? "Approve" : "Complete"}</button>`).join(" ")}</td></tr>`).join("")
        || `<tr><td colspan="7" class="text-muted">No requests.</td></tr>`;
    };
    const loadUsers = async () => {
      const {data} = await api("/api/admin/users");
      $("#users").innerHTML = data.items.map(u => `<tr><td>${esc(u.full_name)}</td><td>${esc(u.email)}</td><td>${esc(u.phone)}</td><td>${esc(u.role)}</td>
        <td class="text-nowrap"><button class="btn btn-sm btn-ghost py-0" data-role="${u.id}" data-to="${u.role === "admin" ? "user" : "admin"}">Make ${u.role === "admin" ? "user" : "admin"}</button>
        <button class="btn btn-sm btn-outline-danger py-0" data-del="${u.id}">Delete</button></td></tr>`).join("");
    };
    $("#flt").addEventListener("change", loadReq);
    $("#reqs").addEventListener("click", async e => {
      const b = e.target.closest("[data-id]"); if (!b) return;
      const r = await api(`/api/admin/requests/${b.dataset.id}`, {method: "PATCH", body: {status: b.dataset.s}});
      r.ok ? toast("Status updated") : toast(r.data.error, false); loadReq();
    });
    $("#users").addEventListener("click", async e => {
      const r = e.target.closest("[data-role]"), x = e.target.closest("[data-del]"); let res;
      if (r) res = await api(`/api/admin/users/${r.dataset.role}`, {method: "PATCH", body: {role: r.dataset.to}});
      else if (x && confirm("Delete this user and all their data?")) res = await api(`/api/admin/users/${x.dataset.del}`, {method: "DELETE"});
      if (res) { res.ok ? toast("Done") : toast(res.data.error, false); loadUsers(); }
    });
    loadReq(); loadUsers();
  },
};

document.addEventListener("DOMContentLoaded", () => {
  const lo = $("#logout");
  if (lo) lo.addEventListener("click", async () => { await api("/api/auth/logout", {method: "POST"}); location.href = "/login"; });
  const p = pages[document.body.dataset.page]; if (p) p();
});
