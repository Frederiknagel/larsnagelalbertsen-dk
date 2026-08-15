// Simpelt lightbox: klik på et galleri-billede for at se det i stort format.
// Ingen afhængigheder, virker på alle sider med .gallery img.

function initLightbox() {
  const images = document.querySelectorAll(".gallery img");
  if (images.length === 0) return;

  const overlay = document.createElement("div");
  overlay.className = "lightbox-overlay";
  overlay.innerHTML = `
    <button class="lightbox-close" aria-label="Luk">&times;</button>
    <img class="lightbox-image" alt="">
  `;
  document.body.appendChild(overlay);

  const lightboxImg = overlay.querySelector(".lightbox-image");
  const closeBtn = overlay.querySelector(".lightbox-close");

  function open(src, alt) {
    lightboxImg.src = src;
    lightboxImg.alt = alt || "";
    overlay.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }

  function close() {
    overlay.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  images.forEach((img) => {
    img.style.cursor = "zoom-in";
    img.addEventListener("click", () => open(img.src, img.alt));
  });

  overlay.addEventListener("click", (e) => {
    if (e.target === lightboxImg) return; // klik på selve billedet lukker ikke
    close();
  });
  closeBtn.addEventListener("click", close);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
}

document.addEventListener("DOMContentLoaded", initLightbox);
