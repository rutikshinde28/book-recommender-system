# 📚 Book Recommender System

A web-based **Book Recommender System** built using Python and Flask. The system helps users discover books through popularity-based recommendations and collaborative filtering.

## 🚀 Features

* 📖 Displays the top 50 trending/popular books.
* 🔍 Allows users to search for a book.
* 🤖 Recommends 5 similar books using collaborative filtering.
* ⭐ Uses book ratings to calculate recommendations.
* 🌐 Simple and user-friendly Flask web interface.
* 🎨 Generates book-cover visuals directly in the application.

## 🛠️ Technologies Used

* **Python**
* **Flask**
* **Pandas**
* **NumPy**
* **Scikit-learn**
* **HTML/CSS**
* **Pickle**
* **Collaborative Filtering**
* **Cosine Similarity**

## 📂 Project Structure

```text
book-recommender/
│
├── app.py
├── generate_data.py
├── model_training.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── Books.csv
│   ├── Users.csv
│   └── Ratings.csv
│
├── models/
│   ├── books.pkl
│   ├── popular.pkl
│   ├── pt.pkl
│   └── similarity_scores.pkl
│
├── static/
│   ├── style.css
│   └── covers.js
│
└── templates/
    ├── index.html
    └── recommend.html
```

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/rutikshinde28/book-recommender-project.git
cd book-recommender-project
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## ▶️ Run the Project

Start the Flask application:

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

## 🧠 How It Works

### 1. Popularity-Based Recommendation

The system calculates the number of ratings and average rating for each book. The highest-rated popular books are displayed as the **Top 50 Trending Books**.

### 2. Collaborative Filtering

The system creates a **User × Book rating matrix** and uses **Cosine Similarity** to find books with similar rating patterns.

When a user selects a book, the system finds the **5 most similar books** and displays them as recommendations.

## 📊 Model Training

To regenerate the recommendation models, run:

```bash
python model_training.py
```

The generated model files are stored in the `models/` folder.

If you want to generate the demo dataset again, run:

```bash
python generate_data.py
```

## 🎯 Project Objective

The main objective of this project is to build a simple recommendation system that helps users discover books they may be interested in by analyzing book ratings and popularity.

## 🔮 Future Improvements

* Add user login and personalized recommendations.
* Add genre-based filtering.
* Improve the recommendation algorithm.
* Add more books and ratings.
* Deploy the application online.

## 👨‍💻 Author

**Rutik Shinde**

GitHub: https://github.com/rutikshinde28
