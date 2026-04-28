"""
webex_bot.py — Flask webhook server for the Webex billing analyst bot.

Incoming flow:
  POST /webhook  ← Webex sends an event when someone messages the bot
    1. Verify HMAC signature
    2. Fetch full message via Webex API
    3. Download any CSV attachment
    4. Call claude_agent.ask()
    5. Reply in the Webex room

Setup:
  1. Create a bot at https://developer.webex.com/my-apps
  2. Copy the bot token → WEBEX_BOT_TOKEN in .env
  3. Expose this server (ngrok, etc.) and register a webhook:
       python bot/register_webhook.py --url https://<your-host>/webhook
"""

import hashlib
import hmac
import os
import uuid

import requests
from flask import Flask, abort, jsonify, request

from . import claude_agent
from .tools import register_uploaded_file

app = Flask(__name__)

WEBEX_API = "https://webexapis.com/v1"

# Bot's own person ID — fetched once at startup to avoid echoing ourselves
_BOT_PERSON_ID: str | None = None


# ── Webex helpers ─────────────────────────────────────────────────────────────

def _bot_token() -> str:
    token = os.environ.get("WEBEX_BOT_TOKEN", "")
    if not token:
        raise EnvironmentError("WEBEX_BOT_TOKEN environment variable not set.")
    return token


def _headers() -> dict:
    return {"Authorization": f"Bearer {_bot_token()}"}


def get_bot_person_id() -> str:
    global _BOT_PERSON_ID
    if _BOT_PERSON_ID is None:
        r = requests.get(f"{WEBEX_API}/people/me", headers=_headers(), timeout=10)
        r.raise_for_status()
        _BOT_PERSON_ID = r.json()["id"]
    return _BOT_PERSON_ID


def get_message(message_id: str) -> dict:
    r = requests.get(
        f"{WEBEX_API}/messages/{message_id}", headers=_headers(), timeout=10
    )
    r.raise_for_status()
    return r.json()


def send_message(room_id: str, text: str, markdown: str | None = None) -> None:
    payload: dict = {"roomId": room_id}
    if markdown:
        payload["markdown"] = markdown
    else:
        payload["text"] = text
    requests.post(
        f"{WEBEX_API}/messages", headers=_headers(), json=payload, timeout=15
    )


def download_file(file_url: str) -> bytes:
    """Download a Webex message attachment (requires bot auth)."""
    r = requests.get(file_url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.content


# ── Signature verification ────────────────────────────────────────────────────

def _verify_signature(raw_body: bytes) -> bool:
    secret = os.environ.get("WEBEX_WEBHOOK_SECRET", "")
    if not secret:
        # No secret configured — skip verification (dev only)
        return True
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha1
    ).hexdigest()
    received = request.headers.get("X-Spark-Signature", "")
    return hmac.compare_digest(expected, received)


# ── Webhook endpoint ──────────────────────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    raw_body = request.get_data()

    if not _verify_signature(raw_body):
        abort(403, "Invalid signature")

    event = request.get_json(force=True)

    # Only handle 'messages' resource with 'created' event
    if event.get("resource") != "messages" or event.get("event") != "created":
        return jsonify({"status": "ignored"}), 200

    message_id = event.get("data", {}).get("id")
    if not message_id:
        return jsonify({"status": "no message id"}), 200

    # Fetch full message
    try:
        msg = get_message(message_id)
    except Exception as e:
        print(f"[webex] Failed to fetch message {message_id}: {e}")
        return jsonify({"status": "error fetching message"}), 200

    # Ignore messages sent by the bot itself
    if msg.get("personId") == get_bot_person_id():
        return jsonify({"status": "self-message ignored"}), 200

    room_id = msg["roomId"]
    raw_text = (msg.get("text") or "").strip()

    # Strip the bot's display name if mentioned (direct/group space)
    bot_mention_prefix = msg.get("mentionedPeople", [])
    # Remove leading "@BotName" if present
    if raw_text.lower().startswith("@"):
        raw_text = raw_text.split(" ", 1)[-1].strip()

    # Handle /reset command
    if raw_text.lower() in ("/reset", "reset"):
        claude_agent.clear_history(room_id)
        send_message(room_id, "Conversation history cleared. Ready for a new session.")
        return jsonify({"status": "reset"}), 200

    # ── Handle file attachments ───────────────────────────────────────────────
    file_context = ""
    file_urls = msg.get("files", [])
    for file_url in file_urls:
        try:
            file_bytes = download_file(file_url)
            # Generate a stable file ID for this attachment
            file_id = str(uuid.uuid4())
            csv_text = file_bytes.decode("utf-8", errors="replace")
            register_uploaded_file(file_id, csv_text)
            file_context += (
                f"\n\n[A CSV file has been uploaded. file_id={file_id}. "
                f"Use the read_csv tool with file_id='{file_id}' to analyse it.]"
            )
        except Exception as e:
            file_context += f"\n\n[File download failed: {e}]"

    # Build the full user message
    user_message = (raw_text + file_context).strip()
    if not user_message:
        user_message = "(the user sent an empty message)"

    # ── Ask Claude ────────────────────────────────────────────────────────────
    try:
        reply = claude_agent.ask(room_id=room_id, user_message=user_message)
    except Exception as e:
        reply = f"Sorry, I hit an error: {e}"
        print(f"[claude] Error for room {room_id}: {e}")

    # ── Reply in Webex ────────────────────────────────────────────────────────
    # Send as markdown so headers, bold text, and code blocks render
    send_message(room_id, text=reply, markdown=reply)

    return jsonify({"status": "ok"}), 200


# ── Health check ──────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "bot": "webex-billing-analyst"}), 200
