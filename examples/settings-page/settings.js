(() => {
  "use strict";

  const form = document.getElementById("settings-form");
  const savebar = document.getElementById("savebar");
  const savebarStatus = document.getElementById("savebar-status");
  const saveButton = document.getElementById("save-changes");
  const discardButton = document.getElementById("discard-changes");
  const workspaceName = document.getElementById("workspace-name");
  const supportEmail = document.getElementById("support-email");
  const settingsTitle = document.getElementById("settings-title");
  const navLinks = [...document.querySelectorAll(".settings-nav a")];
  const sections = navLinks
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);
  const tokenInput = document.getElementById("api-token");
  const tokenStatus = document.getElementById("token-status");
  const tokenMeta = document.getElementById("token-meta");
  const revealToken = document.getElementById("reveal-token");
  const copyToken = document.getElementById("copy-token");
  const rotateToken = document.getElementById("rotate-token");
  const rotateDialog = document.getElementById("rotate-dialog");
  const rotateConfirm = document.getElementById("rotate-confirm");
  const deleteWorkspace = document.getElementById("delete-workspace");
  const deleteDialog = document.getElementById("delete-dialog");
  const deleteConfirm = document.getElementById("delete-confirm");
  const deleteConfirmButton = document.getElementById("delete-confirm-button");
  const deleteTargetTitle = document.getElementById("delete-target-title");
  const deleteTargetLabel = document.getElementById("delete-target-label");
  const maskedToken = `mrd_live_${"•".repeat(32)}`;

  let actualToken = "mrd_live_7Q4mK2xR9pLv6D1sB8nC3tY5eH8uJ1aF";
  let tokenVisible = false;
  let baseline = null;
  let deleteTarget = "Northstar Labs";
  let navFrame = 0;

  function captureState() {
    const state = {};
    for (const element of form.querySelectorAll("input, select, textarea")) {
      if (!element.id || element.hasAttribute("data-ignore-dirty")) continue;
      if (element.type === "checkbox" || element.type === "radio") {
        state[element.id] = element.checked;
      } else {
        state[element.id] = element.value;
      }
    }
    return state;
  }

  function switchLabels() {
    for (const input of form.querySelectorAll('input[role="switch"]')) {
      const label = input.closest(".switch")?.querySelector(".switch-state");
      if (label) label.textContent = input.checked ? "On" : "Off";
    }
  }

  function restoreState(state) {
    for (const element of form.querySelectorAll("input, select, textarea")) {
      if (!element.id || !(element.id in state)) continue;
      if (element.type === "checkbox" || element.type === "radio") {
        element.checked = Boolean(state[element.id]);
      } else {
        element.value = state[element.id];
      }
    }
    switchLabels();
    updateDeleteState();
  }

  function isDirty() {
    return JSON.stringify(captureState()) !== JSON.stringify(baseline);
  }

  function refreshSavebar() {
    const dirty = isDirty();
    savebar.hidden = !dirty;
    if (dirty) savebarStatus.textContent = "Unsaved changes";
  }

  function validateName() {
    if (!workspaceName.value.trim()) {
      Meridian.setFieldError(workspaceName, "Workspace name is required.");
      return false;
    }
    Meridian.clearFieldError(workspaceName);
    return true;
  }

  function validateSupportEmail() {
    const value = supportEmail.value.trim();
    if (!value) {
      Meridian.setFieldError(supportEmail, "An operations contact is required.");
      return false;
    }
    if (!Meridian.emailValid(value)) {
      Meridian.setFieldError(supportEmail, "Enter an email in the format name@company.com.");
      return false;
    }
    Meridian.clearFieldError(supportEmail);
    return true;
  }

  function updateDisplayedName() {
    const name = workspaceName.value.trim() || "Untitled workspace";
    settingsTitle.textContent = name;
    for (const node of document.querySelectorAll(".workspace-card-name")) {
      node.textContent = name;
    }
    deleteTarget = name;
    deleteTargetTitle.textContent = name;
    deleteTargetLabel.textContent = name;
    updateDeleteState();
  }

  function updateTokenDisplay() {
    tokenInput.value = tokenVisible ? actualToken : maskedToken;
    revealToken.setAttribute("aria-pressed", String(tokenVisible));
    revealToken.textContent = tokenVisible ? "Hide" : "Reveal";
  }

  function updateDeleteState() {
    const matches = deleteConfirm.value.trim() === deleteTarget;
    deleteConfirmButton.disabled = !matches;
    deleteConfirm.removeAttribute("aria-invalid");
    const error = document.getElementById("delete-confirm-error");
    if (error) {
      error.textContent = "";
      error.hidden = true;
    }
  }

  function generateToken() {
    const bytes = new Uint8Array(20);
    if (window.crypto?.getRandomValues) {
      window.crypto.getRandomValues(bytes);
    } else {
      for (let index = 0; index < bytes.length; index += 1) {
        bytes[index] = Math.floor(Math.random() * 256);
      }
    }
    return `mrd_live_${[...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join("")}`;
  }

  function setActiveNav(id) {
    for (const link of navLinks) {
      const active = link.getAttribute("href") === `#${id}`;
      link.classList.toggle("is-active", active);
      if (active) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    }
  }

  function syncNav() {
    navFrame = 0;
    let current = sections[0]?.id;
    for (const section of sections) {
      if (section.getBoundingClientRect().top <= 110) current = section.id;
    }
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) {
      current = sections.at(-1)?.id;
    }
    if (current) setActiveNav(current);
  }

  form.addEventListener("input", (event) => {
    if (event.target === workspaceName) Meridian.clearFieldError(workspaceName);
    if (event.target === supportEmail) Meridian.clearFieldError(supportEmail);
    refreshSavebar();
  });

  form.addEventListener("change", () => {
    switchLabels();
    refreshSavebar();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (savebar.hidden) return;
    const nameOk = validateName();
    const emailOk = validateSupportEmail();
    if (!nameOk || !emailOk) {
      savebarStatus.textContent = "Check the highlighted fields before saving.";
      (nameOk ? supportEmail : workspaceName).focus();
      return;
    }

    savebarStatus.textContent = "Saving changes…";
    Meridian.setBusy(saveButton, true, "Saving…");
    form.setAttribute("aria-busy", "true");
    await Meridian.wait(700);
    baseline = captureState();
    form.removeAttribute("aria-busy");
    Meridian.setBusy(saveButton, false);
    updateDisplayedName();
    savebar.hidden = true;
    Meridian.toast("Workspace settings saved");
    Meridian.announce("Workspace settings saved. No changes were sent to a server.");
    workspaceName.focus({ preventScroll: true });
    refreshSavebar();
  });

  discardButton.addEventListener("click", () => {
    restoreState(baseline);
    for (const field of [workspaceName, supportEmail]) {
      Meridian.clearFieldError(field);
    }
    refreshSavebar();
    Meridian.toast("Changes discarded");
    Meridian.announce("Unsaved changes discarded.");
    workspaceName.focus({ preventScroll: true });
  });

  workspaceName.addEventListener("blur", () => {
    if (workspaceName.value.trim()) Meridian.clearFieldError(workspaceName);
  });

  supportEmail.addEventListener("blur", () => {
    if (supportEmail.value.trim()) validateSupportEmail();
  });

  revealToken.addEventListener("click", () => {
    tokenVisible = !tokenVisible;
    updateTokenDisplay();
    Meridian.announce(tokenVisible ? "Production token revealed." : "Production token hidden.");
    tokenInput.focus();
  });

  copyToken.addEventListener("click", () => {
    Meridian.copyText(actualToken, "API token copied");
  });

  rotateToken.addEventListener("click", () => {
    window.setTimeout(() => rotateConfirm.focus(), 60);
  });

  rotateConfirm.addEventListener("click", async () => {
    Meridian.setBusy(rotateConfirm, true, "Rotating…");
    await Meridian.wait(700);
    actualToken = generateToken();
    updateTokenDisplay();
    tokenStatus.textContent = "Rotated just now";
    const firstMeta = tokenMeta.querySelector("span");
    if (firstMeta) firstMeta.textContent = "Created just now";
    Meridian.setBusy(rotateConfirm, false);
    rotateDialog.close();
    Meridian.toast("Production token rotated");
    Meridian.announce("Production token rotated. The previous token remains valid for 24 hours in this demo narrative.");
  });

  deleteWorkspace.addEventListener("click", () => {
    deleteConfirm.value = "";
    updateDeleteState();
    window.setTimeout(() => deleteConfirm.focus(), 60);
  });

  deleteConfirm.addEventListener("input", updateDeleteState);

  deleteConfirm.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !deleteConfirmButton.disabled) {
      event.preventDefault();
      deleteConfirmButton.click();
    }
  });

  deleteDialog.addEventListener("close", () => {
    deleteConfirm.value = "";
    updateDeleteState();
    for (const node of deleteDialog.querySelectorAll(".field-error")) {
      node.textContent = "";
      node.hidden = true;
    }
  });

  deleteConfirmButton.addEventListener("click", async () => {
    if (deleteConfirm.value.trim() !== deleteTarget) {
      Meridian.setFieldError(deleteConfirm, `Type “${deleteTarget}” exactly to continue.`);
      deleteConfirm.focus();
      return;
    }
    Meridian.setBusy(deleteConfirmButton, true, "Deleting…");
    await Meridian.wait(850);
    deleteDialog.close();
    Meridian.toast("Demo workspace deletion complete");
    Meridian.announce("Demo workspace deletion complete. Returning to sign in.");
    await Meridian.wait(650);
    window.location.href = "../login-page/";
  });

  window.addEventListener(
    "scroll",
    () => {
      if (!navFrame) {
        navFrame = window.requestAnimationFrame(syncNav);
      }
    },
    { passive: true },
  );

  for (const link of navLinks) {
    link.addEventListener("click", () => {
      setActiveNav(link.getAttribute("href").slice(1));
    });
  }

  baseline = captureState();
  switchLabels();
  updateTokenDisplay();
  updateDisplayedName();
  refreshSavebar();
  syncNav();
})();
