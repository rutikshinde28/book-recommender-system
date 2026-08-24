"""
model_training.py
------------------
Recreates the tutorial's ML pipeline end-to-end:

  1. Load & merge Books / Users / Ratings
  2. POPULARITY-BASED RECOMMENDER
     - keep only books with a minimum number of ratings
     - rank by (num_ratings, avg_rating) -> Top 50 "Trending Books"
  3. COLLABORATIVE FILTERING RECOMMENDER
     - keep only users who rated > 200... (scaled down here since our
       demo dataset is smaller) and books with >= a minimum rating count
     - build a User x Book pivot table of ratings
     - compute cosine similarity between books (item-based CF)
     - for any book, return the 5 most similar books
  4. Pickle everything the Flask app needs:
     - models/popular.pkl          (top 50 books dataframe)
     - models/pt.pkl               (pivot table)
     - models/books.pkl            (deduplicated books dataframe)
     - models/similarity_scores.pkl(book-book cosine similarity matrix)

Run: python model_training.py
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity

pd.set_option("display.max_columns", None)

# ---------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------
print("Loading data...")
books = pd.read_csv("data/Books.csv")
users = pd.read_csv("data/Users.csv")
ratings = pd.read_csv("data/Ratings.csv")

print(f"books: {books.shape}, users: {users.shape}, ratings: {ratings.shape}")

# Merge ratings with book metadata (ISBN is the join key, same as tutorial)
ratings_with_name = ratings.merge(books, on="ISBN")

# ---------------------------------------------------------------------
# 2. POPULARITY-BASED RECOMMENDER
#    (books that are in trend / rated by the most people)
# ---------------------------------------------------------------------
print("\nBuilding popularity-based recommender...")

num_rating_df = (
    ratings_with_name.groupby("Book-Title")
    .count()["Book-Rating"]
    .reset_index()
    .rename(columns={"Book-Rating": "num_ratings"})
)

avg_rating_df = (
    ratings_with_name.groupby("Book-Title")["Book-Rating"]
    .mean()
    .reset_index()
    .rename(columns={"Book-Rating": "avg_rating"})
)

popular_df = num_rating_df.merge(avg_rating_df, on="Book-Title")

# Original tutorial threshold is >=250 ratings (huge Book-Crossing dataset);
# our demo dataset is smaller, so we scale the threshold down proportionally.
MIN_RATINGS_POPULAR = 15
popular_df = popular_df[popular_df["num_ratings"] >= MIN_RATINGS_POPULAR]
popular_df = popular_df.sort_values("avg_rating", ascending=False).head(50)

popular_df = popular_df.merge(
    books, on="Book-Title"
).drop_duplicates("Book-Title")[
    ["Book-Title", "Book-Author", "ISBN", "Image-URL-M", "num_ratings", "avg_rating"]
]
popular_df["avg_rating"] = popular_df["avg_rating"].round(2)

print(f"Popularity table: {popular_df.shape[0]} books")
print(popular_df.head(5).to_string(index=False))

# ---------------------------------------------------------------------
# 3. COLLABORATIVE FILTERING RECOMMENDER (item-based, cosine similarity)
# ---------------------------------------------------------------------
print("\nBuilding collaborative filtering recommender...")

# Only consider "explicit" ratings (>0), same idea as the tutorial
explicit_ratings = ratings_with_name[ratings_with_name["Book-Rating"] > 0]

# Keep "knowledgeable" users who rated a decent number of books
MIN_RATINGS_PER_USER = 10
user_rating_counts = explicit_ratings.groupby("User-ID").count()["Book-Rating"]
knowledgeable_users = user_rating_counts[user_rating_counts >= MIN_RATINGS_PER_USER].index
filtered_ratings = explicit_ratings[explicit_ratings["User-ID"].isin(knowledgeable_users)]

# Keep books that have a minimum number of ratings so the pivot table isn't too sparse
MIN_RATINGS_PER_BOOK = 8
book_rating_counts = filtered_ratings.groupby("Book-Title").count()["Book-Rating"]
famous_books = book_rating_counts[book_rating_counts >= MIN_RATINGS_PER_BOOK].index
final_ratings = filtered_ratings[filtered_ratings["Book-Title"].isin(famous_books)]

print(f"Users kept: {len(knowledgeable_users)}, Books kept: {len(famous_books)}, "
      f"Ratings used: {len(final_ratings)}")

# Pivot: rows = book title, columns = user id, values = rating
pt = final_ratings.pivot_table(
    index="Book-Title", columns="User-ID", values="Book-Rating"
)
pt.fillna(0, inplace=True)

print(f"Pivot table shape: {pt.shape}")

# Item-item cosine similarity between books based on rating patterns
similarity_scores = cosine_similarity(pt)
print(f"Similarity matrix shape: {similarity_scores.shape}")


def recommend(book_name, n=5):
    """Return the n most similar books to `book_name` (must exist in pt.index)."""
    if book_name not in pt.index:
        return []
    index = np.where(pt.index == book_name)[0][0]
    similar_items = sorted(
        list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True
    )[1: n + 1]

    data = []
    for i, score in similar_items:
        title = pt.index[i]
        item = books[books["Book-Title"] == title].drop_duplicates("Book-Title")
        if item.empty:
            continue
        row = item.iloc[0]
        data.append({
            "title": row["Book-Title"],
            "author": row["Book-Author"],
            "image": row["Image-URL-M"],
            "score": round(float(score), 3),
        })
    return data


# quick sanity check
sample_book = pt.index[0]
print(f"\nSample recommendation for: {sample_book!r}")
for rec in recommend(sample_book):
    print(f"  -> {rec['title']} (score={rec['score']})")

# ---------------------------------------------------------------------
# 4. SAVE ARTIFACTS FOR THE FLASK APP
# ---------------------------------------------------------------------
print("\nSaving pickle files to models/ ...")
pickle.dump(popular_df, open("models/popular.pkl", "wb"))
pickle.dump(pt, open("models/pt.pkl", "wb"))
pickle.dump(books, open("models/books.pkl", "wb"))
pickle.dump(similarity_scores, open("models/similarity_scores.pkl", "wb"))

print("Done. Artifacts: models/popular.pkl, models/pt.pkl, "
      "models/books.pkl, models/similarity_scores.pkl")
