/**
 * covers.js
 * ---------
 * Every cover <img> starts pointed at Open Library (server-rendered).
 * If that 404s (real 404, thanks to ?default=false on the URL), we try
 * Google Books' cover database as a second real source — its ISBN
 * coverage is broader than Open Library's. Only if *both* real sources
 * come up empty do we fall back to the generated placeholder art.
 */
async function resolveCover(img) {
  const isbn = img.dataset.isbn;
  const fallback = img.dataset.fallback;

  try {
    const res = await fetch(`https://www.googleapis.com/books/v1/volumes?q=isbn:${isbn}`);
    const data = await res.json();
    const links = data.items && data.items[0] &&
                  data.items[0].volumeInfo &&
                  data.items[0].volumeInfo.imageLinks;
    const thumb = links && (links.thumbnail || links.smallThumbnail);
    if (thumb) {
      img.src = thumb.replace("http://", "https://").replace("zoom=1", "zoom=2");
      return;
    }
  } catch (e) {
    /* network hiccup or no CORS — fall through to placeholder */
  }
  img.src = fallback;
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("img[data-isbn]").forEach((img) => {
    img.addEventListener(
      "error",
      function onErr() {
        img.removeEventListener("error", onErr);
        resolveCover(img);
      },
      { once: true }
    );
  });
});
