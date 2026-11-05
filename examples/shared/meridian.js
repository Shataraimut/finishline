(() => {
  "use strict";

  const Meridian = {};
  let dialogTrigger = null;
  let toastTimer = null;

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => {
      const replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      };
      return replacements[character];
    });
  }

  function toastNode() {
    let node = document.getElementById("toast");
    if (!node) {
      node = document.createElement("div");
      node.id = "toast";
      node.className = "toast";
      node.setAttribute("role", "status");
      node.setAttribute("aria-live", "polite");
      document.body.append(node);
    }
    return node;
  }

  function announceNode() {
    let node = document.getElementById("announcer");
    if (!node) {
      node = document.createElement("div");
      node.id = "announcer";
      node.className = "sr-region";
      node.setAttribute("aria-live", "polite");
      document.body.append(node);
    }
    return node;
  }

  Meridian.toast = (message, options = {}) => {
    const node = toastNode();
    node.textContent = message;
    node.classList.toggle("is-error", Boolean(options.error));
    node.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => {
      node.classList.remove("is-visible");
    }, options.duration || 2800);
  };

  Meridian.announce = (message) => {
    const node = announceNode();
    node.textContent = "";
    window.setTimeout(() => {
      node.textContent = message;
    }, 30);
  };

  Meridian.openDialog = (dialog, trigger) => {
    if (!dialog) return;
    dialogTrigger = trigger || document.activeElement;
    for (const open of document.querySelectorAll("dialog[open]")) {
      if (open !== dialog) open.close();
    }
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    } else {
      dialog.setAttribute("open", "");
    }
  };

  Meridian.closeDialog = (dialog) => {
    if (dialog) dialog.close();
  };

  Meridian.setBusy = (button, busy, label = "Working…") => {
    if (!button) return;
    if (busy) {
      if (!button.dataset.idleHtml) button.dataset.idleHtml = button.innerHTML;
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      button.innerHTML = `<span class="spinner" aria-hidden="true"></span>${escapeHtml(label)}`;
    } else {
      if (button.dataset.idleHtml) {
        button.innerHTML = button.dataset.idleHtml;
        delete button.dataset.idleHtml;
      }
      button.disabled = false;
      button.removeAttribute("aria-busy");
    }
  };

  Meridian.wait = (milliseconds) =>
    new Promise((resolve) => window.setTimeout(resolve, milliseconds));

  Meridian.todayLabel = () => {
    const formatter = new Intl.DateTimeFormat("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
    return formatter.format(new Date());
  };

  Meridian.formatNumber = (value) => new Intl.NumberFormat("en-US").format(value);

  Meridian.emailValid = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value).trim());

  Meridian.setFieldError = (input, message) => {
    if (!input) return;
    input.setAttribute("aria-invalid", "true");
    const error = document.getElementById(`${input.id}-error`);
    if (error) {
      error.textContent = message;
      error.hidden = false;
    }
    const describedBy = (input.getAttribute("aria-describedby") || "")
      .split(/\s+/)
      .filter(Boolean);
    if (error && !describedBy.includes(error.id)) {
      describedBy.push(error.id);
      input.setAttribute("aria-describedby", describedBy.join(" "));
    }
  };

  Meridian.clearFieldError = (input) => {
    if (!input) return;
    input.removeAttribute("aria-invalid");
    const error = document.getElementById(`${input.id}-error`);
    if (error) {
      error.textContent = "";
      error.hidden = true;
    }
  };

  Meridian.showFormAlert = (alert, message, options = {}) => {
    if (!alert) return;
    const paragraph = alert.querySelector("p") || alert;
    paragraph.textContent = message;
    alert.hidden = false;
    alert.classList.toggle("is-success", Boolean(options.success));
  };

  Meridian.hideFormAlert = (alert) => {
    if (!alert) return;
    alert.hidden = true;
  };

  Meridian.copyText = async (text, successMessage = "Copied") => {
    try {
      await navigator.clipboard.writeText(text);
      Meridian.toast(successMessage);
      Meridian.announce(successMessage);
      return true;
    } catch {
      const field = document.createElement("textarea");
      field.value = text;
      field.setAttribute("readonly", "");
      field.style.position = "fixed";
      field.style.opacity = "0";
      document.body.append(field);
      field.select();
      let copied = false;
      try {
        copied = document.execCommand("copy");
      } catch {
        copied = false;
      }
      field.remove();
      Meridian.toast(copied ? successMessage : "Copy failed", { error: !copied });
      Meridian.announce(copied ? successMessage : "Copy failed");
      return copied;
    }
  };

  function setShell(open) {
    const sidebar = document.querySelector("[data-sidebar]");
    const backdrop = document.querySelector("[data-shell-backdrop]");
    const toggle = document.querySelector("[data-shell-toggle]");
    if (!sidebar || !toggle) return;
    sidebar.classList.toggle("is-open", open);
    document.body.classList.toggle("is-locked", open);
    toggle.setAttribute("aria-expanded", String(open));
    if (backdrop) backdrop.classList.toggle("is-visible", open);
    const label = toggle.querySelector(".sr-only");
    if (label) label.textContent = open ? "Close navigation" : "Open navigation";
    if (open) {
      const first = sidebar.querySelector("a, button, select");
      if (first) first.focus();
    }
  }

  function initShell() {
    const sidebar = document.querySelector("[data-sidebar]");
    const toggle = document.querySelector("[data-shell-toggle]");
    const backdrop = document.querySelector("[data-shell-backdrop]");
    if (!sidebar || !toggle) return;
    toggle.addEventListener("click", () => {
      setShell(!sidebar.classList.contains("is-open"));
    });
    if (backdrop) {
      backdrop.addEventListener("click", () => setShell(false));
    }
    for (const link of sidebar.querySelectorAll("a")) {
      link.addEventListener("click", () => setShell(false));
    }
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && sidebar.classList.contains("is-open")) {
        setShell(false);
        toggle.focus();
      }
    });
    window.addEventListener("resize", () => {
      if (window.innerWidth > 880 && sidebar.classList.contains("is-open")) {
        setShell(false);
      }
    });
  }

  function initDialogs() {
    document.addEventListener("click", (event) => {
      const opener = event.target.closest("[data-open-dialog]");
      if (opener) {
        event.preventDefault();
        Meridian.openDialog(
          document.getElementById(opener.dataset.openDialog),
          opener,
        );
        return;
      }
      const closer = event.target.closest("[data-close-dialog]");
      if (closer) {
        const dialog = closer.closest("dialog");
        if (dialog) dialog.close();
      }
    });
    for (const dialog of document.querySelectorAll("dialog")) {
      dialog.addEventListener("click", (event) => {
        if (event.target === dialog) dialog.close();
      });
      dialog.addEventListener("close", () => {
        const trigger = dialogTrigger;
        dialogTrigger = null;
        if (trigger && document.contains(trigger)) {
          trigger.focus({ preventScroll: true });
        }
      });
    }
  }

  Meridian.escapeHtml = escapeHtml;
  initShell();
  initDialogs();
  window.Meridian = Meridian;
})();
