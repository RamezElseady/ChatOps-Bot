from datetime import datetime
from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import requests

app = Flask(__name__)

metrics = PrometheusMetrics(app)

events_database = []

SLACK_WEBHOOK_URL = "YOUR_SLACK_WEBHOOK_URL_HERE"

def send_to_slack(message):
    if "YOUR_SLACK_WEBHOOK_URL" in SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message})
    except Exception as e:
        print(f"Error sending to Slack: {e}")

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "UP", "service": "Webhook Hub"}), 200

@app.route("/webhook", methods=["POST"])
def receive_webhook():
    data = request.json or {}
    
    gitlab_event = request.headers.get("X-Gitlab-Event", "")
    object_kind = data.get("object_kind", "")
    
    source = "GitLab"
    description = f"Event: {gitlab_event or object_kind}"
    
    # تحليل مرن يشمل الهيدر أو الـ object_kind مباشرة
    if "Push" in gitlab_event or object_kind == "push":
        user_name = data.get("user_name") or data.get("user_username", "Someone")
        ref = data.get("ref", "refs/heads/main").split("/")[-1]
        commits = data.get("commits", [])
        commit_msg = commits[0].get("message", "No commit message") if commits else "No commits"
        description = f"🔨 Push by *{user_name}* to *{ref}*:\n> _{commit_msg.strip()}_"
        
    elif "Pipeline" in gitlab_event or object_kind == "pipeline":
        attributes = data.get("object_attributes", {})
        pipeline_id = attributes.get("id", "N/A")
        status = attributes.get("status", "unknown")
        ref = attributes.get("ref", "main")
        description = f"🚀 Pipeline #{pipeline_id} on *{ref}* status: *{status}*"
        
    elif "Merge Request" in gitlab_event or object_kind == "merge_request":
        mr = data.get("object_attributes", {})
        title = mr.get("title", "No Title")
        state = mr.get("state", "opened")
        description = f"🔀 Merge Request: *{title}* (State: *{state}*)"
    else:
        description = f"📦 GitLab Event: {gitlab_event or object_kind or 'Generic'}"

    event_entry = {
        "source": source,
        "event_type": gitlab_event or object_kind or "Unknown",
        "summary": description,
        "payload": data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    events_database.insert(0, event_entry)
    if len(events_database) > 20:
        events_database.pop()

    send_to_slack(f"🔔 *GitLab Webhook Alert*\n{description}")

    return jsonify({"status": "success", "message": "Event processed and recorded"}), 201

@app.route("/api/events/recent", methods=["GET"])
def get_recent_events():
    return jsonify(events_database), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
