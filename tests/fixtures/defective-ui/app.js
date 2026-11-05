const form = document.querySelector("#settings-form");
const toast = document.querySelector("#toast");

document.querySelectorAll(".toggle").forEach((toggle) => {
  const flip = () => {
    const next = toggle.getAttribute("aria-checked") !== "true";
    toggle.setAttribute("aria-checked", String(next));
  };
  toggle.addEventListener("click", flip);
  toggle.addEventListener("keydown", (event) => {
    if (event.key === " " || event.key === "Enter") {
      event.preventDefault();
      flip();
    }
  });
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(form);
  fetch("/api/settings", { method: "POST", body: data });
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2200);
});

document.querySelector(".delete").addEventListener("click", () => {
  fetch("/api/workspace", { method: "DELETE" });
});

document.querySelector(".docs-link").addEventListener("click", () => {
  window.location.href = "https://docs.example.com/migration";
});