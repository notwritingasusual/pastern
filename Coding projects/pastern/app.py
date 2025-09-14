from flask import Flask, render_template, request, redirect 
import sqlite3, datetime, re

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS clipboard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        keywords TEXT,
        created_at TIMESTAMP
    )""")
    conn.commit()
    conn.close()

# Extract simple keywords
def extract_keywords(text):
    words = re.findall(r"\b\w+\b", text.lower())
    common = {"the","and","a","to","of","in","it","is","that","for"}  # stop words
    keywords = [w for w in words if w not in common]
    return ",".join(set(keywords))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        content = request.form["content"]
        keywords = extract_keywords(content)
        conn = sqlite3.connect("data.db")
        c = conn.cursor()
        c.execute("INSERT INTO clipboard (content, keywords, created_at) VALUES (?, ?, ?)",
                  (content, keywords, datetime.datetime.now()))
        conn.commit()
        conn.close()
        return redirect("/")
    
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM clipboard ORDER BY created_at DESC")
    entries = c.fetchall()
    conn.close()
    return render_template("index.html", entries=entries)

@app.route("/search")
def search():
    q = request.args.get("q", "")
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM clipboard WHERE keywords LIKE ?", ('%'+q+'%',))
    results = c.fetchall()
    conn.close()
    return render_template("index.html", entries=results, search=q)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
