document.addEventListener("DOMContentLoaded", () => {
    const categoryItems = document.querySelectorAll(".category-item");
  
    categoryItems.forEach((item) => {
      item.addEventListener("click", () => {
        const checkbox = item.querySelector("input");
        checkbox.checked = !checkbox.checked;
        item.classList.toggle("selected");
      });
    });
  });
  