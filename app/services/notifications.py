import json
import smtplib
import logging
import threading
from email.message import EmailMessage
from typing import Optional

import requests

logger = logging.getLogger(__name__)


# ── WebSocket Connection Manager ──────────────────────────────────────

class ConnectionManager:
    """Gère les connexions WebSocket pour le broadcast temps réel."""

    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)


manager = ConnectionManager()


# ── Payload builder ──────────────────────────────────────────────────

def build_analysis_payload(analysis) -> dict:
    """Construit un payload standardisé à partir d'une analyse."""
    result = json.loads(analysis.result_json) if analysis.result_json else {}
    return {
        "event": "analysis.completed",
        "analysis_id": analysis.id,
        "candidate": result.get("candidate_name", analysis.cv_filename),
        "job_title": analysis.job_title or "",
        "score": analysis.score,
        "status": analysis.status,
        "feedback": result.get("feedback", ""),
        "skills_found": result.get("skills_found", []),
        "skills_missing": result.get("skills_missing", []),
    }


# ── Webhook (Slack / Discord) ───────────────────────────────────────

def send_webhook(webhook_url: str, payload: dict) -> bool:
    """Envoie une notification vers un webhook Slack/Discord."""
    try:
        slack_payload = {
            "text": (
                f"✅ *Analyse terminée*\n"
                f"• Candidat : {payload['candidate']}\n"
                f"• Poste : {payload['job_title']}\n"
                f"• Score : *{payload['score']}%*\n"
                f"• Statut : {payload['status']}"
            )
        }
        resp = requests.post(webhook_url, json=slack_payload, timeout=10)
        resp.raise_for_status()
        logger.info(f"Webhook envoyé → {webhook_url}")
        return True
    except Exception as e:
        logger.error(f"Webhook échoué : {e}")
        return False


# ── Email ────────────────────────────────────────────────────────────

def send_email(smtp_config: dict, to: str, subject: str, body: str) -> bool:
    """Envoie un email via SMTP."""
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = smtp_config["from"]
        msg["To"] = to

        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            if smtp_config.get("use_tls"):
                server.starttls()
            if smtp_config.get("username"):
                server.login(smtp_config["username"], smtp_config["password"])
            server.send_message(msg)

        logger.info(f"Email envoyé à {to}")
        return True
    except Exception as e:
        logger.error(f"Email échoué : {e}")
        return False


# ── Orchestrateur ────────────────────────────────────────────────────

def notify_all_sync(
    analysis,
    webhook_url: Optional[str] = None,
    smtp_config: Optional[dict] = None,
    email_to: Optional[str] = None,
):
    """Version synchrone — appelée depuis l'endpoint (fire & forget)."""
    payload = build_analysis_payload(analysis)

    # 1. Webhook
    if webhook_url:
        send_webhook(webhook_url, payload)

    # 2. Email
    if smtp_config and email_to:
        subject = f"✅ Analyse terminée : {payload['candidate']} — {payload['score']}%"
        body = (
            f"Candidat : {payload['candidate']}\n"
            f"Poste : {payload['job_title']}\n"
            f"Score : {payload['score']}%\n"
            f"Statut : {payload['status']}\n\n"
            f"Compétences trouvées : {', '.join(payload['skills_found'])}\n"
            f"Compétences manquantes : {', '.join(payload['skills_missing'])}\n\n"
            f"Feedback : {payload['feedback']}"
        )
        send_email(smtp_config, email_to, subject, body)


def notify_async(analysis, **kwargs):
    """Lance les notifications dans un thread séparé (fire & forget)."""
    thread = threading.Thread(target=notify_all_sync, args=(analysis,), kwargs=kwargs, daemon=True)
    thread.start()
