import json
import os
import datetime
import urllib3
import boto3
from urllib.parse import parse_qs, unquote

http = urllib3.PoolManager()
ec2_client = boto3.client('ec2', region_name='us-east-1')
ce_client = boto3.client('ce', region_name='us-east-1')

def get_dashboard_blocks(result_text=None):
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "⚡ DevOps Operations Center", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "Unified dashboard to manage Pipelines, Infrastructure, and Event Hub:"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*⚙️ GitLab CI/CD Pipeline Controls:*"}},
        {
            "type": "actions",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "🚀 Run Build", "emoji": True}, "style": "primary", "action_id": "trigger_build_btn"},
                {"type": "button", "text": {"type": "plain_text", "text": "🔄 Retry", "emoji": True}, "action_id": "retry_build_btn"},
                {"type": "button", "text": {"type": "plain_text", "text": "🛑 Cancel", "emoji": True}, "style": "danger", "action_id": "cancel_build_btn"},
                {"type": "button", "text": {"type": "plain_text", "text": "📊 Status", "emoji": True}, "action_id": "check_status_btn"}
            ]
        },
        {
            "type": "actions",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "📜 Last 5 Pipelines", "emoji": True}, "action_id": "last_5_pipelines_btn"}
            ]
        },
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*📡 Webhook Hub, Monitoring & Infrastructure:*"}},
        {
            "type": "actions",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "🩺 Hub Health", "emoji": True}, "action_id": "check_hub_btn"},
                {"type": "button", "text": {"type": "plain_text", "text": "📥 Recent Events", "emoji": True}, "action_id": "get_events_btn"},
                {"type": "button", "text": {"type": "plain_text", "text": "🧹 Clear Events", "emoji": True}, "action_id": "clear_events_btn"},
                {"type": "button", "text": {"type": "plain_text", "text": "💰 AWS Cost", "emoji": True}, "action_id": "aws_cost_btn"}
            ]
        },
        {
            "type": "actions",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "🔥 Prom Alerts", "emoji": True}, "style": "danger", "action_id": "prom_alerts_btn"},
                {"type": "button", "text": {"type": "plain_text", "text": "🖥️ EC2 Status", "emoji": True}, "action_id": "check_ec2_btn"}
            ]
        }
    ]
    
    # Show result only if present and not empty
    if result_text:
        blocks.append({"type": "divider"})
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*📌 Current Result:*\n{result_text}"}})
        
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": "💡 Event-Driven Architecture | AWS Lambda, Cost Explorer & Slack Integration."}]})
    return blocks

def lambda_handler(event, context):
    GITLAB_TOKEN = os.environ.get('GITLAB_TOKEN', '')
    PROJECT_ID = os.environ.get('PROJECT_ID', '')
    WEBHOOK_HUB_URL = os.environ.get('WEBHOOK_HUB_URL', 'http://localhost:5000')
    
    body_val = event.get('body')
    body_str = "" if body_val is None else str(body_val)
        
    if event.get('isBase64Encoded', False):
        import base64
        try:
            body_str = base64.b64decode(body_str).decode('utf-8')
        except Exception:
            pass

    command_text = ""
    is_interactive = False
    action_id = ""
    response_url = ""

    decoded_body = unquote(body_str) if body_str else ""

    if "payload=" in decoded_body:
        is_interactive = True
        try:
            parts = decoded_body.split("payload=", 1)
            if len(parts) > 1:
                payload_json = json.loads(parts[1])
                actions = payload_json.get('actions', [])
                response_url = payload_json.get('response_url', '')
                if actions:
                    action_id = actions[0].get('action_id', '')
        except Exception as e:
            print("Error parsing payload JSON:", str(e))
            
    elif "command=" in decoded_body:
        parsed_body = parse_qs(decoded_body)
        text_list = parsed_body.get('text', [])
        response_url_list = parsed_body.get('response_url', [])
        if response_url_list:
            response_url = response_url_list[0]
        if text_list:
            full_text = text_list[0].strip().lower()
            command_text = full_text.split()[0] if full_text else ""

    # --- GitLab CI/CD Functions ---
    def get_pipeline_status():
        url = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/pipelines?per_page=1"
        headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
        try:
            res = http.request("GET", url, headers=headers, timeout=5.0)
            data = json.loads(res.data.decode('utf-8'))
            if res.status == 200 and isinstance(data, list) and len(data) > 0:
                latest = data[0]
                return f"📊 *Latest Pipeline Status*\n*ID:* `{latest.get('id')}`\n*Status:* `{latest.get('status')}`\n*Branch:* `{latest.get('ref')}`"
            return "⚠️ Could not fetch pipelines status."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def get_last_5_pipelines():
        url = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/pipelines?per_page=5"
        headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
        try:
            res = http.request("GET", url, headers=headers, timeout=5.0)
            data = json.loads(res.data.decode('utf-8'))
            if res.status == 200 and isinstance(data, list) and len(data) > 0:
                msg = "📊 *Last 5 Pipelines:*\n"
                for p in data:
                    emoji = "🟢" if p.get('status') == 'success' else ("🔴" if p.get('status') == 'failed' else "🟡")
                    msg += f"• {emoji} ID: `{p.get('id')}` | Status: *{p.get('status')}* | Ref: `{p.get('ref')}`\n"
                return msg
            return "⚠️ No pipelines found."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def trigger_pipeline():
        branch = "main"
        url = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/pipeline?ref={branch}"
        headers = {"PRIVATE-TOKEN": GITLAB_TOKEN, "Content-Type": "application/json"}
        try:
            res = http.request("POST", url, headers=headers, timeout=5.0)
            data = json.loads(res.data.decode('utf-8'))
            if res.status == 201:
                return f"🚀 *Pipeline Triggered Successfully!*\n*ID:* `{data.get('id')}`\n*Status:* `{data.get('status')}`"
            return f"⚠️ Failed to trigger: {data.get('message', 'Unknown error')}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def retry_latest_pipeline():
        list_url = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/pipelines?per_page=1"
        headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
        try:
            res = http.request("GET", list_url, headers=headers, timeout=5.0)
            data = json.loads(res.data.decode('utf-8'))
            if res.status == 200 and isinstance(data, list) and len(data) > 0:
                pipeline_id = data[0].get('id')
                retry_url = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/pipelines/{pipeline_id}/retry"
                retry_res = http.request("POST", retry_url, headers=headers, timeout=5.0)
                retry_data = json.loads(retry_res.data.decode('utf-8'))
                if retry_res.status in [200, 201]:
                    return f"🔄 *Pipeline #{pipeline_id} Retried Successfully!*\n*Status:* `{retry_data.get('status')}`"
                return f"⚠️ Could not retry pipeline: {retry_data.get('message', 'Unknown')}"
            return "⚠️ No pipelines found to retry."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def cancel_latest_pipeline():
        list_url = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/pipelines?per_page=1"
        headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
        try:
            res = http.request("GET", list_url, headers=headers, timeout=5.0)
            data = json.loads(res.data.decode('utf-8'))
            if res.status == 200 and isinstance(data, list) and len(data) > 0:
                pipeline_id = data[0].get('id')
                cancel_url = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/pipelines/{pipeline_id}/cancel"
                cancel_res = http.request("POST", cancel_url, headers=headers, timeout=5.0)
                if cancel_res.status == 200:
                    return f"🛑 *Pipeline #{pipeline_id} Cancelled Successfully!*"
                return f"⚠️ Could not cancel pipeline."
            return "⚠️ No active pipelines found."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    # --- AWS, Cost Explorer & Webhook Hub Functions ---
    def check_ec2_status():
        try:
            response = ec2_client.describe_instances()
            instances_info = "☁️ *AWS EC2 Instances Status:*\n"
            found = False
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    found = True
                    instance_id = instance.get('InstanceId')
                    state = instance.get('State', {}).get('name', 'unknown')
                    instance_type = instance.get('InstanceType')
                    name = "Unnamed"
                    for tag in instance.get('Tags', []):
                        if tag.get('Key') == 'Name':
                            name = tag.get('Value')
                    emoji = "🟢" if state == "running" else "🔴"
                    instances_info += f"• {emoji} *{name}* (`{instance_id}`) | `{instance_type}` | *{state}*\n"
            return instances_info if found else "☁️ No EC2 instances found."
        except Exception as e:
            return f"❌ Error fetching EC2: {str(e)}"

    def get_aws_estimated_cost():
        try:
            today = datetime.date.today()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            
            response = ce_client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            amount = "0.00"
            unit = "USD"
            results = response.get('ResultsByTime', [])
            if results:
                total = results[0].get('Total', {})
                unblended_cost = total.get('UnblendedCost', {})
                amount = round(float(unblended_cost.get('Amount', '0')), 2)
                unit = unblended_cost.get('Unit', 'USD')
                
            return f"💰 *Estimated AWS Cost (This Month):* `${amount} {unit}`"
        except Exception as e:
            return f"❌ Error fetching AWS Cost: {str(e)}"

    def check_hub_health():
        health_url = f"{WEBHOOK_HUB_URL.rstrip('/')}/health"
        try:
            res = http.request("GET", health_url, timeout=4.0)
            if res.status == 200:
                return f"🟢 *Webhook Hub Health:* UP (`HTTP 200 OK`)\n*URL:* `{health_url}`"
            else:
                return f"🟡 *Webhook Hub Health:* Warning (`HTTP {res.status}`)"
        except Exception as e:
            return f"🔴 *Webhook Hub Health:* DOWN or Unreachable!\n*Error:* {str(e)}"

    def get_recent_events():
        events_url = f"{WEBHOOK_HUB_URL.rstrip('/')}/api/events/recent"
        try:
            res = http.request("GET", events_url, timeout=4.0)
            if res.status == 200:
                events = json.loads(res.data.decode('utf-8'))
                if not events:
                    return "ℹ️ No events recorded yet in Webhook Hub."
                
                msg = "📥 *Recent Webhook Events:*\n"
                for ev in events[:3]:
                    timestamp = ev.get('timestamp', '')
                    summary = ev.get('summary', 'No details')
                    source = ev.get('source', 'GitLab')
                    msg += f"• *{source}* | `{timestamp}`\n  ↳ {summary}\n"
                return msg
            return f"⚠️ Could not fetch events (`HTTP {res.status}`)."
        except Exception as e:
            return f"❌ Error fetching events: {str(e)}"

    def clear_events_db():
        clear_url = f"{WEBHOOK_HUB_URL.rstrip('/')}/api/events/clear"
        try:
            # استخدام GET بدلاً من POST لتجنب أي مشاكل في توافق مسارات الـ Flask
            http.request("GET", clear_url, timeout=4.0)
            return None  # ينظف الشاشة تماماً
        except Exception as e:
            return f"❌ Failed to clear events: {str(e)}"

    def get_prometheus_alerts():
        alerts_url = f"{WEBHOOK_HUB_URL.rstrip('/')}/api/prometheus/alerts"
        try:
            res = http.request("GET", alerts_url, timeout=4.0)
            if res.status == 200:
                data = json.loads(res.data.decode('utf-8'))
                alerts = data.get('data', {}).get('alerts', [])
                active_alerts = [a for a in alerts if a.get('state') == 'firing']
                
                if not active_alerts:
                    return "🟢 *Prometheus Alerts:* No active firing alerts! All systems nominal."
                
                msg = "🔥 *Active Prometheus Alerts:*\n"
                for alert in active_alerts:
                    labels = alert.get('labels', {})
                    alertname = labels.get('alertname', 'Unknown')
                    severity = labels.get('severity', 'warning')
                    msg += f"• 🚨 *{alertname}* (Severity: `{severity}`)\n"
                return msg
            return "⚠️ Could not fetch Prometheus alerts from Webhook Hub."
        except Exception as e:
            return f"❌ Error fetching alerts: {str(e)}"

    # 1. Initial Dashboard Block UI
    if not is_interactive and command_text != "status":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "response_type": "in_channel",
                "blocks": get_dashboard_blocks(None)
            })
        }

    # 2. Handle Actions
    result_text = None
    if is_interactive:
        if action_id == "trigger_build_btn":
            result_text = trigger_pipeline()
        elif action_id == "retry_build_btn":
            result_text = retry_latest_pipeline()
        elif action_id == "cancel_build_btn":
            result_text = cancel_latest_pipeline()
        elif action_id == "check_status_btn":
            result_text = get_pipeline_status()
        elif action_id == "last_5_pipelines_btn":
            result_text = get_last_5_pipelines()
        elif action_id == "check_ec2_btn":
            result_text = check_ec2_status()
        elif action_id == "aws_cost_btn":
            result_text = get_aws_estimated_cost()
        elif action_id == "check_hub_btn":
            result_text = check_hub_health()
        elif action_id == "get_events_btn":
            result_text = get_recent_events()
        elif action_id == "clear_events_btn":
            result_text = clear_events_db()
        elif action_id == "prom_alerts_btn":
            result_text = get_prometheus_alerts()
        else:
            result_text = "❓ Unknown action received."
    elif command_text == "status":
        result_text = get_pipeline_status()

    # Update dashboard and clear or show results underneath buttons
    if response_url:
        try:
            encoded_data = json.dumps({
                "replace_original": True,
                "response_type": "in_channel",
                "blocks": get_dashboard_blocks(result_text)
            }).encode('utf-8')
            
            http.request(
                'POST',
                response_url,
                body=encoded_data,
                headers={'Content-Type': 'application/json'}
            )
        except Exception as e:
            print("Error sending to response_url:", str(e))

    return {
        "statusCode": 200,
        "body": ""
    }
