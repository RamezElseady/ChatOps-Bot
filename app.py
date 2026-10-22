from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

# قائمة مؤقتة لتخزين الأحداث (في المشروع الحقيقي ممكن نربطها بـ SQLite أو PostgreSQL)
events_database = []


@app.route("/health", methods=["GET"])
def health_check():
  """نقطة فحص صحة التطبيق - البوت بيستخدمها لزرار Hub Health"""
  return jsonify({"status": "UP", "service": "Webhook Hub"}), 200


@app.route("/webhook", methods=["POST"])
def receive_webhook():
  """نقطة استقبال الأحداث من أي خدمة خارجية (GitLab, AWS, GitHub)"""
  data = request.json or {}

  event_entry = {
      "source": data.get("source", "Unknown Source"),
      "event_type": data.get("event_type", "Generic Event"),
      "payload": data,
      "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
  }

  # بنضيف الحدث الجديد في أول القائمة
  events_database.insert(0, event_entry)

  # نحتفظ فقط بأخر 20 حدث عشان الذاكرة
  if len(events_database) > 20:
    events_database.pop()

  return jsonify({"status": "success", "message": "Event recorded"}), 201


@app.route("/api/events/recent", methods=["GET"])
def get_recent_events():
  """نقطة جلب أحدث الأحداث - البوت بيستخدمها لزرار Recent Events"""
  return jsonify(events_database), 200


if __name__ == "__main__":
  # تشغيل السيرفر على البورت 5000
  app.run(host="0.0.0.0", port=5000)
