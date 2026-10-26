"use strict";

const api = {
  async request(path, options = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const body = res.status === 204 ? null : await res.json();
    if (!res.ok) {
      const detail = body && body.detail ? body.detail : `Request failed (${res.status})`;
      const msg = Array.isArray(detail)
        ? detail.map((d) => d.msg).join("; ")
        : detail;
      throw new Error(msg);
    }
    return body;
  },
  get: (path) => api.request(path),
  post: (path, data) =>
    api.request(path, { method: "POST", body: JSON.stringify(data) }),
  put: (path, data) =>
    api.request(path, { method: "PUT", body: JSON.stringify(data) }),
  del: (path) => api.request(path, { method: "DELETE" }),
};

function showMessage(text, isError = false) {
  const el = document.getElementById("message");
  el.textContent = text;
  el.classList.toggle("error", isError);
  el.hidden = false;
  clearTimeout(showMessage.timer);
  showMessage.timer = setTimeout(() => (el.hidden = true), 5000);
}

async function refreshSelectors() {
  const [doctors, patients] = await Promise.all([
    api.get("/api/doctors"),
    api.get("/api/patients"),
  ]);
  for (const select of document.querySelectorAll('select[name="doctor_id"]')) {
    select.innerHTML = doctors
      .map((d) => `<option value="${d.id}">${escapeHtml(d.name)} — ${escapeHtml(d.specialization)}</option>`)
      .join("");
  }
  for (const select of document.querySelectorAll('select[name="patient_id"]')) {
    select.innerHTML = patients
      .map((p) => `<option value="${p.id}">${escapeHtml(p.name)}</option>`)
      .join("");
  }
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

async function refreshAppointments() {
  const params = new URLSearchParams();
  const day = document.getElementById("filter-day").value;
  const status = document.getElementById("filter-status").value;
  if (day) params.set("day", day);
  if (status) params.set("status", status);
  const appointments = await api.get(`/api/appointments?${params}`);
  const tbody = document.getElementById("appointments-body");
  tbody.innerHTML = appointments
    .map(
      (a) => `<tr>
        <td>${a.id}</td>
        <td>${a.doctor_id}</td>
        <td>${a.patient_id}</td>
        <td>${new Date(a.start).toLocaleString()}</td>
        <td>${new Date(a.end).toLocaleString()}</td>
        <td class="status-${a.status}">${a.status}</td>
        <td class="row-actions">
          ${a.status === "booked" ? `
            <button data-action="reschedule" data-id="${a.id}">Reschedule</button>
            <button data-action="cancel" data-id="${a.id}">Cancel</button>` : ""}
        </td>
      </tr>`
    )
    .join("");
}

function bindForm(id, build, onSuccess) {
  document.getElementById(id).addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    if (!form.reportValidity()) return;
    try {
      await build(new FormData(form));
      form.reset();
      showMessage("Saved.");
      await Promise.all([refreshSelectors(), refreshAppointments()]);
      if (onSuccess) onSuccess();
    } catch (err) {
      showMessage(err.message, true);
    }
  });
}

bindForm("doctor-form", (fd) =>
  api.post("/api/doctors", { name: fd.get("name"), specialization: fd.get("specialization") }));

bindForm("patient-form", (fd) =>
  api.post("/api/patients", {
    name: fd.get("name"), email: fd.get("email"), phone: fd.get("phone"),
  }));

bindForm("availability-form", (fd) =>
  api.post("/api/availability", {
    doctor_id: Number(fd.get("doctor_id")),
    weekday: Number(fd.get("weekday")),
    start_time: fd.get("start_time"),
    end_time: fd.get("end_time"),
  }));

bindForm("appointment-form", (fd) =>
  api.post("/api/appointments", {
    doctor_id: Number(fd.get("doctor_id")),
    patient_id: Number(fd.get("patient_id")),
    start: fd.get("start"),
    end: fd.get("end"),
  }));

document.getElementById("apply-filters").addEventListener("click", refreshAppointments);
document.getElementById("clear-filters").addEventListener("click", () => {
  document.getElementById("filter-day").value = "";
  document.getElementById("filter-status").value = "";
  refreshAppointments();
});

document.getElementById("appointments-body").addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  const id = btn.dataset.id;
  try {
    if (btn.dataset.action === "cancel") {
      await api.del(`/api/appointments/${id}`);
      showMessage("Appointment cancelled.");
    } else if (btn.dataset.action === "reschedule") {
      const start = prompt("New start (YYYY-MM-DDTHH:MM):");
      if (!start) return;
      const end = prompt("New end (YYYY-MM-DDTHH:MM):");
      if (!end) return;
      await api.put(`/api/appointments/${id}`, { start, end });
      showMessage("Appointment rescheduled.");
    }
    await refreshAppointments();
  } catch (err) {
    showMessage(err.message, true);
  }
});

Promise.all([refreshSelectors(), refreshAppointments()]).catch((err) =>
  showMessage(err.message, true));
