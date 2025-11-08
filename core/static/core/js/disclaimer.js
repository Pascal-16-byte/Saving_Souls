document.addEventListener("DOMContentLoaded", function () {
  const sections = document.querySelectorAll(".section");
  const prevBtn = document.getElementById("prev-btn");
  const nextBtn = document.getElementById("next-btn");
  const acceptBtn = document.getElementById("accept-btn");
  const agreeCheckbox = document.getElementById("agree-checkbox");

  let current = 0;

  function updateSections() {
    sections.forEach((sec, i) => {
      sec.classList.toggle("active", i === current);
    });
    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === sections.length - 1;
  }

  prevBtn.addEventListener("click", () => {
    if (current > 0) current--;
    updateSections();
  });

  nextBtn.addEventListener("click", () => {
    if (current < sections.length - 1) current++;
    updateSections();
  });

  agreeCheckbox.addEventListener("change", () => {
    acceptBtn.disabled = !agreeCheckbox.checked;
  });

  acceptBtn.addEventListener("click", () => {
    alert("Disclaimer accepted! Redirecting to platform...");
    window.location.href = "/home/"; // Redirect to your platform's home page
  });

  updateSections();
});
