import os
import csv
import glob
import datetime
import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# GRE folder inside project root
GRE_DIR = os.path.join(os.getcwd(), "GRE")

# RESULTS folder in project root
RESULT_DIR = os.path.join(os.getcwd(), "results")
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)


def load_words(selection):
    """
    selection can be:
      - "ALL"
      - list of filenames like ["set10.csv", "set11.csv"]
    """

    # Determine files to load
    if selection == "ALL":
        files = glob.glob(os.path.join(GRE_DIR, "*.csv"))
    else:
        files = [os.path.join(GRE_DIR, f) for f in selection]

    words = []
    seen = set()  # To remove duplicates across files

    for file in files:
        if not os.path.exists(file):
            continue

        with open(file, encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                next(reader)  # Skip header
            except StopIteration:
                continue

            for row in reader:
                if len(row) == 0:
                    continue

                word = row[0].strip()
                if not word:
                    continue

                if word in seen:
                    continue  # Skip duplicate word in this session

                # Combine all other columns as meaning
                meaning = ", ".join([c.strip() for c in row[1:] if c.strip()])

                words.append({"word": word, "meaning": meaning})
                seen.add(word)

    # Shuffle for random order
    random.shuffle(words)
    return words


@app.route("/")
def home():
    # List all CSV files in GRE folder
    files = [os.path.basename(f) for f in glob.glob(os.path.join(GRE_DIR, "*.csv"))]
    files.sort()
    return render_template("index.html", files=files)


@app.post("/start")
def start():
    """
    Receives: files="ALL" or "set10.csv,set12.csv"
    Returns: list of words, total count, session folder name
    """
    raw = request.form["files"]

    if raw == "ALL":
        selection = "ALL"
    else:
        selection = [x.strip() for x in raw.split(",") if x.strip()]

    words = load_words(selection)
    total = len(words)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"session_{timestamp}"
    session_path = os.path.join(RESULT_DIR, session_name)
    os.makedirs(session_path)

    return jsonify({
        "words": words,
        "total": total,
        "session": session_name
    })


@app.post("/save_result")
def save_result():
    """
    Save each word into right.csv or wrong.csv inside session folder
    """
    session = request.form["session"]
    word = request.form["word"]
    meaning = request.form["meaning"]
    status = request.form["status"]  # right / wrong

    session_path = os.path.join(RESULT_DIR, session)
    file_path = os.path.join(session_path, f"{status}.csv")

    # Write header only once
    write_header = not os.path.exists(file_path)

    with open(file_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Word", "Meaning"])
        writer.writerow([word, meaning])

    return "OK"


if __name__ == "__main__":
    app.run(debug=True)