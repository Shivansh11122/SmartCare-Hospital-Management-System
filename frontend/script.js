const $ = id => document.getElementById(id);

// ---------------- API HELPER ----------------

async function api(url, options = {}) {

  const response = await fetch(url, {

    ...options,

    headers: {

      "Content-Type": "application/json",

      ...(options.headers || {})

    }

  });

  const data = await response.json();

  if (!response.ok) {

    throw new Error(data.error || "Request failed");

  }

  return data;

}

function showMessage(text, error = false) {

  showSectionMessage("message", text, error);

}

function showSectionMessage(id, text, error = false) {

  const element = $(id);

  if (!element) return;

  element.textContent = text;

  element.style.color = error ? "#b91c1c" : "#15803d";

}

// ---------------- DASHBOARD ----------------

async function loadDashboard() {

  const data = await api("/api/dashboard");

  $("patientsCount").textContent = data.patients;

  $("doctorsCount").textContent = data.doctors;

  $("wardsCount").textContent = data.wards;

  $("departmentsCount").textContent = data.departments;

  $("appointmentsCount").textContent = data.appointments;

}

async function loadDashboardAppointments() {

  const appointments = await api("/api/appointments");

  const table = $("dashboardAppointmentsTable");

  if (!table) return;

  table.replaceChildren();

  if (appointments.length === 0) {

    const row = table.insertRow();

    const cell = row.insertCell();

    cell.colSpan = 6;

    cell.textContent = "No appointments yet.";

    return;

  }

  appointments.slice(0, 5).forEach(appointment => {

    const row = table.insertRow();

    [

      appointment.appointment_id,

      appointment.patient_name,

      appointment.doctor_name,

      appointment.appointment_date,

      appointment.appointment_time,

      appointment.status

    ].forEach(value => {

      const cell = row.insertCell();

      cell.textContent = value ?? "—";

    });

  });

}

// ---------------- PATIENTS ----------------

async function loadPatients() {

  const patients = await api("/api/patients");

  const table = $("patientsTable");

  table.replaceChildren();

  if (patients.length === 0) {

    const row = table.insertRow();

    const cell = row.insertCell();

    cell.colSpan = 6;

    cell.textContent = "No patients registered yet.";

    return;

  }

  patients.forEach(patient => {

    const row = table.insertRow();

    [

      patient.patient_id,

      patient.name,

      patient.gender,

      patient.phone,

      patient.blood_group

    ].forEach(value => {

      const cell = row.insertCell();

      cell.textContent = value ?? "—";

    });

    const actionCell = row.insertCell();

    const removeButton = document.createElement("button");

    removeButton.textContent = "Remove";

    removeButton.type = "button";

    removeButton.addEventListener("click", async () => {

      const confirmed = confirm(

        `Remove patient ${patient.name}?`

      );

      if (!confirmed) return;

      try {

        const result = await api(

          `/api/patients/${patient.patient_id}`,

          { method: "DELETE" }

        );

        alert(result.message || "Patient removed successfully.");

        await Promise.all([

          loadPatients(),

          loadDashboard(),

          loadAssignmentOptions()

        ]);

      } catch (error) {

        alert(error.message);

      }

    });

    actionCell.appendChild(removeButton);

  });

}

async function refresh() {

  await Promise.all([

    loadDashboard(),

    loadPatients()

  ]);

}

// ---------------- DEPARTMENTS ----------------

async function loadDepartments() {

  const departments = await api("/api/departments");

  const select = $("doctorDepartment");

  select.replaceChildren(new Option("Select department", ""));

  departments.forEach(department => {

    select.add(new Option(

      department.department_name,

      department.department_id

    ));

  });

}

// ---------------- DOCTORS ----------------

async function loadDoctors() {

  const doctors = await api("/api/doctors");

  const table = $("doctorsTable");

  table.replaceChildren();

  if (doctors.length === 0) {

    const row = table.insertRow();

    const cell = row.insertCell();

    cell.colSpan = 8;

    cell.textContent = "No doctors registered yet.";

    return;

  }

  doctors.forEach(doctor => {

    const row = table.insertRow();

    [

      doctor.doctor_id,

      doctor.name,

      doctor.specialization,

      doctor.department_name,

      doctor.phone,

      doctor.email,

      doctor.status || "Active"

    ].forEach(value => {

      const cell = row.insertCell();

      cell.textContent = value ?? "—";

    });

    const actionCell = row.insertCell();

    const actionButton = document.createElement("button");

    actionButton.type = "button";

    if ((doctor.status || "Active") === "Inactive") {

      actionButton.textContent = "Inactive";

      actionButton.disabled = true;

    } else {

      actionButton.textContent = "Deactivate";

      actionButton.addEventListener("click", async () => {

        const confirmed = confirm(

          `Deactivate doctor ${doctor.name}? Their appointment history will be preserved.`

        );

        if (!confirmed) return;

        try {

          const result = await api(

            `/api/doctors/${doctor.doctor_id}/deactivate`,

            { method: "PATCH" }

          );

          alert(result.message || "Doctor deactivated successfully.");

          await Promise.all([

            loadDoctors(),

            loadDashboard()

          ]);

        } catch (error) {

          alert(error.message);

        }

      });

    }

    actionCell.appendChild(actionButton);

  });

}

$("doctorForm").addEventListener("submit", async event => {

  event.preventDefault();

  const form = event.currentTarget;

  const doctor = Object.fromEntries(

    new FormData(form).entries()

  );

  doctor.department_id = Number(doctor.department_id);

  try {

    const result = await api("/api/doctors", {

      method: "POST",

      body: JSON.stringify(doctor)

    });

    showSectionMessage(

      "doctorMessage",

      result.message || "Doctor registered successfully."

    );

    form.reset();

    await Promise.all([

      loadDoctors(),

      loadDashboard()

    ]);

  } catch (error) {

    showSectionMessage(

      "doctorMessage",

      error.message,

      true

    );

  }

});

// ---------------- APPOINTMENTS ----------------

async function loadAppointments() {
  const appointments = await api("/api/appointments");
  const table = $("appointmentsTable");
  table.replaceChildren();
  if (!appointments.length) {
    const row = table.insertRow();
    const cell = row.insertCell();
    cell.colSpan = 8;
    cell.textContent = "No appointments registered yet.";
    return;
  }
  const priorityLabel = value => ({1: "Emergency", 2: "Urgent", 3: "Regular"}[Number(value)] || "—");
  const today = new Date();
  const todayString = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  appointments.forEach(appointment => {
    const row = table.insertRow();
    const patientCell = row.insertCell();
    patientCell.innerHTML = "";
    const patientName = document.createElement("strong");
    patientName.textContent = appointment.patient_name || "Unknown patient";
    const reason = document.createElement("small");
    reason.textContent = appointment.reason ? `Reason: ${appointment.reason}` : "Reason: —";
    reason.style.display = "block";
    patientCell.append(patientName, reason);

    const idCell = row.insertCell();
    idCell.textContent = appointment.appointment_id;
    // Keep the table order aligned with the compact header: ID first, then Patient.
    row.insertBefore(idCell, patientCell);

    const doctorCell = row.insertCell();
    const doctorName = document.createElement("strong");
    doctorName.textContent = appointment.doctor_name || "—";
    const specialization = document.createElement("small");
    specialization.textContent = appointment.specialization || "—";
    specialization.style.display = "block";
    doctorCell.append(doctorName, specialization);

    const appointmentCell = row.insertCell();
    const dateLine = document.createElement("div");
    dateLine.textContent = appointment.appointment_date || "—";
    const timeLine = document.createElement("small");
    timeLine.textContent = appointment.appointment_time ? String(appointment.appointment_time).slice(0, 5) : "—";
    appointmentCell.append(dateLine, timeLine);

    const priorityCell = row.insertCell();
    const requested = document.createElement("div");
    requested.textContent = `Requested: ${priorityLabel(appointment.requested_priority)}`;
    const confirmed = document.createElement("small");
    confirmed.textContent = appointment.arrival_time
    ? `Confirmed: ${priorityLabel(appointment.queue_priority)}`
    : "Not confirmed";
    confirmed.style.display = "block";
    priorityCell.append(requested, confirmed);

    const queueCell = row.insertCell();
    const queueStatus = appointment.queue_status || "Not Arrived";
    const queueLine = document.createElement("strong");
    queueLine.textContent = queueStatus;
    const arrivalLine = document.createElement("small");
    arrivalLine.textContent = appointment.arrival_time ? `Arrived: ${appointment.arrival_time}` : "Not checked in";
    arrivalLine.style.display = "block";
    queueCell.append(queueLine, arrivalLine);

    const statusCell = row.insertCell();
    statusCell.textContent = appointment.status || "—";

    const actionCell = row.insertCell();
    actionCell.className = "appointment-actions";
    const isToday = String(appointment.appointment_date).slice(0, 10) === todayString;
    if (isToday && appointment.status === "Scheduled" && queueStatus === "Not Arrived") {
      const prioritySelect = document.createElement("select");
      [{value: 1, label: "Emergency"}, {value: 2, label: "Urgent"}, {value: 3, label: "Regular"}].forEach(item => {
        const option = document.createElement("option");
        option.value = String(item.value);
        option.textContent = item.label;
        prioritySelect.appendChild(option);
      });
      prioritySelect.value = String(appointment.requested_priority || 3);
      const checkInButton = document.createElement("button");
      checkInButton.type = "button";
      checkInButton.textContent = "Check In";
      checkInButton.addEventListener("click", async () => {
        try {
          const result = await api(`/api/patient-queue/${appointment.appointment_id}/check-in`, {method: "POST", body: JSON.stringify({priority: Number(prioritySelect.value)})});
          alert(result.message || "Patient checked in.");
          await loadAppointments();
        } catch (error) { alert(error.message); }
      });
      actionCell.append(prioritySelect, checkInButton);
    } else if (isToday && appointment.status === "Scheduled" && queueStatus === "Waiting") {
      const startButton = document.createElement("button");
      startButton.type = "button";
      startButton.textContent = "Start Service";
      startButton.addEventListener("click", async () => {
        try {
          const result = await api(`/api/patient-queue/${appointment.appointment_id}/status`, {method: "PATCH", body: JSON.stringify({queue_status: "In Service"})});
          alert(result.message || "Service started.");
          await loadAppointments();
        } catch (error) { alert(error.message); }
      });
      actionCell.appendChild(startButton);
    } else if (isToday && appointment.status === "Scheduled" && queueStatus === "In Service") {
      const completeButton = document.createElement("button");
      completeButton.type = "button";
      completeButton.textContent = "Complete Visit";
      completeButton.addEventListener("click", async () => {
        try {
          const result = await api(`/api/patient-queue/${appointment.appointment_id}/status`, {method: "PATCH", body: JSON.stringify({queue_status: "Completed"})});
          alert(result.message || "Visit completed.");
          await Promise.all([loadAppointments(), loadDashboard()]);
        } catch (error) { alert(error.message); }
      });
      actionCell.appendChild(completeButton);
    }
    const statusSelect = document.createElement("select");
    ["Scheduled", "Completed", "Cancelled"].forEach(status => {
      const option = document.createElement("option");
      option.value = status;
      option.textContent = status;
      statusSelect.appendChild(option);
    });
    statusSelect.value = appointment.status || "Scheduled";
    const updateButton = document.createElement("button");
    updateButton.type = "button";
    updateButton.textContent = "Update Status";
    updateButton.addEventListener("click", async () => {
      try {
        const result = await api(`/api/appointments/${appointment.appointment_id}/status`, {method: "PATCH", body: JSON.stringify({status: statusSelect.value})});
        alert(result.message || "Appointment status updated.");
        await Promise.all([loadAppointments(), loadDashboard()]);
      } catch (error) { alert(error.message); }
    });
    const statusControls = document.createElement("div");
    statusControls.className = "appointment-status-controls";
    statusControls.append(statusSelect, updateButton);
    actionCell.appendChild(statusControls);
  });
}



// ---------------- WARDS ----------------

async function loadWards() {

  const wards = await api("/api/wards");

  const table = $("wardsTable");

  table.replaceChildren();

  let totalCapacity = 0;

  let availableSpaces = 0;

  if (wards.length === 0) {

    const row = table.insertRow();

    const cell = row.insertCell();

    cell.colSpan = 8;

    cell.textContent = "No wards available.";

  }

  wards.forEach(ward => {

    totalCapacity += Number(ward.capacity) || 0;

    availableSpaces += Number(ward.available_capacity) || 0;

    const row = table.insertRow();

    [

      ward.ward_id,

      ward.ward_name,

      ward.ward_type,

      ward.capacity,

      ward.available_capacity,

      ward.floor_no,

      ward.status

    ].forEach(value => {

      const cell = row.insertCell();

      cell.textContent = value ?? "—";

    });

    const actionCell = row.insertCell();

    const removeButton = document.createElement("button");

    removeButton.textContent = "Remove";

    removeButton.type = "button";

    removeButton.addEventListener("click", async () => {

      const confirmed = confirm(

        `Remove ward "${ward.ward_name}"?`

      );

      if (!confirmed) return;

      try {

        const result = await api(

          `/api/wards/${ward.ward_id}`,

          { method: "DELETE" }

        );

        alert(result.message || "Ward removed successfully.");

        await Promise.all([

          loadWards(),

          loadDashboard(),

          loadAssignmentOptions()

        ]);

      } catch (error) {

        alert(error.message);

      }

    });

    actionCell.appendChild(removeButton);

  });

  if ($("totalWards")) {

    $("totalWards").textContent = wards.length;

  }

  if ($("totalCapacity")) {

    $("totalCapacity").textContent = totalCapacity;

  }

  if ($("availableSpaces")) {

    $("availableSpaces").textContent = availableSpaces;

  }

  if ($("wardsPageTotal")) {

    $("wardsPageTotal").textContent = wards.length;

  }

  if ($("wardsPageCapacity")) {

    $("wardsPageCapacity").textContent = totalCapacity;

  }

  if ($("wardsPageAvailable")) {

    $("wardsPageAvailable").textContent = availableSpaces;

  }

}

$("wardForm").addEventListener("submit", async event => {

  event.preventDefault();

  const form = event.currentTarget;

  const ward = Object.fromEntries(new FormData(form).entries());

  ward.capacity = Number(ward.capacity);

  ward.floor_no = ward.floor_no === ""

    ? null

    : Number(ward.floor_no);

  try {

    const result = await api("/api/wards", {

      method: "POST",

      body: JSON.stringify(ward)

    });

    showSectionMessage("wardFormMessage", result.message);

    form.reset();

    await Promise.all([

      loadWards(),

      loadDashboard(),

      loadAssignmentOptions()

    ]);

  } catch (error) {

    showSectionMessage("wardFormMessage", error.message, true);

  }

});

// ---------------- PATIENT-WARD ASSIGNMENT ----------------

async function loadAssignmentOptions() {

  const [patients, wards, assignments] = await Promise.all([

    api("/api/patients"),

    api("/api/wards"),

    api("/api/ward-assignments")

  ]);

  const patientSelect = $("assignmentPatient");

  const wardSelect = $("assignmentWard");

  patientSelect.replaceChildren(new Option("Select patient", ""));

  wardSelect.replaceChildren(new Option("Select ward", ""));

  const assignedPatientIds = new Set(

    assignments.map(item => Number(item.patient_id))

  );

  patients.forEach(patient => {

    if (!assignedPatientIds.has(Number(patient.patient_id))) {

      patientSelect.add(new Option(

        `${patient.name} (ID: ${patient.patient_id})`,

        patient.patient_id

      ));

    }

  });

  wards.forEach(ward => {

    const option = new Option(

      `${ward.ward_name} — ${ward.available_capacity} available`,

      ward.ward_id

    );

    if (Number(ward.available_capacity) <= 0) {

      option.disabled = true;

    }

    wardSelect.add(option);

  });

}

async function loadAssignments() {

  const assignments = await api("/api/ward-assignments");

  const table = $("assignmentsTable");

  table.replaceChildren();

  if (assignments.length === 0) {

    const row = table.insertRow();

    const cell = row.insertCell();

    cell.colSpan = 4;

    cell.textContent = "No patients assigned to wards yet.";

    return;

  }

  assignments.forEach(item => {

    const row = table.insertRow();

    [

      item.patient_id,

      item.patient_name,

      item.ward_name,

      item.ward_type

    ].forEach(value => {

      const cell = row.insertCell();

      cell.textContent = value ?? "—";

    });

  });

}

async function refreshWardAssignmentData() {

  await Promise.all([

    loadWards(),

    loadAssignments(),

    loadDashboard()

  ]);

  await loadAssignmentOptions();

}

$("wardAssignmentForm").addEventListener("submit", async event => {

  event.preventDefault();

  const form = event.currentTarget;

  const assignment = Object.fromEntries(

    new FormData(form).entries()

  );

  assignment.patient_id = Number(assignment.patient_id);

  assignment.ward_id = Number(assignment.ward_id);

  try {

    const result = await api("/api/ward-assignments", {

      method: "POST",

      body: JSON.stringify(assignment)

    });

    showSectionMessage("assignmentMessage", result.message);

    form.reset();

    await refreshWardAssignmentData();

  } catch (error) {

    showSectionMessage(

      "assignmentMessage",

      error.message,

      true

    );

  }

});

// ---------------- SIDEBAR NAVIGATION ----------------

const pageDetails = {

  dashboard: {

    title: "Dashboard",

    subtitle: "Hospital overview and daily activity"

  },

  patients: {

    title: "Patients",

    subtitle: "Register patients and view patient records"

  },

  doctors: {

    title: "Doctors",

    subtitle: "Manage doctor information and departments"

  },

  appointments: {

    title: "Appointments",

    subtitle: "Schedule and view patient appointments"

  },

  wards: {

    title: "Hospital Wards",

    subtitle: "Monitor ward capacity and availability"

  },

  assignments: {

    title: "Ward Assignments",

    subtitle: "Assign patients to wards and review assignments"

  },
  patientQueue: { title: "Patient Queue", subtitle: "Demonstrate FCFS and Priority Scheduling for patients" }
};

function showPage(page) {

  const details = pageDetails[page];

  if (!details) return;

  document.querySelectorAll("[data-section]").forEach(section => {

    section.hidden = section.dataset.section !== page;

  });

  document.querySelectorAll(".nav-link").forEach(button => {

    const active = button.dataset.page === page;

    button.classList.toggle("active", active);

    if (active) {

      button.setAttribute("aria-current", "page");

    } else {

      button.removeAttribute("aria-current");

    }

  });

  $("pageTitle").textContent = details.title;

  $("pageSubtitle").textContent = details.subtitle;

  const refreshFunctions = {

    dashboard: () => Promise.all([

      loadDashboard(),

      loadDashboardAppointments()

    ]),

    patients: loadPatients,

    doctors: () => Promise.all([

      loadDoctors(),

      loadDepartments()

    ]),

    appointments: () => Promise.all([loadAppointments(), loadTodayQueue()]),

    wards: loadWards,

    assignments: refreshWardAssignmentData,

  };

  Promise.resolve()

    .then(() => refreshFunctions[page]())

    .catch(error => {

      console.error(`Could not refresh ${page}:`, error);

    });

}

document.querySelectorAll(".nav-link").forEach(button => {

  button.addEventListener("click", () => {

    showPage(button.dataset.page);

  });

});

// ---------------- INITIAL PAGE LOAD ----------------

async function initializeApp() {

  const results = await Promise.allSettled([

    loadDashboard(),

    loadPatients(),

    loadDepartments(),

    loadDoctors(),

    loadAppointments(),

    loadDashboardAppointments(),

    loadWards(),

    loadAssignments()

  ]);

  const errors = results.filter(result => result.status === "rejected");

  if (errors.length > 0) {

    console.error("Some sections failed to load:", errors);

  }

  try {

    await loadAssignmentOptions();

  } catch (error) {

    showSectionMessage(

      "assignmentMessage",

      "Could not load assignment options: " + error.message,

      true

    );

  }

  showPage("dashboard");

}

const schedulingAlgorithm = $("schedulingAlgorithm");
const refreshQueueBtn = $("refreshQueueBtn");

if (schedulingAlgorithm) {
  schedulingAlgorithm.addEventListener("change", async () => {
    try {
      await loadTodayQueue();
      showSectionMessage(
        "schedulingMessage",
        `Queue sorted using ${schedulingAlgorithm.value.toUpperCase()}.`
      );
    } catch (error) {
      showSectionMessage("schedulingMessage", error.message, true);
    }
  });
}

if (refreshQueueBtn) {
  refreshQueueBtn.addEventListener("click", async () => {
    try {
      await loadTodayQueue();
      showSectionMessage("schedulingMessage", "Patient queue refreshed.");
    } catch (error) {
      showSectionMessage("schedulingMessage", error.message, true);
    }
  });
}

async function loadTodayQueue() {
  const algorithm = $("schedulingAlgorithm")?.value || "fcfs";
  const data = await api(`/api/patient-queue?algorithm=${algorithm}`);
  const appointments = data.appointments || [];
  const table = $("todayQueueTable");
  if (!table) return;
  table.replaceChildren();
  $("queueWaitingCount").textContent = data.stats?.waiting_count ?? 0;
  $("queueInServiceCount").textContent = data.stats?.in_service_count ?? 0;
  $("queueCompletedCount").textContent = data.stats?.completed_count ?? 0;
  $("queueAverageWait").textContent = data.stats?.average_wait_minutes ?? 0;
  if (!appointments.length) {
    const row = table.insertRow();
    const cell = row.insertCell();
    cell.colSpan = 7;
    cell.textContent = "No patients in today's queue.";
    return;
  }
  const priorityLabel = value => ({1: "Emergency", 2: "Urgent", 3: "Regular"}[Number(value)] || "—");
  appointments.forEach(patient => {
    const row = table.insertRow();
    [
      patient.patient_name,
      patient.doctor_name,
      patient.appointment_time,
      priorityLabel(patient.queue_priority),
      patient.arrival_time || "Not arrived",
      patient.queue_status || "Not Arrived",
      patient.waiting_minutes ?? "—"
    ].forEach(value => {
      const cell = row.insertCell();
      cell.textContent = value ?? "—";
    });
  });
}

initializeApp();
