from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import os
from datetime import datetime
from ai_module import ask_gemini
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from db import tasks_collection, users_collection, flashcards_collection
from bson import ObjectId
import json
from flashcard_module import generate_flashcards_ai

app = Flask(__name__, static_folder="static")
app.secret_key = "super_secret_key_change_this"  # Required for sessions


# --- LOGIN SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

USERS_FILE = "users.txt"


# User Class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


# --- AUTH ROUTES ---


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user_data = users_collection.find_one({"username": username})
        if user_data:
            if check_password_hash(user_data["password"], password):
                login_user(User(username))
                return redirect(url_for("index"))
            else:
                flash("Incorrect password. Please try again.")
                return redirect(url_for("login"))

        flash("User not found. Please sign up.")
    return render_template("login.html")


@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username")
    password = request.form.get("password")

    # Check if user exists
    if users_collection.find_one({"username": username}):
        flash("Username already exists!")
        return redirect(url_for("login"))

    # Create new user
    hashed_pw = generate_password_hash(password, method="scrypt")
    new_user = {
        "username": username,
        "password": hashed_pw,
        "created_at": datetime.now(),
    }

    users_collection.insert_one(new_user)
    login_user(User(username))
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# --- APP ROUTES (Now Protected) ---


def get_all_tasks():
    tasks = list(tasks_collection.find({"user_id": current_user.id}))
    for t in tasks:
        t["_id"] = str(t["_id"])
    return tasks


@app.route("/")
@login_required
def index():
    tasks = get_all_tasks()
    today = datetime.now().date()

    completed = [t for t in tasks if t["status"] == "Completed"]
    overdue = [
        t
        for t in tasks
        if t["status"] != "Completed"
        and datetime.strptime(t["due_date"], "%Y-%m-%d").date() < today
    ]

    return render_template(
        "index.html",
        tasks=tasks,
        total=len(tasks),
        completed=len(completed),
        pending=len(tasks) - len(completed),
        overdue_count=len(overdue),
        overdue_list=overdue,
        username=current_user.id,
    )


@app.route("/calendar")
@login_required
def calendar():
    tasks = get_all_tasks()
    today = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        "calendar.html",
        tasks=tasks,
        today=today,
        username=current_user.id,
    )


@app.route("/add", methods=["POST"])
@login_required
def add_task_route():
    task = {
        "user_id": current_user.id,
        "subject": request.form.get("subject"),
        "description": request.form.get("task"),
        "due_date": request.form.get("due_date"),
        "priority": request.form.get("priority", "Medium"),
        "status": "Pending",
    }

    tasks_collection.insert_one(task)
    return redirect(url_for("index"))


@app.route("/complete/<task_id>")
@login_required
def complete_task(task_id):
    tasks_collection.update_one(
        {"_id": ObjectId(task_id), "user_id": current_user.id},
        {"$set": {"status": "Completed"}},
    )
    return redirect(url_for("index"))


@app.route("/delete/<task_id>")
@login_required
def delete_task(task_id):
    tasks_collection.delete_one({"_id": ObjectId(task_id), "user_id": current_user.id})
    return redirect(url_for("index"))


@app.route("/ask_ai", methods=["POST"])
@login_required
def ask_ai():
    prompt = request.form.get("prompt", "")
    if prompt:
        tasks = get_all_tasks()

        # --- TOKEN REDUCTION: Pruning context ---
        # Only take the 10 most recent/relevant tasks and only essential fields
        short_tasks = tasks[:10]
        if short_tasks:
            tasks_context = "Current Tasks:\n"
            for t in short_tasks:
                # Removed 'description' and 'priority' to save tokens unless strictly needed
                tasks_context += (
                    f"- {t['subject']} (Due: {t['due_date']}, Status: {t['status']})\n"
                )
        else:
            tasks_context = "No tasks found."

        # --- TOKEN REDUCTION: Concise System Instruction ---
        full_prompt = f"""
        System: You are a concise study assistant. Answer in under 150 words.
        User Question: {prompt}
        """

        response = ask_gemini(full_prompt)
        return jsonify({"response": response})

    return jsonify({"response": "No prompt provided."})


@app.route("/edit/<task_id>", methods=["POST"])
@login_required
def edit_task(task_id):
    tasks_collection.update_one(
        {"_id": ObjectId(task_id), "user_id": current_user.id},
        {
            "$set": {
                "subject": request.form.get("subject"),
                "description": request.form.get("task"),
                "due_date": request.form.get("due_date"),
                "priority": request.form.get("priority"),
            }
        },
    )
    return redirect(url_for("index"))


# --- FLASHCARD ROUTES ---


@app.route("/flashcards")
@login_required
def flashcards():
    saved_cards = list(flashcards_collection.find({"user_id": current_user.id}))
    return render_template(
        "flashcards.html", username=current_user.id, saved_cards=saved_cards
    )


@app.route("/generate_flashcards", methods=["POST"])
@login_required
def generate_flashcards():
    data = request.json
    subject = data.get("subject")
    topic = data.get("topic")

    # --- TOKEN REDUCTION: Explicitly limit output size in the prompt ---
    prompt = f"""
    Generate 5 short flashcards for {subject}: {topic}.
    Keep 'front' and 'back' text under 20 words each.
    Return ONLY a JSON array. 
    Format: [{{"front": "Q", "back": "A"}}]
    """
    try:
        # This function now returns a list directly, not a string!
        cards = generate_flashcards_ai(prompt)

        # Check if it returned an empty list (all keys failed)
        if not cards:
            return jsonify({"error": "All AI keys failed,Please try again later"}), 500

        # No need to use .replace() or json.loads() here anymore
        return jsonify({"cards": cards})

    except Exception as e:
        print(f"Error in app.py flashcard route: {e}")
        return jsonify({"error": "Failed to generate cards"}), 500


@app.route("/save_flashcard", methods=["POST"])
@login_required
def save_flashcard():
    data = request.json
    flashcards_collection.insert_one(
        {
            "user_id": current_user.id,
            "topic": data.get("topic"),
            "front": data.get("front"),
            "back": data.get("back"),
        }
    )
    return jsonify({"status": "success"})


@app.route("/my-library")
@login_required
def my_library():
    # Get all cards for this user
    user_cards = list(flashcards_collection.find({"user_id": current_user.id}))
    return render_template("library.html", cards=user_cards, username=current_user.id)


@app.route("/delete_card/<card_id>")
@login_required
def delete_card(card_id):
    flashcards_collection.delete_one(
        {"_id": ObjectId(card_id), "user_id": current_user.id}
    )
    return redirect(url_for("library"))


@app.route("/library")
@login_required
def library():
    # Fetch all cards for the logged-in user
    all_cards = list(flashcards_collection.find({"user_id": current_user.id}))

    # Group cards by their topic/title for better organization
    grouped_cards = {}
    for card in all_cards:
        topic = card.get("topic", "General")
        if topic not in grouped_cards:
            grouped_cards[topic] = []
        grouped_cards[topic].append(card)

    return render_template(
        "library.html", grouped_cards=grouped_cards, username=current_user.id
    )


@app.route("/toggle_task/<task_id>", methods=["POST"])
@login_required
def toggle_task(task_id):
    task = tasks_collection.find_one(
        {"_id": ObjectId(task_id), "user_id": current_user.id}
    )

    if not task:
        return jsonify({"error": "Task not found"}), 404

    new_status = "Completed" if task["status"] != "Completed" else "Pending"

    tasks_collection.update_one(
        {"_id": ObjectId(task_id)}, {"$set": {"status": new_status}}
    )

    return jsonify({"status": new_status})


@app.route("/timer")
@login_required
def timer():
    # Reuse your helper to get tasks for the current user
    tasks = get_all_tasks()
    # Optional: Filter for only 'Pending' tasks to show what needs doing
    pending_tasks = [t for t in tasks if t["status"] == "Pending"]
    return render_template("timer.html", username=current_user.id, tasks=pending_tasks)


@app.route("/subscribe")
@login_required
def subscribe():
    return render_template("subscribe.html", username=current_user.id)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")

        # --- Handle Username Change ---
        if action == "update_username":
            new_username = request.form.get("username")
            old_username = current_user.id

            if users_collection.find_one({"username": new_username}):
                flash("Username already taken.")
            else:
                users_collection.update_one(
                    {"username": old_username}, {"$set": {"username": new_username}}
                )
                tasks_collection.update_many(
                    {"user_id": old_username}, {"$set": {"user_id": new_username}}
                )
                new_user_obj = User(new_username)
                login_user(new_user_obj)
                flash("Username updated successfully!")

        # --- Handle Password Change ---
        elif action == "update_password":
            current_pw = request.form.get("current_password")
            new_pw = request.form.get("new_password")
            # Make sure this matches the 'id' in your confirm password input if you check it here

            user_data = users_collection.find_one({"username": current_user.id})

            if user_data and check_password_hash(user_data["password"], current_pw):
                hashed_pw = generate_password_hash(new_pw, method="scrypt")
                users_collection.update_one(
                    {"username": current_user.id}, {"$set": {"password": hashed_pw}}
                )
                flash("Password updated successfully!")
            else:
                flash("Current password incorrect.")
        return redirect(url_for("profile"))

    return render_template("profile.html", username=current_user.id)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
