from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import mysql.connector
import os
import whisper
from transformers import pipeline
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "mysecretkey"



UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"mp3", "wav"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
model = whisper.load_model("base")


# summarizer = pipeline(
#     "text2text-generation",
#     model="google/flan-t5-small"
# )
summarizer = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-12-6"
)


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="flask_basic"
)
cursor = db.cursor(buffered=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already exists!")
            return render_template("register.html")

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        db.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session["user_id"] = user[0]
            session["email"] = user[2]
            return redirect(url_for("upload_audio"))
        else:
            flash("Invalid email or password")

    return render_template("login.html")

@app.route("/upload-audio", methods=["GET", "POST"])
def upload_audio():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("audio_file")

        if not file or file.filename == "":
            flash("No file selected")
            return redirect(request.url)

        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)

            # Transcribe
            result = model.transcribe(path)
            transcription = result["text"]

            # Summarize
            summary_result = summarizer(
              transcription[:1000],   # limit input size
              max_length=150,
              min_length=30,
              do_sample=False
        )
            summary = summary_result[0]["summary_text"]
            print("🧠 Summary:", summary_result[0]['summary_text'])

            # Save transcription
            txt_filename = f"{filename}.txt"
            txt_path = os.path.join(app.config["UPLOAD_FOLDER"], txt_filename)

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(transcription)
                
                # Save summary
            summary_filename = f"{filename}_summary.txt"
            summary_path = os.path.join(app.config["UPLOAD_FOLDER"], summary_filename)

            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
                
                # Create combined TXT file
            combined_filename = f"{filename}_full_result.txt"
            combined_path = os.path.join(app.config["UPLOAD_FOLDER"], combined_filename)

            with open(combined_path, "w", encoding="utf-8") as f:
              f.write("===== TRANSCRIPTION =====\n\n")
              f.write(transcription)
              f.write("\n\n\n===== SUMMARY =====\n\n")
              f.write(summary)
                
            import json

            json_filename = f"{filename}_result.json"
            json_path = os.path.join(app.config["UPLOAD_FOLDER"], json_filename)

            data = {
                "transcript": transcription,
                "summary": summary
            }

            with open(json_path, "w", encoding="utf-8") as f:
               json.dump(data, f, indent=4)

            return render_template(
                "index.html",
                transcription=transcription,
                summary=summary,
                download_combined=combined_filename,
                download_json=json_filename
            )

        else:
            flash("Only MP3 or WAV files allowed")
            return redirect(request.url)

    return render_template("index.html")
    
@app.route("/download/<filename>")
def download_file(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    return send_file(path, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)