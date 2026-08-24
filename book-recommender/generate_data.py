"""
generate_data.py
-----------------
Creates Books.csv, Users.csv, Ratings.csv in the same shape as the
Kaggle "Book-Crossing" dataset used in the original tutorial:

Books.csv   -> ISBN, Book-Title, Book-Author, Year-Of-Publication, Publisher,
               Image-URL-S, Image-URL-M, Image-URL-L
Users.csv   -> User-ID, Location, Age
Ratings.csv -> User-ID, ISBN, Book-Rating   (0 = implicit, 1-10 = explicit)

NOTE: The real project uses Kaggle's Book-Crossing dataset (~270k books,
~1.1M ratings). That file has to be downloaded manually (see README).
This script builds a smaller, realistic stand-in using real book titles
AND real ISBNs, so cover art loads from Open Library's public cover API
(https://covers.openlibrary.org) -- the same "link out to a hosted image"
approach the original Book-Crossing dataset itself uses. You can run the
*entire* pipeline (EDA -> popularity model -> collaborative filtering ->
Flask app) immediately, with no downloads. Swap in the real CSVs later
and everything downstream still works.
"""

import csv
import random

random.seed(42)

# ---------------------------------------------------------------------
# 1. A real, varied catalogue of books across genres/"taste clusters".
#    Each cluster represents readers who tend to rate these books highly,
#    which is what gives the collaborative-filtering model real signal.
# ---------------------------------------------------------------------
CLUSTERS = {
    "fantasy": [
        ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", 1997, "Scholastic", "9780590353427"),
        ("The Hobbit", "J.R.R. Tolkien", 1937, "Houghton Mifflin", "9780547928227"),
        ("The Fellowship of the Ring", "J.R.R. Tolkien", 1954, "George Allen & Unwin", "9780618640157"),
        ("A Game of Thrones", "George R.R. Martin", 1996, "Bantam Spectra", "9780553103540"),
        ("The Name of the Wind", "Patrick Rothfuss", 2007, "DAW Books", "9780756404741"),
        ("Eragon", "Christopher Paolini", 2002, "Knopf", "9780375826696"),
        ("The Way of Kings", "Brandon Sanderson", 2010, "Tor Books", "9780765326355"),
        ("Mistborn: The Final Empire", "Brandon Sanderson", 2006, "Tor Books", "9780765311788"),
        ("The Lion, the Witch and the Wardrobe", "C.S. Lewis", 1950, "Geoffrey Bles", "9780064404990"),
        ("Percy Jackson and the Lightning Thief", "Rick Riordan", 2005, "Disney-Hyperion", "9780786838653"),
        ("The Golden Compass", "Philip Pullman", 1995, "Scholastic", "9780679879244"),
        ("Wizard's First Rule", "Terry Goodkind", 1994, "Tor Books", "9780812548051"),
    ],
    "scifi": [
        ("Dune", "Frank Herbert", 1965, "Chilton Books", "9780441172719"),
        ("Ender's Game", "Orson Scott Card", 1985, "Tor Books", "9780812550702"),
        ("Foundation", "Isaac Asimov", 1951, "Gnome Press", "9780553293357"),
        ("The Martian", "Andy Weir", 2011, "Crown", "9780553418026"),
        ("Neuromancer", "William Gibson", 1984, "Ace Books", "9780441569595"),
        ("Snow Crash", "Neal Stephenson", 1992, "Bantam Books", "9780553380958"),
        ("The Left Hand of Darkness", "Ursula K. Le Guin", 1969, "Ace Books", "9780441478125"),
        ("Hyperion", "Dan Simmons", 1989, "Doubleday", "9780553283686"),
        ("Ready Player One", "Ernest Cline", 2011, "Crown", "9780307887436"),
        ("The Hitchhiker's Guide to the Galaxy", "Douglas Adams", 1979, "Pan Books", "9780345391803"),
        ("Brave New World", "Aldous Huxley", 1932, "Chatto & Windus", "9780060850524"),
        ("Nineteen Eighty-Four", "George Orwell", 1949, "Secker & Warburg", "9780451524935"),
    ],
    "mystery_thriller": [
        ("The Da Vinci Code", "Dan Brown", 2003, "Doubleday", "9780307474278"),
        ("Gone Girl", "Gillian Flynn", 2012, "Crown", "9780307588364"),
        ("The Girl with the Dragon Tattoo", "Stieg Larsson", 2005, "Norstedts Forlag", "9780307454546"),
        ("And Then There Were None", "Agatha Christie", 1939, "Collins Crime Club", "9780062073488"),
        ("The Silence of the Lambs", "Thomas Harris", 1988, "St. Martin's Press", "9780312924584"),
        ("Sharp Objects", "Gillian Flynn", 2006, "Shaye Areheart Books", "9780307341556"),
        ("The Girl on the Train", "Paula Hawkins", 2015, "Doubleday", "9781594634024"),
        ("In the Woods", "Tana French", 2007, "Viking Press", "9780143113492"),
        ("The Big Sleep", "Raymond Chandler", 1939, "Alfred A. Knopf", "9780394758282"),
        ("Sherlock Holmes: A Study in Scarlet", "Arthur Conan Doyle", 1887, "Ward Lock & Co", "9781503278921"),
        ("Murder on the Orient Express", "Agatha Christie", 1934, "Collins Crime Club", "9780062693662"),
        ("The Silent Patient", "Alex Michaelides", 2019, "Celadon Books", "9781250301697"),
    ],
    "romance": [
        ("Pride and Prejudice", "Jane Austen", 1813, "T. Egerton", "9780141439518"),
        ("The Notebook", "Nicholas Sparks", 1996, "Warner Books", "9780446605236"),
        ("Outlander", "Diana Gabaldon", 1991, "Delacorte Press", "9780440212560"),
        ("Me Before You", "Jojo Moyes", 2012, "Penguin Books", "9780143124542"),
        ("It Ends with Us", "Colleen Hoover", 2016, "Atria Books", "9781501110368"),
        ("The Fault in Our Stars", "John Green", 2012, "Dutton Books", "9780525478812"),
        ("Jane Eyre", "Charlotte Bronte", 1847, "Smith, Elder & Co", "9780142437209"),
        ("Twilight", "Stephenie Meyer", 2005, "Little, Brown", "9780316015844"),
        ("The Time Traveler's Wife", "Audrey Niffenegger", 2003, "MacAdam/Cage", "9780156029438"),
        ("Wuthering Heights", "Emily Bronte", 1847, "Thomas Cautley Newby", "9780141439556"),
        ("Bridget Jones's Diary", "Helen Fielding", 1996, "Picador", "9780140280098"),
        ("One Day", "David Nicholls", 2009, "Hodder & Stoughton", "9780307472880"),
    ],
    "literary_classics": [
        ("To Kill a Mockingbird", "Harper Lee", 1960, "J.B. Lippincott", "9780060935467"),
        ("The Great Gatsby", "F. Scott Fitzgerald", 1925, "Charles Scribner's Sons", "9780743273565"),
        ("Crime and Punishment", "Fyodor Dostoevsky", 1866, "The Russian Messenger", "9780486415871"),
        ("One Hundred Years of Solitude", "Gabriel Garcia Marquez", 1967, "Editorial Sudamericana", "9780060883287"),
        ("The Catcher in the Rye", "J.D. Salinger", 1951, "Little, Brown", "9780316769488"),
        ("Beloved", "Toni Morrison", 1987, "Alfred A. Knopf", "9781400033416"),
        ("Moby-Dick", "Herman Melville", 1851, "Harper & Brothers", "9780142437247"),
        ("War and Peace", "Leo Tolstoy", 1869, "The Russian Messenger", "9781400079988"),
        ("The Grapes of Wrath", "John Steinbeck", 1939, "The Viking Press", "9780143039433"),
        ("Anna Karenina", "Leo Tolstoy", 1877, "The Russian Messenger", "9780143035008"),
        ("Slaughterhouse-Five", "Kurt Vonnegut", 1969, "Delacorte Press", "9780440180296"),
        ("Invisible Man", "Ralph Ellison", 1952, "Random House", "9780679732761"),
    ],
    "nonfiction_selfhelp": [
        ("Sapiens: A Brief History of Humankind", "Yuval Noah Harari", 2011, "Harvill Secker", "9780062316097"),
        ("Atomic Habits", "James Clear", 2018, "Avery", "9780735211292"),
        ("Thinking, Fast and Slow", "Daniel Kahneman", 2011, "Farrar, Straus and Giroux", "9780374533557"),
        ("Educated", "Tara Westover", 2018, "Random House", "9780399590504"),
        ("The Power of Habit", "Charles Duhigg", 2012, "Random House", "9780812981605"),
        ("Man's Search for Meaning", "Viktor Frankl", 1946, "Verlag fur Jugend und Volk", "9780807014295"),
        ("Outliers", "Malcolm Gladwell", 2008, "Little, Brown", "9780316017930"),
        ("Quiet: The Power of Introverts", "Susan Cain", 2012, "Crown", "9780307352149"),
        ("Becoming", "Michelle Obama", 2018, "Crown", "9781524763138"),
        ("The Subtle Art of Not Giving a F*ck", "Mark Manson", 2016, "Harper", "9780062457714"),
        ("Never Split the Difference", "Chris Voss", 2016, "Harper Business", "9780062407801"),
        ("A Brief History of Time", "Stephen Hawking", 1988, "Bantam Books", "9780553380163"),
    ],
    "horror_gothic": [
        ("It", "Stephen King", 1986, "Viking Press", "9781501142970"),
        ("Dracula", "Bram Stoker", 1897, "Archibald Constable & Co", "9780486411095"),
        ("Frankenstein", "Mary Shelley", 1818, "Lackington, Hughes", "9780486282114"),
        ("The Shining", "Stephen King", 1977, "Doubleday", "9780307743657"),
        ("The Haunting of Hill House", "Shirley Jackson", 1959, "Viking Press", "9780143039983"),
        ("Pet Sematary", "Stephen King", 1983, "Doubleday", "9781501156751"),
        ("Interview with the Vampire", "Anne Rice", 1976, "Alfred A. Knopf", "9780345337665"),
        ("The Exorcist", "William Peter Blatty", 1971, "Harper & Row", "9780062094354"),
        ("Bird Box", "Josh Malerman", 2014, "Ecco", "9780062259653"),
        ("Something Wicked This Way Comes", "Ray Bradbury", 1962, "Simon & Schuster", "9780380729407"),
        ("The Turn of the Screw", "Henry James", 1898, "Macmillan", "9780486266847"),
        ("Salem's Lot", "Stephen King", 1975, "Doubleday", "9780307743683"),
    ],
    "young_adult": [
        ("The Hunger Games", "Suzanne Collins", 2008, "Scholastic", "9780439023528"),
        ("Divergent", "Veronica Roth", 2011, "Katherine Tegen Books", "9780062024039"),
        ("The Maze Runner", "James Dashner", 2009, "Delacorte Press", "9780385737951"),
        ("Charlie and the Chocolate Factory", "Roald Dahl", 1964, "Alfred A. Knopf", "9780142410318"),
        ("Matilda", "Roald Dahl", 1988, "Jonathan Cape", "9780142410370"),
        ("The Perks of Being a Wallflower", "Stephen Chbosky", 1999, "MTV Books", "9781451696196"),
        ("Wonder", "R.J. Palacio", 2012, "Knopf", "9780375869020"),
        ("The Giver", "Lois Lowry", 1993, "Houghton Mifflin", "9780544336261"),
        ("Holes", "Louis Sachar", 1998, "Farrar, Straus and Giroux", "9780440414803"),
        ("Speak", "Laurie Halse Anderson", 1999, "Farrar, Straus and Giroux", "9780312674397"),
        ("Eleanor & Park", "Rainbow Rowell", 2013, "St. Martin's Griffin", "9781250012579"),
        ("Six of Crows", "Leigh Bardugo", 2015, "Henry Holt", "9781627792127"),
    ],
}

ALL_BOOKS = []
for cluster, books in CLUSTERS.items():
    for title, author, year, publisher, isbn in books:
        ALL_BOOKS.append({"cluster": cluster, "title": title, "author": author,
                           "year": year, "publisher": publisher, "isbn": isbn})

random.shuffle(ALL_BOOKS)

CLUSTER_NAMES = list(CLUSTERS.keys())

LOCATIONS = [
    "new york, ny, usa", "los angeles, ca, usa", "chicago, il, usa",
    "london, england, united kingdom", "toronto, ontario, canada",
    "sydney, nsw, australia", "mumbai, maharashtra, india",
    "berlin, berlin, germany", "paris, ile-de-france, france",
    "seattle, wa, usa", "austin, tx, usa", "dublin, dublin, ireland",
]

N_USERS = 600
N_BOOKS = len(ALL_BOOKS)

# ---------------------------------------------------------------------
# 2. Users: each user has a home cluster (their main taste) and
#    optionally a secondary cluster, mirroring real overlapping taste.
# ---------------------------------------------------------------------
users = []
user_clusters = {}
for uid in range(1, N_USERS + 1):
    primary = random.choice(CLUSTER_NAMES)
    secondary = random.choice([c for c in CLUSTER_NAMES if c != primary]) \
        if random.random() < 0.4 else None
    user_clusters[uid] = (primary, secondary)
    users.append({
        "User-ID": uid,
        "Location": random.choice(LOCATIONS),
        "Age": random.choice([""] * 3 + [str(random.randint(14, 70)) for _ in range(7)]),
    })

# ---------------------------------------------------------------------
# 3. Ratings: users rate books mostly within their taste cluster(s),
#    with some noise from outside, so the pivot/cosine-similarity
#    model in the tutorial has genuine structure to learn from.
# ---------------------------------------------------------------------
ratings = []
seen_pairs = set()

books_by_cluster = {}
for b in ALL_BOOKS:
    books_by_cluster.setdefault(b["cluster"], []).append(b)

for uid in range(1, N_USERS + 1):
    primary, secondary = user_clusters[uid]
    n_ratings = random.randint(15, 60)

    pool = list(books_by_cluster[primary])
    if secondary:
        pool += books_by_cluster[secondary]
    # a little noise from completely random books
    pool += random.sample(ALL_BOOKS, k=min(8, len(ALL_BOOKS)))

    chosen = random.sample(pool, k=min(n_ratings, len(pool)))
    for b in chosen:
        key = (uid, b["isbn"])
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        in_taste = b["cluster"] in (primary, secondary)
        if random.random() < 0.15:
            rating = 0  # implicit / no explicit rating given
        elif in_taste:
            rating = random.choices(range(6, 11), weights=[1, 2, 3, 4, 5])[0]
        else:
            rating = random.choices(range(1, 8), weights=[3, 3, 3, 2, 2, 1, 1])[0]
        ratings.append({"User-ID": uid, "ISBN": b["isbn"], "Book-Rating": rating})

# Make a handful of books very popular (lots of ratings) like real long-tail data
for b in random.sample(ALL_BOOKS, 20):
    extra_users = random.sample(range(1, N_USERS + 1), k=random.randint(60, 150))
    for uid in extra_users:
        key = (uid, b["isbn"])
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        rating = random.choices(range(5, 11), weights=[2, 2, 3, 4, 5, 4])[0]
        ratings.append({"User-ID": uid, "ISBN": b["isbn"], "Book-Rating": rating})

# ---------------------------------------------------------------------
# 4. Write CSVs in the exact Book-Crossing column format
# ---------------------------------------------------------------------
with open("data/Books.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ISBN", "Book-Title", "Book-Author", "Year-Of-Publication", "Publisher",
                "Image-URL-S", "Image-URL-M", "Image-URL-L"])
    for b in ALL_BOOKS:
        # ?default=false makes Open Library return a real 404 (instead of a
        # blank 1x1 placeholder with a 200 status) when it has no cover for
        # this ISBN, so the <img onerror> fallback in the templates actually
        # fires and swaps in the generated cover art.
        s = f"https://covers.openlibrary.org/b/isbn/{b['isbn']}-S.jpg?default=false"
        m = f"https://covers.openlibrary.org/b/isbn/{b['isbn']}-M.jpg?default=false"
        l = f"https://covers.openlibrary.org/b/isbn/{b['isbn']}-L.jpg?default=false"
        w.writerow([b["isbn"], b["title"], b["author"], b["year"], b["publisher"], s, m, l])

with open("data/Users.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["User-ID", "Location", "Age"])
    for u in users:
        w.writerow([u["User-ID"], u["Location"], u["Age"]])

with open("data/Ratings.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["User-ID", "ISBN", "Book-Rating"])
    for r in ratings:
        w.writerow([r["User-ID"], r["ISBN"], r["Book-Rating"]])

print(f"Generated {len(ALL_BOOKS)} books, {len(users)} users, {len(ratings)} ratings")
print("Files written to data/Books.csv, data/Users.csv, data/Ratings.csv")
