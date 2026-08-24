# The Shelf — Book Recommender System

A recreation of the classic **Book Recommender System** project (Book-Crossing
dataset, popularity-based + item-based collaborative filtering, served as a
Flask web app) — the same architecture used in the referenced tutorial.

## How it works

1. **`generate_data.py`** — builds `data/Books.csv`, `data/Users.csv`,
   `data/Ratings.csv` in the exact Book-Crossing column format. Since the
   real Kaggle dataset requires a manual download (see below), this script
   generates a realistic stand-in: ~100 real, well-known books across 8
   genre "taste clusters," 600 synthetic users, and ~15,000 ratings, where
   users rate books in their taste cluster(s) more highly — so the
   collaborative-filtering model has genuine structure to learn from, not
   just noise.

2. **`model_training.py`** — the ML pipeline itself:
   - **Popularity-Based Recommender**: groups ratings by book, filters to
     books with a minimum number of ratings, ranks by average rating →
     Top 50 "Trending Books" table.
   - **Collaborative Filtering (item-based)**: filters to active users and
     well-rated books, builds a *Book × User* pivot table of ratings, and
     computes **cosine similarity** between books based on rating patterns.
     Given any book, it returns the 5 most similar titles.
   - Saves everything the web app needs as pickles in `models/`:
     `popular.pkl`, `pt.pkl`, `books.pkl`, `similarity_scores.pkl`.

3. **`app.py`** — Flask app with two pages:
   - `/` — homepage showing the Top 50 trending books (popularity-based).
   - `/recommend` — search a book title, get 5 similar titles with a
     match-percentage bar (collaborative filtering).

## Run it

```bash
pip install -r requirements.txt

# 1. generate the dataset
python generate_data.py

# 2. train the models / build the pickles
python model_training.py

# 3. launch the web app
python app.py
```

Then open **http://127.0.0.1:5000**.

## Using the real Book-Crossing dataset

To match the original tutorial exactly, download the real dataset (Books.csv,
Users.csv, Ratings.csv — ~270k books, ~1.1M ratings) and drop the three CSVs
into `data/`, replacing the generated ones. It's available on Kaggle
("Book Recommendation Dataset" / Book-Crossing). Then in `model_training.py`
bump the thresholds back up to the tutorial's originals:

```python
MIN_RATINGS_POPULAR = 250      # was 15
MIN_RATINGS_PER_USER = 200     # was 10
MIN_RATINGS_PER_BOOK = 50      # was 8
```

Re-run `python model_training.py` and restart `app.py` — no other code
changes needed, since the app just loads whatever's in `models/*.pkl`.

## Project structure

```
book-recommender/
├── data/                  Books.csv, Users.csv, Ratings.csv
├── models/                pickled artifacts (popular.pkl, pt.pkl, books.pkl, similarity_scores.pkl)
├── templates/
│   ├── index.html         Top-50 trending books page
│   └── recommend.html     search + similar-books results
├── static/
│   └── style.css
├── generate_data.py        builds the demo dataset
├── model_training.py       popularity model + collaborative filtering + pickling
├── app.py                  Flask app
└── requirements.txt
```

## Deploying

The original project was deployed to Heroku. Any Flask-friendly host works
today (Render, Railway, PythonAnywhere, Fly.io) — just make sure `models/*.pkl`
and `data/*.csv` are included in the deployment and add a `Procfile`:

```
web: gunicorn app:app
```
