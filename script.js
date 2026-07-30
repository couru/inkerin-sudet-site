const menuButton = document.querySelector(".menuButton");
const navigation = document.querySelector("#main-nav");

menuButton?.addEventListener("click", () => {
  const isOpen = menuButton.getAttribute("aria-expanded") === "true";
  menuButton.setAttribute("aria-expanded", String(!isOpen));
  navigation?.classList.toggle("isOpen", !isOpen);
  document.body.classList.toggle("menuOpen", !isOpen);
});

navigation?.addEventListener("click", (event) => {
  if (!event.target.closest("a")) return;
  menuButton?.setAttribute("aria-expanded", "false");
  navigation.classList.remove("isOpen");
  document.body.classList.remove("menuOpen");
});

const revealItems = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("isVisible");
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.12 },
  );
  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add("isVisible"));
}

const phoneInput = document.querySelector('input[name="phone"]');
phoneInput?.addEventListener("input", () => {
  const digits = phoneInput.value.replace(/\D/g, "").replace(/^8/, "7").slice(0, 11);
  const normalized = digits.startsWith("7") ? digits : `7${digits}`;
  const parts = [
    normalized.slice(1, 4),
    normalized.slice(4, 7),
    normalized.slice(7, 9),
    normalized.slice(9, 11),
  ];
  let value = "+7";
  if (parts[0]) value += ` (${parts[0]}`;
  if (parts[0].length === 3) value += ")";
  if (parts[1]) value += ` ${parts[1]}`;
  if (parts[2]) value += `-${parts[2]}`;
  if (parts[3]) value += `-${parts[3]}`;
  phoneInput.value = value;
});

document.querySelector("#trial-form")?.addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const status = form.querySelector(".formStatus");
  const name = new FormData(form).get("name")?.toString().trim();
  status.textContent = `${name ? `${name}, с` : "С"}пасибо! Заявка принята. Мы свяжемся с вами и подберём первую тренировку.`;
  form.reset();
});

document.querySelector("#year").textContent = new Date().getFullYear();
