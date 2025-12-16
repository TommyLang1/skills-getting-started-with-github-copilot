document.addEventListener("DOMContentLoaded", () => {
  const activitiesListEl = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageEl = document.getElementById("message");

  function showMessage(text, type = "info") {
    messageEl.textContent = text;
    messageEl.className = `message ${type}`;
    messageEl.classList.remove("hidden");
    setTimeout(() => messageEl.classList.add("hidden"), 5000);
  }

  function clearChildren(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  function createActivityCard(name, data) {
    const card = document.createElement("div");
    card.className = "activity-card";
    card.dataset.activityName = name;

    const title = document.createElement("h4");
    title.textContent = name;

    const desc = document.createElement("p");
    desc.textContent = data.description || "";

    const sched = document.createElement("p");
    sched.innerHTML = `<strong>Schedule:</strong> ${data.schedule || "TBA"}`;

    const count = document.createElement("p");
    const participants = data.participants || [];
    count.innerHTML = `<strong>Participants:</strong> ${participants.length} / ${data.max_participants}`;

    // Participants block
    const participantsBlock = document.createElement("div");
    participantsBlock.className = "participants";

    const participantsTitle = document.createElement("h5");
    participantsTitle.textContent = "Signed-up Students";

    const list = document.createElement("ul");
    list.className = "participants-list";

    if (participants.length === 0) {
      const no = document.createElement("p");
      no.className = "no-participants";
      no.textContent = "No participants yet.";
      participantsBlock.appendChild(participantsTitle);
      participantsBlock.appendChild(no);
    } else {
      participants.forEach((email) => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.className = "participant-email";
        a.href = `mailto:${email}`;
        a.textContent = email;
        li.appendChild(a);
        const del = document.createElement("button");
        del.className = "participant-delete";
        del.type = "button";
        del.dataset.email = email;
        del.title = "Unregister";
        del.textContent = "✕";
        li.appendChild(del);
        list.appendChild(li);
      });
      participantsBlock.appendChild(participantsTitle);
      participantsBlock.appendChild(list);
    }

    card.appendChild(title);
    card.appendChild(desc);
    card.appendChild(sched);
    card.appendChild(count);
    card.appendChild(participantsBlock);

    return card;
  }

  function renderActivities(data) {
    clearChildren(activitiesListEl);
    clearChildren(activitySelect);

    // default option
    const defaultOpt = document.createElement("option");
    defaultOpt.value = "";
    defaultOpt.textContent = "-- Select an activity --";
    activitySelect.appendChild(defaultOpt);

    Object.keys(data).forEach((name) => {
      const card = createActivityCard(name, data[name]);
      activitiesListEl.appendChild(card);

      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      activitySelect.appendChild(opt);
    });
  }

  function findCardByName(name) {
    const cards = document.querySelectorAll(".activity-card");
    for (const c of cards) {
      if (c.dataset.activityName === name) return c;
    }
    return null;
  }

  function updateParticipantsInCard(name, participants, max) {
    const card = findCardByName(name);
    if (!card) return;

    // update count
    const countP = card.querySelector("p:nth-of-type(3)");
    if (countP) countP.innerHTML = `<strong>Participants:</strong> ${participants.length} / ${max}`;

    const participantsBlock = card.querySelector(".participants");
    clearChildren(participantsBlock);

    const participantsTitle = document.createElement("h5");
    participantsTitle.textContent = "Signed-up Students";
    participantsBlock.appendChild(participantsTitle);

    if (!participants || participants.length === 0) {
      const no = document.createElement("p");
      no.className = "no-participants";
      no.textContent = "No participants yet.";
      participantsBlock.appendChild(no);
    } else {
      const list = document.createElement("ul");
      list.className = "participants-list";
      participants.forEach((email) => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.className = "participant-email";
        a.href = `mailto:${email}`;
        a.textContent = email;
        li.appendChild(a);
        const del = document.createElement("button");
        del.className = "participant-delete";
        del.type = "button";
        del.dataset.email = email;
        del.title = "Unregister";
        del.textContent = "✕";
        li.appendChild(del);
        list.appendChild(li);
      });
      participantsBlock.appendChild(list);
    }
  }

  // Fetch and render activities on load
  fetch("/activities")
    .then((res) => {
      if (!res.ok) throw new Error("Failed to load activities");
      return res.json();
    })
    .then((data) => renderActivities(data))
    .catch((err) => {
      clearChildren(activitiesListEl);
      const p = document.createElement("p");
      p.className = "error";
      p.textContent = "Unable to load activities.";
      activitiesListEl.appendChild(p);
      console.error(err);
    });

  // Handle signup form
  signupForm.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const email = document.getElementById("email").value.trim();
    const activity = document.getElementById("activity").value;

    if (!activity) {
      showMessage("Please select an activity.", "error");
      return;
    }
    if (!email) {
      showMessage("Please enter an email address.", "error");
      return;
    }

    const url = `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`;

    fetch(url, { method: "POST" })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Signup failed");
        }
        return res.json();
      })
      .then((json) => {
        showMessage(json.message || "Signed up successfully!", "success");

        // Refresh activities to get updated participant list
        return fetch("/activities")
          .then((r) => r.json())
          .then((data) => {
            const activityData = data[activity];
            if (activityData) updateParticipantsInCard(activity, activityData.participants, activityData.max_participants);
          });
      })
      .catch((err) => {
        showMessage(err.message || "Signup failed", "error");
        console.error(err);
      });
  });

  // Delegate click on delete buttons to unregister participants
  activitiesListEl.addEventListener("click", (ev) => {
    const btn = ev.target.closest && ev.target.closest(".participant-delete");
    if (!btn) return;

    const email = btn.dataset.email;
    const card = btn.closest(".activity-card");
    const activity = card && card.dataset.activityName;
    if (!activity || !email) return;

    if (!confirm(`Unregister ${email} from ${activity}?`)) return;

    fetch(`/activities/${encodeURIComponent(activity)}/participants?email=${encodeURIComponent(email)}`, {
      method: "DELETE",
    })
      .then(async (res) => {
        if (res.ok) {
          const json = await res.json();
          showMessage(json.message || "Unregistered successfully", "success");

          // Refresh the activity participants
          return fetch("/activities").then((r) => r.json()).then((data) => {
            const activityData = data[activity];
            if (activityData) updateParticipantsInCard(activity, activityData.participants, activityData.max_participants);
          });
        } else {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Unregister failed");
        }
      })
      .catch((err) => {
        showMessage(err.message || "Unregister failed", "error");
        console.error(err);
      });
  });
});
