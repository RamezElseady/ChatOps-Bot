# ⚡ Slack-based DevOps Operations Center

A modern, **event-driven Operations Center & Automation Platform** built to streamline DevOps workflows through a conversational Slack interface.

---

## 🏗️ Architecture Overview

The system architecture follows a reactive event-driven model. Interactivity is handled via Slack's Block Kit UI, orchestrated by AWS Lambda, and backed by a Python Flask Webhook Hub running on EC2.

```
                        HTTP Payload
┌─────────────────┐                    ┌──────────────────────┐
│    Slack UI      │ ─────────────────► │    AWS Lambda        │
│ (Interactive Hub)│                   │   (Orchestrator)     │
└─────────────────┘                    └──────────────────────┘
                                              │         │
                              ┌───────────────┘         └───────────────┐
                    [Trigger/Manage API]              [Direct API Queries]
                              │                                │
                   ┌──────────▼──────────┐       ┌────────────▼────────────┐
                   │    GitLab CI/CD     │       │    AWS Cloud APIs        │
                   │  (Pipelines & Jobs) │       │ (Cost Explorer & EC2)   │
                   └─────────────────────┘       └─────────────────────────┘
                              │
                   ┌──────────▼──────────┐
                   │ Real-time Webhook   │
                   │       Event        │
                   └─────────────────────┘
```

---

## 🔄 End-to-End Data Flow

1. **Slack UI Interactivity:** User clicks an action button (e.g., `Run Build`, `Check Costs`, `Prom Alerts`) inside a custom Slack Block Kit interface.

2. **Event Orchestration (AWS Lambda):** AWS Lambda receives the interactive payload, decodes the user intent, and acts as the central router.

3. **Pipeline Control (GitLab API):** Lambda triggers, retries, or cancels GitLab CI/CD pipelines through GitLab REST APIs.

4. **Webhook Ingestion (Flask Hub on EC2):** GitLab pushes real-time pipeline and job state notifications via Webhooks to a Python Flask Webhook Hub running inside Docker on AWS EC2.

5. **Cloud Infrastructure & Metrics Query:**
   - Lambda directly queries AWS Cost Explorer API for current month-to-date spending.
   - Lambda queries AWS EC2 API for real-time server statuses (Running/Stopped).
   - Lambda queries Prometheus AlertManager (port 9090) via the Webhook Hub to fetch active monitoring alerts.

6. **Dynamic In-Place Response:** Lambda updates the existing Slack message (`replace_original: True`), avoiding channel spam and keeping a clean operational dashboard.

---

## ✨ Key Features

- 🎛️ **Interactive Slack Kit Dashboard:** Manage complex DevOps tasks via intuitive buttons without leaving Slack.
- ⚡ **Event-Driven Pipeline Triggering:** Start and manage GitLab CI/CD builds instantly.
- 📦 **Centralized Webhook Hub:** Ingests and stores real-time events in-memory inside Docker.
- 💰 **Real-Time AWS Cost Tracking:** On-demand cloud cost inspection via AWS Cost Explorer.
- 🖥️ **Infrastructure State Inspection:** Instantly view AWS EC2 instance health and running statuses.
- 🔥 **Live Prometheus Alerting:** Pull active alerts directly from Prometheus metrics without opening extra tabs.
- 🧹 **Clean Chat Lifecycle:** Uses in-place message updates (`replace_original`) to maintain a single, dynamic state view.

---

## 🛠️ Tech Stack & Prerequisites

| Layer | Tool / Service | Purpose |
|---|---|---|
| User Interface | Slack API | Block Kit UI, Interactive Components, Slash Commands |
| Serverless Compute | AWS Lambda | Event orchestration, payload processing (`boto3`, `urllib3`) |
| CI/CD Platform | GitLab Cloud API | Pipeline automation and webhook event delivery |
| Backend & Runtime | Python Flask / Docker | Webhook listener hosted inside Docker on AWS EC2 |
| Cloud Provider | AWS (EC2 & Cost Explorer) | Infrastructure control and financial metrics API |
| Observability | Prometheus | Local metrics scraping and alert state management (Port 9090) |


---

## 🚀 Deployment & Setup Guide

### 1. Clone the Repository

```bash
git clone https://gitlab.com/your-username/slack-devops-ops-center.git
cd slack-devops-ops-center
```

### 2. Deploy the Flask Webhook Hub (AWS EC2 / Docker)

Navigate to the `webhook_hub` folder and start the containerized service:

```bash
cd webhook_hub
docker compose up -d --build
```

Ensure port `5000` (Flask) and port `9090` (Prometheus) are reachable within your AWS Security Group rules.

### 3. Configure GitLab Webhooks

- Go to your GitLab Repository → **Settings** → **Webhooks**.
- Set URL to: `http://<EC2_PUBLIC_IP>:5000/webhook`
- Select trigger events: **Push events**, **Pipeline events**, **Job events**.

### 4. Configure AWS Lambda & Environment Variables

Deploy the Python script inside `lambda/lambda_function.py` to AWS Lambda and set up the following environment variables:

| Variable | Description |
|---|---|
| `SLACK_BOT_TOKEN` | OAuth Bot Token from Slack API configuration |
| `GITLAB_PERSONAL_TOKEN` | Access Token with `api` permissions |
| `GITLAB_PROJECT_ID` | Project ID found in your GitLab repository header |
| `WEBHOOK_HUB_URL` | Public endpoint of your EC2 Flask Hub (e.g., `http://<EC2_IP>:5000`) |

---

## 💡 Sample Interactivity Logic (Code Snippets)

### In-Place Message Update Pattern (Slack API)

```python
import json
import urllib3

http = urllib3.PoolManager()

def update_slack_message(response_url, payload):
    """Updates the existing Slack message block."""
    payload["replace_original"] = True
    response = http.request(
        "POST",
        response_url,
        body=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )
    return response.status
```

---

## 🤝 Contributing & Feedback

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

Made with ❤️ by a DevOps Engineer who loves automation.
