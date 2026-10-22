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
    print("--- NEW WEBHOOK RECEIVED ---")
    print("Headers:", dict(request.headers))
    print("Body:", request.json)
    
    data = request.json or {}
    
    gitlab_event = request.headers.get("X-Gitlab-Event", "")
    object_kind = data.get("object_kind", "")
    
    source = "GitLab"
    description = ""
    
    # التحقق الأدق لأحداث الـ Push بغض النظر عن مصدر الهيدر أو الـ object_kind
    if object_kind == "push" or "Push Hook" in gitlab_event:
        user_name = data.get("user_name") or data.get("user_username", "Someone")
        ref = data.get("ref", "refs/heads/main").split("/")[-1]
        commits = data.get("commits", [])
        
        if commits:
            commit_msgs = [c.get("message", "").strip() for c in commits]
            commit_text = " | ".join(commit_msgs)
        else:
            commit_text = "No commit message provided"
            
        description = f"🔨 Push by *{user_name}* to *{ref}*:\n> _{commit_text}_"
        
    elif object_kind == "pipeline" or "Pipeline Hook" in gitlab_event:
        attributes = data.get("object_attributes", {})
        pipeline_id = attributes.get("id", "N/A")
        status = attributes.get("status", "unknown")
        ref = attributes.get("ref", "main")
        description = f"🚀 Pipeline #{pipeline_id} on *{ref}* status: *{status}*"
        
    elif object_kind == "merge_request" or "Merge Request Hook" in gitlab_event:
        mr = data.get("object_attributes", {})
        title = mr.get("title", "No Title")
        state = mr.get("state", "opened")
        description = f"🔀 Merge Request: *{title}* (State: *{state}*)"
        
    elif object_kind == "build" or "Job Hook" in gitlab_event:
        build_name = data.get("build_name", "job")
        build_status = data.get("build_status", "unknown")
        description = f"🛠️ Job *{build_name}* status: *{build_status}*"
    else:
        # التقاط أي حدث آخر بشكل تفصيلي
        event_name = gitlab_event or object_kind or "Generic Event"
        description = f"📦 GitLab Event: {event_name}"

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
@app.route("/api/events/clear", methods=["POST"])
def clear_events():
    global events_database
    events_database.clear()
    return jsonify({"status": "cleared"}), 200
