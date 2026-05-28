function setStatusPill(elementId, status) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = status;
  const pill = el.closest(".status-pill");
  if (!pill) return;
  pill.classList.toggle("online",  status === "ONLINE");
  pill.classList.toggle("offline", status !== "ONLINE");
}

function renderPresent(presentStudents) {
  const list = document.getElementById("present-list");
  list.innerHTML = "";

  const entries = Object.entries(presentStudents || {});
  if (entries.length === 0) {
    list.innerHTML = "<li style='color:var(--muted);font-size:14px'>No students present yet.</li>";
    return;
  }

  entries.forEach(([name, info]) => {
    const li       = document.createElement("li");
    const filename = info.snapshot_filename;

    const imgEl = filename
      ? `<img src="/proxy_snapshot/${filename}" alt="${name}" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'no-photo'}))">`
      : `<div class="no-photo"></div>`;

    li.innerHTML = `
      ${imgEl}
      <div class="student-info">
        <div class="name">${name}</div>
        <div class="time">${info.timestamp || ""}</div>
      </div>`;
    list.appendChild(li);
  });
}

function renderAbsent(absentStudents) {
  const list = document.getElementById("absent-list");
  list.innerHTML = "";
  (absentStudents || []).forEach(name => {
    const li = document.createElement("li");
    li.textContent = name;
    list.appendChild(li);
  });
}

async function loadDashboard() {
  try {
    const res  = await fetch("/dashboard_data");
    const data = await res.json();

    setStatusPill("fog-status",   data.fog.fog_status);
    setStatusPill("cloud-status", data.cloud.cloud_status);

    document.getElementById("occupancy").textContent =
      data.fog.occupancy ?? 0;

    renderPresent(data.fog.present_students);
    renderAbsent(data.fog.absent_students);

    const ts = document.getElementById("last-updated");
    if (ts) ts.textContent = "Updated " + new Date().toLocaleTimeString();

  } catch (err) {
    console.error("Dashboard fetch error:", err);
  }
}

loadDashboard();
setInterval(loadDashboard, 5000);