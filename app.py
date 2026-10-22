from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

events_database = []


@app.route("/health", methods=["GET"])
def health_check():
  return jsonify({"status": "UP", "service": "Webhook Hub"}), 200


@app.route("/webhook", methods=["POST"])
def receive_webhook():
  data = request.json or {}

  # فحص إضافي لقراءة هيدر أو داتا جيت لاب بشكل ذكي
  gitlab_event_header = request.headers.get("X-Gitlab-Event")

  if gitlab_event_header:
    source = "GitLab"
    event_type = gitlab_event_header
  elif "object_kind" in data:
    source = f"GitLab ({data.get('project', {}).get('name', 'Project')})"
    event_type = data.get("object_kind", "Event")
  else:
    source = data.get("source", "Unknown Source")
    event_type = data.get("event_type", "Generic Event")

  event_entry = {
      "source": source,
      "event_type": event_type,
      "payload": data,
      "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
  }

  events_database.insert(0, event_entry)

  if len(events_database) > 20:
    events_database.pop()

  return jsonify({"status": "success", "message": "Event recorded"}), 201


@app.route("/api/events/recent", methods=["GET"])
def get_recent_events():
  return jsonify(events_database), 200


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
