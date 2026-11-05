(() => {
  "use strict";

  const form = document.getElementById("login-form");
  const email = document.getElementById("email");
  const password = document.getElementById("password");
  const submit = document.getElementById("login-submit");
  const alert = document.getElementById("login-alert");
  const reveal = document.getElementById("reveal-password");
  const fillDemo = document.getElementById("fill-demo");
  const forgot = document.getElementById("forgot-password");
  const resetDialog = document.getElementById("reset-dialog");
  const resetForm = document.getElementById("reset-form");
  const resetEmail = document.getElementById("reset-email");
  const resetSubmit = document.getElementById("reset-submit");
  const resetSuccess = document.getElementById("reset-success");
  const resetClose = resetDialog.querySelector("[data-close-dialog]");
  const demoEmail = "ops@meridian.dev";
  const demoPassword = "meridian-demo";

  function validateEmailField(input, message) {
    const value = input.value.trim();
    if (!value) {
      Meridian.setFieldError(input, "Enter your work email.");
      return false;
    }
    if (!Meridian.emailValid(value)) {
      Meridian.setFieldError(input, "Enter an email in the format name@company.com.");
      return false;
    }
    Meridian.clearFieldError(input);
    return true;
  }

  function validatePasswordField() {
    if (!password.value) {
      Meridian.setFieldError(password, "Enter your password.");
      return false;
    }
    if (password.value.length < 8) {
      Meridian.setFieldError(password, "Password must be at least 8 characters.");
      return false;
    }
    Meridian.clearFieldError(password);
    return true;
  }

  reveal.addEventListener("click", () => {
    const visible = password.type === "text";
    password.type = visible ? "password" : "text";
    reveal.textContent = visible ? "Show" : "Hide";
    reveal.setAttribute("aria-pressed", String(!visible));
    reveal.setAttribute("aria-label", visible ? "Show password" : "Hide password");
    password.focus();
  });

  fillDemo.addEventListener("click", () => {
    email.value = demoEmail;
    password.value = demoPassword;
    Meridian.clearFieldError(email);
    Meridian.clearFieldError(password);
    Meridian.hideFormAlert(alert);
    password.focus();
    Meridian.toast("Demo credentials filled");
    Meridian.announce("Demo credentials filled into the sign-in form.");
  });

  forgot.addEventListener("click", () => {
    resetEmail.value = email.value.trim();
    window.setTimeout(() => resetEmail.focus(), 60);
  });

  email.addEventListener("blur", () => {
    if (email.value) validateEmailField(email);
  });

  password.addEventListener("blur", () => {
    if (password.value) validatePasswordField();
  });

  for (const input of [email, password]) {
    input.addEventListener("input", () => {
      Meridian.clearFieldError(input);
      Meridian.hideFormAlert(alert);
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    Meridian.hideFormAlert(alert);
    const emailOk = validateEmailField(email);
    const passwordOk = validatePasswordField();
    if (!emailOk || !passwordOk) {
      Meridian.showFormAlert(alert, "Check the highlighted fields and try again.");
      (emailOk ? password : email).focus();
      return;
    }

    form.setAttribute("aria-busy", "true");
    Meridian.setBusy(submit, true, "Signing in…");
    await Meridian.wait(750);

    const accepted =
      email.value.trim().toLowerCase() === demoEmail &&
      password.value === demoPassword;

    if (accepted) {
      Meridian.showFormAlert(alert, "Credentials accepted. Opening the dashboard…", {
        success: true,
      });
      Meridian.announce("Sign-in accepted. Opening the dashboard.");
      await Meridian.wait(450);
      window.location.href = "../dashboard/";
      return;
    }

    Meridian.setBusy(submit, false);
    form.removeAttribute("aria-busy");
    Meridian.showFormAlert(alert, "Those credentials do not match the demo workspace. Use the demo access shown below or check your details.");
    Meridian.setFieldError(password, "Incorrect password for this demo account.");
    password.value = "";
    password.focus();
    Meridian.announce("Sign-in failed. Demo credentials are available below the form.");
  });

  resetForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    Meridian.hideFormAlert(resetSuccess);
    if (!validateEmailField(resetEmail)) {
      resetEmail.focus();
      return;
    }

    Meridian.setBusy(resetSubmit, true, "Sending…");
    resetEmail.disabled = true;
    await Meridian.wait(700);
    Meridian.setBusy(resetSubmit, false);
    resetSubmit.disabled = true;
    resetSubmit.textContent = "Link sent";
    resetSuccess.textContent = "If an account uses that address, a single-use link is on its way. This static demo does not send email.";
    resetSuccess.hidden = false;
    resetClose.focus({ preventScroll: true });
    Meridian.announce("Password reset request completed in demo mode.");
  });

  resetEmail.addEventListener("input", () => {
    Meridian.clearFieldError(resetEmail);
  });

  resetDialog.addEventListener("close", () => {
    resetForm.reset();
    Meridian.clearFieldError(resetEmail);
    resetEmail.disabled = false;
    resetSubmit.disabled = false;
    resetSubmit.textContent = "Send reset link";
    resetSuccess.hidden = true;
    resetSuccess.textContent = "";
  });
})();
