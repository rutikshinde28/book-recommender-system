"""
app.py
------
Flask web app for the Book Recommender System.

Routes:
  GET  /            -> homepage: Top 50 trending books (popularity-based)
  GET  /recommend    -> search form
  POST /recommend_books -> collaborative-filtering recommendations for a chosen title
"""

import pickle
import base64
import textwrap
import numpy as np
from flask import Flask, render_template, request

app = Flask(__name__)

SPINE_PALETTE = ["#7b2d26", "#b08d57", "#1b2a41", "#3f5d4f", "#8a3a5c", "#5c4a2e"]


@app.template_filter("spine_color")
def spine_color(title: str) -> str:
    """Deterministically pick a 'spine' color for a book title (visual only)."""
    h = sum(ord(c) for c in title)
    return SPINE_PALETTE[h % len(SPINE_PALETTE)]


def _wrap_title(title, width=16, max_lines=4):
    lines = textwrap.wrap(title, width=width)[:max_lines]
    if len(lines) == max_lines and len(" ".join(lines)) < len(title):
        lines[-1] = lines[-1].rstrip() + "…"
    return lines


@app.template_filter("cover_svg")
def cover_svg(title: str, author: str = "") -> str:
    """
    Build a generated book-cover image (as an inline SVG data URI) so covers
    always render with zero external/network dependency — no broken-image
    icons, no placeholder services that might be down.
    """
    color = spine_color(title)
    lines = _wrap_title(title)
    title_svg = "".join(
        f'<tspan x="20" dy="{0 if i == 0 else 26}">{line}</tspan>'
        for i, line in enumerate(lines)
    )
    author_y = 40 + len(lines) * 26 + 18
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300" viewBox="0 0 200 300">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{color}"/>
      <stop offset="1" stop-color="#26241f"/>
    </linearGradient>
  </defs>
  <rect width="200" height="300" fill="url(#g)"/>
  <rect x="0" y="0" width="9" height="300" fill="{color}"/>
  <rect x="14" y="14" width="172" height="272" fill="none" stroke="rgba(244,236,216,.35)" stroke-width="1"/>
  <text x="20" y="40" font-family="Georgia, serif" font-size="17" font-weight="600" fill="#f4ecd8">{title_svg}</text>
  <text x="20" y="{author_y}" font-family="Georgia, serif" font-size="12" fill="rgba(244,236,216,.75)">{author}</text>
</svg>'''
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


popular_df = pickle.load(open("models/popular.pkl", "rb"))
pt = pickle.load(open("models/pt.pkl", "rb"))
books = pickle.load(open("models/books.pkl", "rb"))
similarity_scores = pickle.load(open("models/similarity_scores.pkl", "rb"))

ALL_TITLES = sorted(pt.index.tolist())


@app.route("/")
def index():
    return render_template(
        "index.html",
        book_title=list(popular_df["Book-Title"].values),
        author=list(popular_df["Book-Author"].values),
        isbn=list(popular_df["ISBN"].astype(str).values),
        image=list(popular_df["Image-URL-M"].values),
        votes=list(popular_df["num_ratings"].values),
        rating=list(popular_df["avg_rating"].values),
    )


@app.route("/recommend")
def recommend_ui():
    return render_template("recommend.html", titles=ALL_TITLES, data=None, query=None)


@app.route("/recommend_books", methods=["POST"])
def recommend_books():
    user_input = request.form.get("user_input", "").strip()
    data = []

    if user_input in pt.index:
        index = np.where(pt.index == user_input)[0][0]
        similar_items = sorted(
            list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True
        )[1:6]

        for i, score in similar_items:
            title = pt.index[i]
            item = books[books["Book-Title"] == title].drop_duplicates("Book-Title")
            if item.empty:
                continue
            row = item.iloc[0]
            data.append({
                "title": row["Book-Title"],
                "author": row["Book-Author"],
                "isbn": str(row["ISBN"]),
                "image": row["Image-URL-M"],
                "score": round(float(score) * 100, 1),
            })

    return render_template("recommend.html", titles=ALL_TITLES, data=data, query=user_input)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
