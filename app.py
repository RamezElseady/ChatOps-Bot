from datetime import datetime
from flask import Flask, jsonify, request
import requests  # مهم لو هتبعت إشعارات مباشرة لـ Slack من الكود

app = Flask(__name__)

from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)

events_database = []

# ضع هنا رابط الـ Slack Webhook الخاص بك لو حابب السيرفر يبعت له مباشرة
SLACK_WEBHOOK_URL = "YOUR_SLACK_WEBHOOK_URL_HERE"

def send_to_slack(message):
    if "YOUR_SLACK_WEBHOOK_URL" in SLACK_WEBHOOK_URL:
        return # تخطي لو لم يتم ضبط الرابط بعد
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
    
    # فحص نوع الحدث القادم من جيت لاب بدقة
    gitlab_event = request.headers.get("X-Gitlab-Event", "Unknown Event")
    
    source = "GitLab"
    description = "General Event"
    
    # تحليل الأحداث المختلفة وإبراز تفاصيلها
    if "Push Hook" in gitlab_event or "object_kind" in data and data.get("object_kind") == "push":
        user_name = data.get("user_name", "Someone")
        ref = data.get("ref", "refs/heads/main").split("/")[-1]
        commits = data.get("commits", [])
        commit_msg = commits[0].get("message", "No commit message") if commits else "No commits"
        
        description = f"🔨 Push by *{user_name}* to *{ref}*:\n> _{commit_msg.strip()}_"
        
    elif "Pipeline Hook" in gitlab_event or "object_kind" in data and data.get("object_kind") == "pipeline":
        attributes = data.get("object_attributes", {})
        pipeline_id = attributes.get("id", "N/A")
        status = attributes.get("status", "unknown")
        ref = attributes.get("ref", "main")
        
        description = f"🚀 Pipeline #{pipeline_id} on *{ref}* status: *{status}*"
        
    elif "Merge Request Hook" in gitlab_event:
        mr = data.get("object_attributes", {})
        title = mr.get("title", "No Title")
        state = mr.get("state", "opened")
        description = f"🔀 Merge Request: *{title}* (State: *{state}*)"
    else:
        description = f"📦 Event received: {gitlab_event}"

    event_entry = {
        "source": source,
        "event_type": gitlab_event,
        "summary": description,
        "payload": data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    events_database.insert(0, event_entry)
    if len(events_database) > 20:
        events_database.pop()

    # إرسال ملخص احترافي للسلاك
    send_to_slack(f"🔔 *GitLab Webhook Alert*\n{description}")

    return jsonify({"status": "success", "message": "Event processed and recorded"}), 201

@app.route("/api/events/recent", methods=["GET"])
def get_recent_events():
    return jsonify(events_database), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
