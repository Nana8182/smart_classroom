let todayChart = null;
let trendChart = null;

function setStatusPill(elementId, status) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = status;
  const pill = el.closest(".status-pill");
  if (!pill) return;
  pill.classList.toggle("online",  status === "ONLINE");
  pill.classList.toggle("offline", status !== "ONLINE");
}

function renderStudentGrid(perStudent) {
  const grid = document.getElementById("student-grid");
  grid.innerHTML = "";

  const entries = Object.entries(perStudent || {});
  if (entries.length === 0) {
    grid.innerHTML = "<p style='color:var(--muted);font-size:14px'>No data for this date.</p>";
    return;
  }

  entries.forEach(([name, info]) => {
    const tile    = document.createElement("div");
    tile.className = "student-tile";
    const filename = info.snapshot_filename;

    const imgEl = filename
      ? `<img src="/proxy_snapshot/${filename}" alt="${name}" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'no-photo'}))">`
      : `<div class="no-photo"></div>`;

    tile.innerHTML = `
      ${imgEl}
      <div class="name">${name}</div>
      <div class="time">${info.first_seen || ""}</div>`;
    grid.appendChild(tile);
  });
}

function renderHistoryTable(records) {
  const tbody = document.querySelector("#history-table tbody");
  tbody.innerHTML = "";
  (records || []).slice().reverse().forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.student}</td><td>${r.timestamp}</td><td>${r.status}</td>`;
    tbody.appendChild(tr);
  });
}

function renderTodayChart(perStudent) {
  const labels = Object.keys(perStudent || {});
  const values = labels.map(() => 1);

  if (todayChart) todayChart.destroy();
  todayChart = new Chart(
    document.getElementById("todayChart"),
    {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Present",
          data: values,
          backgroundColor: "#2563eb",
          borderRadius: 5,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 }, max: 2 },
        },
      },
    }
  );
}

function renderTrendChart(dailyCounts) {
  const labels = Object.keys(dailyCounts || {}).sort();
  const values = labels.map(d => dailyCounts[d]);

  if (trendChart) trendChart.destroy();
  trendChart = new Chart(
    document.getElementById("trendChart"),
    {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Events",
          data: values,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37,99,235,0.1)",
          fill: true,
          tension: 0.35,
          pointRadius: 4,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
      },
    }
  );
}

async function loadAnalytics() {
  const dateVal = document.getElementById("date-picker").value;
  const url     = dateVal ? `/analytics_data?date=${dateVal}` : "/analytics_data";

  try {
    const res  = await fetch(url);
    const data = await res.json();

    setStatusPill("cloud-status", data.cloud_status);

    document.getElementById("present-today").textContent =
      data.students_present_today ?? "—";
    document.getElementById("total-all-time").textContent =
      data.total_records_all_time ?? "—";

    renderStudentGrid(data.per_student);
    renderTodayChart(data.per_student);
    renderTrendChart(data.daily_counts);
    renderHistoryTable(data.attendance_history);

  } catch (err) {
    console.error("Analytics fetch error:", err);
  }
}

// Set date picker default to today
document.getElementById("date-picker").value =
  new Date().toISOString().split("T")[0];

document.getElementById("load-btn").addEventListener("click", loadAnalytics);

loadAnalytics();