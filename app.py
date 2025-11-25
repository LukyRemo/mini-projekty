from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
tasks = []
task_id = 1

def load_tasks():
    global tasks, task_id
    if os.path.exists("tasks.json"):
        with open("tasks.json", "r", encoding="utf-8") as f:
            tasks_data = json.load(f)
            tasks = tasks_data
            if tasks:
                task_id = max(task["id"] for task in tasks) +1
load_tasks()

def save_tasks():
    with open("tasks.json", "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d.%m.%Y %H:%M")
    except ValueError:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M")

def sort_key(task):  
    due = parse_date(task["due_date"])
    priority_order = {"high": 1, "medium": 2, "low": 3}
    return (due, priority_order.get(task["priority"], 4))

@app.route("/")
def home():
    filter_option = request.args.get("filter", "all")
    sort_option = request.args.get("sort", "auto")
    filtered_tasks = tasks.copy()

    if sort_option=="auto":
        filtered_tasks.sort(key=sort_key)

    now = datetime.now()
    for task in tasks:
        due = parse_date(task["due_date"])
        time_diff = (due - now). total_seconds()
        task["is_urgent"] = 0 < time_diff <= 86400

    if filter_option == "done":
        filtered_tasks = [task for task in tasks if task["done"]]
    elif filter_option == "not_done":
        filtered_tasks = [task for task in tasks if not task["done"]]
    elif filter_option in ["high", "medium", "low"]:
        filtered_tasks = [task for task in tasks if task["priority"] == filter_option]

    today = now.date()
    tomorrow = today + timedelta(days=1)

    tasks_today = []
    tasks_tomorrow = []
    tasks_later = []
    tasks_overdue = []

    for task in filtered_tasks:
        due_date_obj = parse_date(task["due_date"])
        due_date = due_date_obj.date()
        task["due_date_formatted"] = due_date_obj.strftime("%d. %m. %Y o %H:%M")

        if due_date < today and not task["done"]:
            tasks_overdue.append(task)
        elif due_date == today:
            tasks_today.append(task)
        elif due_date == tomorrow:
            tasks_tomorrow.append(task)
        else:
            tasks_later.append(task)

    return render_template(
        "index.html",
        tasks_today=tasks_today,
        tasks_tomorrow=tasks_tomorrow,
        tasks_later=tasks_later,
        tasks_overdue=tasks_overdue,
        filter=filter_option,
        sort=sort_option
    )

@app.route('/add', methods=['POST'])
def add_task():
    global task_id
    task_text = request.form.get("task")
    due_date = request.form.get("due_date")
    priority = request.form.get("priority")
    if task_text and due_date:
        tasks.append({
            "id": task_id,
            "text": task_text,
            "done": False,
            "due_date": due_date,
            "priority": priority,
            "order": len(tasks)
        })
        task_id += 1
        save_tasks()
    return redirect(url_for("home"))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_task(id): 
    global tasks
    tasks = [task for task in tasks if task['id'] != id]
    save_tasks()
    return redirect(url_for("home"))

@app.route('/toggle/<int:id>', methods=['POST'])
def toggle_task(id):
    for task in tasks:
        if task['id'] ==id:
            task['done'] = not task['done']
            break
    save_tasks()
    return redirect(url_for("home"))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    for task in tasks:
        if task['id'] == id:
            if request.method == 'POST':
                task['text'] = request.form.get("task")
                task['due_date'] = request.form.get("due_date")
                save_tasks()
                return redirect(url_for("home"))
            else:
                return render_template("edit.html", task=task)
    return redirect(url_for("home"))

from flask import send_from_directory
import os

@app.route('/service-worker.js')
def service_worker():
    return app.send_static_file('service-worker.js')
           
if __name__ == "__main__":
    app.run(debug=True)
