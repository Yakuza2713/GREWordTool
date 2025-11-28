import os
import csv
import glob
import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

GRE_DIR = os.path.join(os.getcwd(), "GRE")

# ONE SINGLE RESULTS folder
RESULT_DIR = os.path.join(os.getcwd(), "results")
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

RIGHT_CSV = os.path.join(RESULT_DIR, "right.csv")
WRONG_CSV = os.path.join(RESULT_DIR, "wrong.csv")


def load_words(selection):
    """Load and randomize words from selected files."""
    if selection == "ALL":
        files = glob.glob(os.path.join(GRE_DIR, "*.csv"))
    else:
        files = [os.path.join(GRE_DIR, f) for f in selection]

    words = []
    seen = set()

    for file in files:
        if not os.path.exists(file):
            continue
        with open(file, encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if not row or not row[0].strip():
                    continue

                word = row[0].strip()
                meaning = ", ".join(c.strip() for c in row[1:] if c.strip())

                if word not in seen:
                    words.append({"word": word, "meaning": meaning})
                    seen.add(word)

    random.shuffle(words)
    return words


@app.route("/")
def home():
    files = [os.path.basename(f) for f in glob.glob(os.path.join(GRE_DIR, "*.csv"))]
    files.sort()
    return render_template("index.html", files=files)


@app.post("/start")
def start():
    raw = request.form["files"]

    if raw == "ALL":
        selection = "ALL"
    else:
        selection = [x.strip() for x in raw.split(",") if x.strip()]

    words = load_words(selection)

    # DELETE previous right/wrong CSV to start fresh
    if os.path.exists(RIGHT_CSV):
        os.remove(RIGHT_CSV)
    if os.path.exists(WRONG_CSV):
        os.remove(WRONG_CSV)

    return jsonify({"words": words, "total": len(words)})


@app.post("/save_result")
def save_result():
    word = request.form["word"]
    meaning = request.form["meaning"]
    status = request.form["status"]

    file_path = RIGHT_CSV if status == "right" else WRONG_CSV
    write_header = not os.path.exists(file_path)

    with open(file_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Word", "Meaning"])
        writer.writerow([word, meaning])

    return "OK"


@app.get("/get_results")
def get_results():
    file = request.args.get("file")  # right / wrong
    csv_path = RIGHT_CSV if file == "right" else WRONG_CSV

    if not os.path.exists(csv_path):
        return jsonify([])

    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            rows.append({"word": row[0], "meaning": row[1]})

    return jsonify(rows)


if __name__ == "__main__":
    app.run(debug=True)